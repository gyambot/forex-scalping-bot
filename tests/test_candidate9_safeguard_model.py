import sqlite3
import tempfile
import unittest
from contextlib import closing
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from paper_trading.candidate9_safeguard_model import (
    SafeguardError, Snapshot, check_model, initialize_model, record_outcome,
)


class Candidate9ModelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "state.sqlite"
        self.kill = Path(self.tmp.name) / "kill.txt"
        self.now = datetime(2026, 11, 16, tzinfo=timezone.utc)
        self.snapshot = Snapshot(True, True, True, True, True, True, 0, 0, 0, 3, 5)
        initialize_model(self.path, self.now)

    def check(self, snapshot=None, now=None):
        return check_model(self.path, self.kill, now or self.now, snapshot or self.snapshot)

    def test_persistent_one_trade_latch_and_rejection_or_reconciliation(self):
        for outcome, expected in (("completed", "ONE_TRADE_COMPLETED"),
                                  ("rejected", "ORDER_REJECTED"),
                                  ("reconciliation_failure", "RECONCILIATION_FAILURE")):
            path = Path(self.tmp.name) / (outcome + ".sqlite")
            initialize_model(path, self.now)
            self.assertEqual(record_outcome(path, self.now, outcome), expected)
            self.assertEqual(check_model(path, self.kill, self.now, self.snapshot), expected)
            with self.assertRaises(SafeguardError):
                record_outcome(path, self.now, "completed")
            with self.assertRaises(FileExistsError):
                initialize_model(path, self.now)

    def test_kill_is_persisted_after_file_removal(self):
        self.kill.write_text("stop", encoding="utf-8")
        self.assertEqual(self.check(), "KILL_SWITCH_TRIGGERED")
        self.kill.unlink()
        self.assertEqual(self.check(), "KILL_SWITCH_TRIGGERED")
        with closing(sqlite3.connect(self.path)) as db, db:
            self.assertEqual(db.execute("SELECT event FROM events").fetchone()[0], "KILL_SWITCH_TRIGGERED")

    def test_spread_gap_limits_and_boundary(self):
        self.assertEqual(self.check(), "MODEL_CHECKS_PASSED_NO_EXECUTION")
        self.assertEqual(self.check(replace(self.snapshot, spread_pips=3.001)), "SIGNAL_SKIPPED_HIGH_SPREAD")
        self.assertEqual(self.check(replace(self.snapshot, gap_pips=-20.001)), "SIGNAL_SKIPPED_EXTREME_GAP")
        self.assertEqual(self.check(replace(self.snapshot, gap_pips=-20)), "MODEL_CHECKS_PASSED_NO_EXECUTION")

    def test_startup_positions_orders_health_and_daily_loss(self):
        cases = [
            (replace(self.snapshot, open_positions=1), "UNEXPECTED_OPEN_POSITION"),
            (replace(self.snapshot, pending_orders=1), "UNEXPECTED_PENDING_ORDER"),
            (replace(self.snapshot, connected=False), "BROKER_HEALTH_FAILURE"),
            (replace(self.snapshot, quote_fresh=False), "BROKER_HEALTH_FAILURE"),
            (replace(self.snapshot, demo_account_verified=False), "BROKER_HEALTH_FAILURE"),
            (replace(self.snapshot, trade_permissions=False), "BROKER_HEALTH_FAILURE"),
            (replace(self.snapshot, daily_net_pnl_r=-1), "SHUTDOWN_DAILY_LOSS"),
            (replace(self.snapshot, daily_net_pnl_r=float("nan")), "BROKER_HEALTH_FAILURE"),
        ]
        for i, (snapshot, expected) in enumerate(cases):
            path = Path(self.tmp.name) / f"case{i}.sqlite"
            initialize_model(path, self.now)
            self.assertEqual(check_model(path, self.kill, self.now, snapshot), expected)
            self.assertEqual(check_model(path, self.kill, self.now, self.snapshot), expected)

    def test_expiry_limit_and_consecutive_failures(self):
        self.assertEqual(self.check(now=self.now + timedelta(days=90)), "VALIDATION_EXPIRED")
        path = Path(self.tmp.name) / "fail.sqlite"
        initialize_model(path, self.now)
        self.assertEqual(record_outcome(path, self.now, "execution_exception"), "")
        self.assertEqual(record_outcome(path, self.now, "execution_exception"), "")
        self.assertEqual(record_outcome(path, self.now, "execution_exception"), "SHUTDOWN_FAILURE_LIMIT")
        self.assertEqual(check_model(path, self.kill, self.now, self.snapshot), "SHUTDOWN_FAILURE_LIMIT")
        limit = Path(self.tmp.name) / "limit.sqlite"
        initialize_model(limit, self.now)
        with closing(sqlite3.connect(limit)) as db, db:
            db.execute("UPDATE state SET completed=10")
        self.assertEqual(check_model(limit, self.kill, self.now, self.snapshot), "VALIDATION_TRADE_LIMIT")

    def test_missing_corrupt_state_and_invalid_expiry_fail(self):
        with self.assertRaises(SafeguardError):
            check_model(Path(self.tmp.name) / "missing.sqlite", self.kill, self.now, self.snapshot)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("UPDATE state SET expires='bad'")
        with self.assertRaises(SafeguardError):
            self.check()
        with self.assertRaises(SafeguardError):
            initialize_model(Path(self.tmp.name) / "other.sqlite", self.now, timedelta(days=91))


if __name__ == "__main__":
    unittest.main()
