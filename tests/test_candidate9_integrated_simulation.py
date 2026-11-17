import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path
from unittest.mock import patch

from paper_trading.candidate9_integrated_simulation import (
    SimulatedBroker, SimulatedOrderResult, SupervisionSample, close, recover,
    run_supervision, start, watch,
)
from paper_trading.candidate9_lifecycle_simulation import (
    SimulatedPosition, SimulatedSnapshot, begin, create, state,
)
from paper_trading.candidate9_reconciliation import Deal
from paper_trading.candidate9_risk import BrokerConstraints
from paper_trading.candidate9_safeguard_model import SafeguardError
from scripts.backtest import Bar


class IntegratedSimulationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "study.sqlite"
        self.kill = Path(self.tmp.name) / "kill"
        self.now = datetime(2026, 11, 22, 22, 5, tzinfo=timezone.utc)
        create(self.path, self.now - timedelta(days=1), self.now + timedelta(days=1))
        self.snapshot = SimulatedSnapshot(True, True, True, 0, 0, D("2"), D("0"))
        self.position = SimulatedPosition(20, 30, "long", D("0.01"),
                                          D("1.09920"), D("1.10220"))
        self.friday = Bar(datetime(2026, 11, 20, 21, 55, tzinfo=timezone.utc),
                          1.1, 1.1001, 1.0999, 1.1)
        self.reopening = Bar(self.now - timedelta(minutes=5), 1.099, 1.0991, 1.0989, 1.099)
        self.constraints = BrokerConstraints(D("0.00001"), D("0.0002"), D("0.01"),
                                             D("10"), D("0.01"), D("100"))
        self.deals = [
            Deal(1, 10, 20, 30, "EURUSD", "buy", "entry", self.now,
                 D("0.01"), D("1.1002"), D("0"), D("0"), D("0"), D("0"), "client"),
            Deal(2, 11, 20, 30, "EURUSD", "sell", "exit", self.now + timedelta(minutes=1),
                 D("0.01"), D("1.1022"), D("2"), D("0"), D("0"), D("0"), "take_profit"),
        ]
        self.broker = self.broker_with("accepted")

    def broker_with(self, outcome, snapshot=None):
        return SimulatedBroker(self.snapshot, snapshot or self.snapshot,
                               SimulatedOrderResult(outcome, 10, 20), self.deals)

    def start(self, broker=None, now=None):
        return start(self.path, now or self.now, self.kill, broker or self.broker,
                     self.friday, self.reopening, bid=D("1.10000"), ask=D("1.10020"),
                     volume=D("0.01"), risk_budget=D("2"), costs_per_lot=D("0"),
                     constraints=self.constraints, magic=30)

    def open(self):
        self.assertEqual(self.start(), "POSITION_OPEN")
        self.assertEqual(watch(self.path, self.now, self.kill,
                               replace(self.snapshot, positions=1), self.position),
                         "POSITION_SUPERVISION")

    def test_happy_path_and_independent_records(self):
        self.open()
        self.assertEqual(watch(self.path, self.now, self.kill, self.snapshot, None), "POSITION_CLOSED")
        self.assertEqual(close(self.path, self.now + timedelta(minutes=1), self.broker), "SHUTDOWN")
        self.assertEqual(state(self.path), ("SHUTDOWN", "ONE_TRADE_COMPLETED"))
        self.assertEqual(self.broker.submit_calls, 1)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT order_ticket,position_id FROM execution_log").fetchone(), (10, 20))
            self.assertTrue(db.execute("SELECT result FROM validation_log").fetchone()[0])
            self.assertEqual(db.execute("SELECT COUNT(*) FROM trade_log").fetchone()[0], 1)
        self.assertEqual(recover(self.path, self.now), "SHUTDOWN")
        with self.assertRaises(SafeguardError):
            self.start()

    def test_rejected_unknown_timeout_and_exception_do_not_retry(self):
        for outcome in ("rejected", "unknown", "timeout", "exception"):
            with self.subTest(outcome=outcome):
                path = Path(self.tmp.name) / (outcome + ".sqlite")
                create(path, self.now - timedelta(days=1), self.now + timedelta(days=1))
                self.path = path
                broker = self.broker_with(outcome)
                expected = "SHUTDOWN" if outcome == "rejected" else "MANUAL_REVIEW_REQUIRED"
                self.assertEqual(self.start(broker), expected)
                self.assertEqual(broker.submit_calls, 1)
                self.assertEqual(recover(path, self.now), expected)
                with self.assertRaises(SafeguardError):
                    self.start(broker)
                self.assertEqual(broker.submit_calls, 1)

    def test_changed_precheck_refuses_without_submission(self):
        for name, snapshot in (
            ("position", replace(self.snapshot, positions=1)),
            ("order", replace(self.snapshot, pending_orders=1)),
            ("connection", replace(self.snapshot, healthy=False)),
            ("spread", replace(self.snapshot, spread_pips=D("3.1"))),
            ("daily_loss", replace(self.snapshot, daily_net_pnl_r=D("-1"))),
            ("changed_quote", replace(self.snapshot, spread_pips=D("2.1"))),
        ):
            with self.subTest(name=name):
                path = Path(self.tmp.name) / (name + ".sqlite")
                create(path, self.now - timedelta(days=1), self.now + timedelta(days=1))
                self.path = path
                broker = self.broker_with("accepted", snapshot)
                self.assertEqual(self.start(broker), "MANUAL_REVIEW_REQUIRED")
                self.assertEqual(broker.submit_calls, 0)

    def test_protection_kill_expiry_and_restart(self):
        for name in ("stop", "target", "kill", "expiry", "restart"):
            with self.subTest(name=name):
                path = Path(self.tmp.name) / (name + ".sqlite")
                create(path, self.now - timedelta(days=1), self.now + timedelta(days=1))
                self.path = path
                self.broker = self.broker_with("accepted")
                self.assertEqual(self.start(), "POSITION_OPEN")
                if name == "restart":
                    result = recover(path, self.now)
                else:
                    position = self.position
                    now = self.now
                    if name == "stop":
                        position = replace(position, stop=D("0"))
                    if name == "target":
                        position = replace(position, target=D("0"))
                    if name == "kill":
                        self.kill.touch()
                    if name == "expiry":
                        now += timedelta(days=1)
                    watch(path, now, self.kill, replace(self.snapshot, positions=1), position)
                    result = state(path)[0]
                self.assertEqual(result, "MANUAL_REVIEW_REQUIRED")
                if name == "kill":
                    self.kill.unlink()
                self.assertEqual(self.broker.submit_calls, 1)

    def test_corrupt_log_or_history_requires_review(self):
        for kind in ("log", "journal", "history"):
            with self.subTest(kind=kind):
                path = Path(self.tmp.name) / (kind + ".sqlite")
                create(path, self.now - timedelta(days=1), self.now + timedelta(days=1))
                self.path = path
                self.broker = self.broker_with("accepted")
                self.open()
                self.assertEqual(watch(path, self.now, self.kill, self.snapshot, None), "POSITION_CLOSED")
                if kind == "history":
                    self.broker.deals = []
                else:
                    with closing(sqlite3.connect(path)) as db, db:
                        if kind == "log":
                            db.execute("UPDATE execution_log SET order_ticket=999")
                        else:
                            db.execute("UPDATE validation_log SET intent='{}'")
                self.assertEqual(close(path, self.now, self.broker), "MANUAL_REVIEW_REQUIRED")
                self.assertEqual(state(path)[1], "RECONCILIATION_FAILURE")
                with closing(sqlite3.connect(path)) as db:
                    self.assertEqual(db.execute("SELECT COUNT(*) FROM trade_log").fetchone()[0], 0)

    def test_expiry_limit_kill_and_non_simulated_broker_refused(self):
        with self.assertRaises(SafeguardError):
            self.start(object())
        self.kill.touch()
        self.assertEqual(self.start(), "KILL_SWITCH_TRIGGERED")
        self.assertEqual(self.broker.submit_calls, 0)
        self.kill.unlink()
        for name in ("expiry", "limit"):
            path = Path(self.tmp.name) / (name + ".sqlite")
            create(path, self.now - timedelta(days=1), self.now + timedelta(days=1))
            self.path = path
            if name == "limit":
                with closing(sqlite3.connect(path)) as db, db:
                    db.execute("UPDATE study SET completed=10")
                self.assertEqual(self.start(), "VALIDATION_TRADE_LIMIT")
            else:
                self.assertEqual(self.start(now=self.now + timedelta(days=1)), "VALIDATION_EXPIRED")
            self.assertEqual(self.broker.submit_calls, 0)

    def test_competing_attempts_submit_at_most_once(self):
        def attempt():
            try:
                return self.start()
            except SafeguardError:
                return "REFUSED"
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: attempt(), range(2)))
        self.assertCountEqual(results, ["POSITION_OPEN", "REFUSED"])
        self.assertEqual(self.broker.submit_calls, 1)

    def test_scripted_supervision_loop_and_exhaustion(self):
        self.assertEqual(self.start(), "POSITION_OPEN")
        samples = [
            SupervisionSample(self.now, replace(self.snapshot, positions=1), self.position),
            SupervisionSample(self.now + timedelta(minutes=1), self.snapshot, None),
        ]
        self.assertEqual(run_supervision(self.path, self.now, self.kill, self.broker, samples),
                         "SHUTDOWN")
        self.assertEqual(state(self.path), ("SHUTDOWN", "ONE_TRADE_COMPLETED"))
        path = Path(self.tmp.name) / "exhaustion.sqlite"
        create(path, self.now - timedelta(days=1), self.now + timedelta(days=1))
        self.path = path
        self.assertEqual(self.start(), "POSITION_OPEN")
        self.assertEqual(run_supervision(path, self.now, self.kill, self.broker, samples[:1]),
                         "MANUAL_REVIEW_REQUIRED")
        self.assertEqual(state(path)[1], "SUPERVISION_ENDED")

    def test_closure_before_verified_position_requires_review(self):
        self.assertEqual(self.start(), "POSITION_OPEN")
        self.assertEqual(watch(self.path, self.now, self.kill, self.snapshot, None),
                         "POSITION_NEVER_OBSERVED")
        self.assertEqual(state(self.path)[0], "MANUAL_REVIEW_REQUIRED")

    def test_history_time_outside_window_is_rejected(self):
        self.open()
        watch(self.path, self.now, self.kill, self.snapshot, None)
        self.assertEqual(close(self.path, self.now, self.broker), "MANUAL_REVIEW_REQUIRED")
        self.assertEqual(state(self.path)[1], "RECONCILIATION_FAILURE")

    def test_restart_after_committed_pending_intent_never_submits(self):
        self.assertEqual(begin(self.path, self.now, self.kill, self.snapshot,
                               self.friday, self.reopening, bid=D("1.10000"),
                               ask=D("1.10020"), volume=D("0.01"),
                               risk_budget=D("2"), costs_per_lot=D("0"),
                               constraints=self.constraints, magic=30), "ORDER_PENDING")
        self.assertEqual(recover(self.path, self.now), "MANUAL_REVIEW_REQUIRED")
        with self.assertRaises(SafeguardError):
            self.start()
        self.assertEqual(self.broker.submit_calls, 0)

    def test_kill_or_file_error_between_precheck_and_submission_latches(self):
        for variant in ("kill", "error"):
            path = Path(self.tmp.name) / (variant + "_race.sqlite")
            create(path, self.now - timedelta(days=1), self.now + timedelta(days=1))
            self.path = path
            effect = True if variant == "kill" else OSError("kill path unavailable")
            with patch("paper_trading.candidate9_integrated_simulation._kill_exists",
                       side_effect=effect if isinstance(effect, OSError) else None,
                       return_value=effect if isinstance(effect, bool) else False):
                self.assertEqual(self.start(), "MANUAL_REVIEW_REQUIRED")
            self.assertEqual(self.broker.submit_calls, 0)
            self.assertEqual(state(path)[1], "KILL_SWITCH_TRIGGERED" if variant == "kill"
                             else "BROKER_HEALTH_FAILURE")


if __name__ == "__main__":
    unittest.main()
