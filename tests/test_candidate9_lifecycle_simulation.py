import sqlite3
import tempfile
import unittest
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path

from paper_trading.candidate9_lifecycle_simulation import (
    SimulatedPosition, SimulatedSnapshot, begin, create, finish, finish_from_broker, restart,
    state, submission_result, supervise,
)
from paper_trading.candidate9_reconciliation import Deal
from paper_trading.candidate9_risk import BrokerConstraints
from paper_trading.candidate9_safeguard_model import SafeguardError
from scripts.backtest import Bar
from tests.test_candidate9_mt5_history import HistoryBroker


class LifecycleSimulationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "simulation.sqlite"
        self.kill = Path(self.tmp.name) / "kill"
        self.now = datetime(2026, 11, 22, 22, 5, tzinfo=timezone.utc)
        create(self.path, self.now - timedelta(days=1), self.now + timedelta(days=30))
        self.snapshot = SimulatedSnapshot(True, True, True, 0, 0, D("2"), D("0"))
        friday = datetime(2026, 11, 20, 21, 55, tzinfo=timezone.utc)
        self.friday = Bar(friday, 1.1, 1.1001, 1.0999, 1.1)
        self.reopening = Bar(self.now - timedelta(minutes=5), 1.099, 1.0991, 1.0989, 1.099)
        self.constraints = BrokerConstraints(D("0.00001"), D("0.0002"), D("0.01"),
                                             D("10"), D("0.01"), D("100"))
        self.position = SimulatedPosition(20, 30, "long", D("0.01"), D("1.09920"), D("1.10220"))

    def begin(self, snapshot=None, now=None):
        return begin(self.path, now or self.now, self.kill, snapshot or self.snapshot,
                     self.friday, self.reopening, bid=D("1.10000"), ask=D("1.10020"),
                     volume=D("0.01"), risk_budget=D("2"), costs_per_lot=D("0"),
                     constraints=self.constraints, magic=30)

    def accept(self):
        self.assertEqual(self.begin(), "ORDER_PENDING")
        self.assertEqual(submission_result(self.path, self.now, "accepted", order_ticket=10, position_id=20),
                         "POSITION_OPEN")

    def open_snapshot(self):
        return replace(self.snapshot, positions=1)

    def test_complete_reconciliation_and_latch(self):
        self.accept()
        self.assertEqual(supervise(self.path, self.now, self.kill, self.open_snapshot(), self.position),
                         "POSITION_SUPERVISION")
        self.assertEqual(supervise(self.path, self.now, self.kill, self.snapshot, None), "POSITION_CLOSED")
        entry = Deal(1, 10, 20, 30, "EURUSD", "buy", "entry", self.now,
                     D("0.01"), D("1.10020"), D("0"), D("0"), D("0"), D("0"), "client")
        exit = Deal(2, 11, 20, 30, "EURUSD", "sell", "exit", self.now + timedelta(minutes=5),
                    D("0.01"), D("1.10220"), D("2"), D("0"), D("0"), D("0"), "take_profit")
        self.assertEqual(finish(self.path, self.now + timedelta(minutes=5), [entry, exit], 10), "SHUTDOWN")
        self.assertEqual(state(self.path), ("SHUTDOWN", "ONE_TRADE_COMPLETED"))
        self.assertEqual(restart(self.path, self.now), "SHUTDOWN")
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM trade_log").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT completed FROM study").fetchone()[0], 1)
            transitions = [r[0] for r in db.execute("SELECT new_state FROM events ORDER BY id")]
        self.assertEqual(transitions, ["PRECHECK", "SIGNAL_DETECTED", "ORDER_PENDING", "POSITION_OPEN",
                                       "POSITION_SUPERVISION", "POSITION_CLOSED", "RECONCILED", "SHUTDOWN"])
        with self.assertRaises(SafeguardError):
            self.begin()

    def test_rejection_unknown_and_timeout_never_retry(self):
        for result, expected in (("rejected", "SHUTDOWN"), ("unknown", "MANUAL_REVIEW_REQUIRED"),
                                 ("timeout", "MANUAL_REVIEW_REQUIRED")):
            with self.subTest(result=result):
                path = Path(self.tmp.name) / (result + ".sqlite")
                create(path, self.now - timedelta(days=1), self.now + timedelta(days=1))
                original, self.path = self.path, path
                self.assertEqual(self.begin(), "ORDER_PENDING")
                self.assertEqual(submission_result(path, self.now, result), expected)
                with self.assertRaises(SafeguardError):
                    submission_result(path, self.now, "accepted", order_ticket=10, position_id=20)
                self.path = original

    def test_restart_pending_open_and_closed(self):
        self.assertEqual(self.begin(), "ORDER_PENDING")
        self.assertEqual(restart(self.path, self.now), "MANUAL_REVIEW_REQUIRED")
        with self.assertRaises(SafeguardError):
            submission_result(self.path, self.now, "accepted", order_ticket=10, position_id=20)
        for stage in ("open", "closed"):
            path = Path(self.tmp.name) / (stage + ".sqlite")
            create(path, self.now - timedelta(days=1), self.now + timedelta(days=1))
            original, self.path = self.path, path
            self.accept()
            if stage == "closed":
                self.assertEqual(supervise(path, self.now, self.kill, self.snapshot, None), "POSITION_CLOSED")
            self.assertEqual(restart(path, self.now), "MANUAL_REVIEW_REQUIRED")
            self.path = original

    def test_missing_protection_and_kill(self):
        for variant in ("stop", "target", "kill", "spread"):
            path = Path(self.tmp.name) / (variant + ".sqlite")
            create(path, self.now - timedelta(days=1), self.now + timedelta(days=1))
            original, self.path = self.path, path
            self.accept()
            position, snapshot = self.position, self.open_snapshot()
            if variant == "stop":
                position = replace(position, stop=D("0"))
            elif variant == "target":
                position = replace(position, target=D("0"))
            elif variant == "kill":
                self.kill.write_text("stop", encoding="utf-8")
            else:
                snapshot = replace(snapshot, spread_pips=D("3.01"))
            result = supervise(path, self.now, self.kill, snapshot, position)
            self.assertIn(result, ("POSITION_OR_PROTECTION_MISMATCH", "KILL_SWITCH_TRIGGERED",
                                   "HIGH_SPREAD_DURING_POSITION"))
            self.assertEqual(state(path)[0], "MANUAL_REVIEW_REQUIRED")
            if self.kill.exists():
                self.kill.unlink()
            self.path = original

    def test_reconciliation_failure_latches(self):
        self.accept()
        supervise(self.path, self.now, self.kill, self.snapshot, None)
        self.assertEqual(finish(self.path, self.now, [], 10), "RECONCILIATION_FAILURE")
        self.assertEqual(state(self.path)[0], "MANUAL_REVIEW_REQUIRED")

    def test_broker_history_path_records_and_latches_on_failure(self):
        self.accept()
        supervise(self.path, self.now, self.kill, self.snapshot, None)
        broker = HistoryBroker(self.now)
        for deal in broker.deals:
            deal.time_msc = int(self.now.timestamp() * 1000)
        result = finish_from_broker(self.path, self.now, broker, expected_login=123,
                                    epoch_is_verified_utc=True, internal_order_ticket=10)
        self.assertEqual(result, "SHUTDOWN")
        self.assertEqual(state(self.path), ("SHUTDOWN", "ONE_TRADE_COMPLETED"))
        self.assertEqual(broker.history_queries, [{"position": 20}])
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM trade_log").fetchone()[0], 1)

        path = Path(self.tmp.name) / "history_failure.sqlite"
        create(path, self.now - timedelta(days=1), self.now + timedelta(days=1))
        self.path = path
        self.accept()
        supervise(path, self.now, self.kill, self.snapshot, None)
        broker.deals = None
        self.assertEqual(finish_from_broker(path, self.now, broker, expected_login=123,
                                            epoch_is_verified_utc=True, internal_order_ticket=10),
                         "RECONCILIATION_FAILURE")
        self.assertEqual(state(path), ("MANUAL_REVIEW_REQUIRED", "RECONCILIATION_FAILURE"))
        with closing(sqlite3.connect(path)) as db:
            reason = db.execute("SELECT reason FROM events ORDER BY id DESC LIMIT 1").fetchone()[0]
            self.assertIn("history unavailable", reason)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM trade_log").fetchone()[0], 0)
        self.assertEqual(restart(path, self.now), "MANUAL_REVIEW_REQUIRED")

    def test_expiry_ten_count_positions_and_filters(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("UPDATE study SET completed=10")
        self.assertEqual(self.begin(), "VALIDATION_TRADE_LIMIT")
        for name, snapshot, expected in (
            ("position", replace(self.snapshot, positions=1), "UNEXPECTED_OPEN_POSITION"),
            ("order", replace(self.snapshot, pending_orders=1), "UNEXPECTED_PENDING_ORDER"),
            ("spread", replace(self.snapshot, spread_pips=D("3.1")), "SIGNAL_SKIPPED_HIGH_SPREAD"),
            ("loss", replace(self.snapshot, daily_net_pnl_r=D("-1")), "SHUTDOWN_DAILY_LOSS"),
        ):
            path = Path(self.tmp.name) / (name + ".sqlite")
            create(path, self.now - timedelta(days=1), self.now + timedelta(days=1))
            original, self.path = self.path, path
            self.assertEqual(self.begin(snapshot), expected)
            self.path = original
        path = Path(self.tmp.name) / "expired.sqlite"
        create(path, self.now - timedelta(days=1), self.now)
        original, self.path = self.path, path
        self.assertEqual(self.begin(), "VALIDATION_EXPIRED")
        self.path = original

    def test_concurrent_intents_allow_only_one(self):
        def attempt():
            try:
                return self.begin()
            except SafeguardError:
                return "REFUSED"
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: attempt(), range(2)))
        self.assertCountEqual(results, ["ORDER_PENDING", "REFUSED"])
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute(
                "SELECT COUNT(*) FROM events WHERE new_state='ORDER_PENDING'"
            ).fetchone()[0], 1)

    def test_invalid_transitions_and_three_failure_limit(self):
        with self.assertRaises(SafeguardError):
            finish(self.path, self.now, [], 10)
        with self.assertRaises(SafeguardError):
            supervise(self.path, self.now, self.kill, self.snapshot, None)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("UPDATE study SET failures=3")
        self.assertEqual(self.begin(), "SHUTDOWN_FAILURE_LIMIT")


if __name__ == "__main__":
    unittest.main()
