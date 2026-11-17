import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from paper_trading.candidate9_position_watch import ExpectedPosition, inspect_position
from paper_trading.candidate9_validation_journal import create_journal, recover
from tests.test_candidate9_broker_observation import ReadOnlyBroker


class ActivePositionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "journal.sqlite"
        self.kill = Path(self.tmp.name) / "kill"
        self.now = datetime(2026, 11, 22, 22, 5, tzinfo=timezone.utc)
        create_journal(self.path, self.now - timedelta(days=1), self.now + timedelta(days=1))
        self.broker = ReadOnlyBroker(self.now)
        self.broker.POSITION_TYPE_BUY = 0
        self.broker.POSITION_TYPE_SELL = 1
        self.position = SimpleNamespace(identifier=42, magic=77, symbol="EURUSD",
                                        type=0, volume=0.01, sl=1.0992, tp=1.1022)
        self.broker.positions = [self.position]
        self.expected = ExpectedPosition(123, 42, 77, "long", Decimal("0.01"),
                                         Decimal("1.0992"), Decimal("1.1022"))

    def inspect(self):
        return inspect_position(self.broker, self.expected, now=self.now, verified_utc=True,
                                kill_switch=self.kill, journal_path=self.path,
                                daily_net_pnl_r=Decimal("0"))

    def test_exact_position_and_closure_needs_reconciliation(self):
        self.assertEqual(self.inspect(), "POSITION_OBSERVED_NO_EXECUTION")
        self.broker.positions = []
        self.assertEqual(self.inspect(), "CLOSURE_RECONCILIATION_REQUIRED")
        self.assertEqual(recover(self.path, self.now), "IDLE_NO_EXECUTION")

    def test_changed_protection_latches(self):
        self.position.sl = 0
        self.assertEqual(self.inspect(), "PROTECTION_FAILURE")
        self.assertEqual(recover(self.path, self.now), "PROTECTION_FAILURE")

    def test_unknown_position_and_kill_latch_without_order(self):
        self.position.magic = 999
        self.assertEqual(self.inspect(), "UNEXPECTED_OPEN_POSITION")
        self.assertEqual(recover(self.path, self.now), "UNEXPECTED_OPEN_POSITION")

    def test_kill_file_latches(self):
        self.kill.write_text("stop", encoding="utf-8")
        self.assertEqual(self.inspect(), "KILL_SWITCH_TRIGGERED")
        self.assertEqual(recover(self.path, self.now), "KILL_SWITCH_TRIGGERED")
        self.assertEqual(len(self.broker.positions), 1)

    def test_disconnected_stale_and_unavailable_orders(self):
        self.broker.tick.time_msc -= 6000
        self.assertEqual(self.inspect(), "BROKER_HEALTH_FAILURE")
        self.assertEqual(recover(self.path, self.now), "BROKER_HEALTH_FAILURE")

    def test_daily_loss_shutdown(self):
        self.assertEqual(inspect_position(self.broker, self.expected, now=self.now,
                                          verified_utc=True, kill_switch=self.kill,
                                          journal_path=self.path, daily_net_pnl_r=Decimal("-1")),
                         "SHUTDOWN_DAILY_LOSS")
        self.assertEqual(recover(self.path, self.now), "SHUTDOWN_DAILY_LOSS")

    def test_high_spread_shutdown(self):
        self.broker.tick.ask = 1.10031
        self.assertEqual(self.inspect(), "HIGH_SPREAD_DURING_POSITION")
        self.assertEqual(recover(self.path, self.now), "HIGH_SPREAD_DURING_POSITION")
        self.assertEqual(len(self.broker.positions), 1)


if __name__ == "__main__":
    unittest.main()
