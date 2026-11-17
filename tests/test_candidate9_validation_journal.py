import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from paper_trading.candidate9_reconciliation import ReconciledTrade
from paper_trading.candidate9_safeguard_model import SafeguardError
from paper_trading.candidate9_validation_journal import (
    EntryIntent, create_journal, record_completion, record_intent, recover, shutdown,
)


class ValidationJournalTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / "journal.sqlite"
        self.now = datetime(2026, 11, 16, tzinfo=timezone.utc)
        create_journal(self.path, self.now, self.now + timedelta(days=90))
        self.intent = EntryIntent("weekend-1", "long", 1.1, 1.099, -10, 2, 1.0992, self.now)

    def test_intent_is_durable_and_restart_is_terminal(self):
        record_intent(self.path, self.intent)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM trade").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT kind FROM events").fetchone()[0], "INTENT_RECORDED")
        self.assertEqual(recover(self.path, self.now), "EXECUTION_UNCERTAIN")
        self.assertEqual(recover(self.path, self.now), "EXECUTION_UNCERTAIN")
        with self.assertRaises(SafeguardError):
            record_intent(self.path, self.intent)

    def test_completion_and_rejection_latch(self):
        record_intent(self.path, self.intent)
        trade = ReconciledTrade(Decimal("1.1"), Decimal("1.102"), Decimal("2"),
                                Decimal("1"), Decimal("0"), self.now,
                                self.now + timedelta(minutes=5), "take_profit")
        record_completion(self.path, self.now + timedelta(minutes=5), trade)
        self.assertEqual(recover(self.path, self.now), "ONE_TRADE_COMPLETED")
        with self.assertRaises(SafeguardError):
            record_completion(self.path, self.now, trade)
        other = self.path.with_name("rejected.sqlite")
        create_journal(other, self.now, self.now + timedelta(days=1))
        record_intent(other, self.intent)
        shutdown(other, self.now, "ORDER_REJECTED")
        self.assertEqual(recover(other, self.now), "ORDER_REJECTED")

    def test_expiry_duplicate_and_corruption_fail_closed(self):
        expired = EntryIntent("late", "short", 1.1, 1.101, 10, 2, 1.1,
                              self.now + timedelta(days=90))
        with self.assertRaisesRegex(SafeguardError, "VALIDATION_EXPIRED"):
            record_intent(self.path, expired)
        self.assertEqual(recover(self.path, self.now), "VALIDATION_EXPIRED")
        with self.assertRaises(FileExistsError):
            create_journal(self.path, self.now, self.now + timedelta(days=1))
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("UPDATE study SET state='broken'")
        with self.assertRaises(SafeguardError):
            recover(self.path, self.now)


if __name__ == "__main__":
    unittest.main()
