import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from paper_trading.candidate9_readiness_preflight import inspect_candidate
from paper_trading.candidate9_risk import BrokerConstraints
from paper_trading.candidate9_safeguard_model import SafeguardError, initialize_model
from paper_trading.candidate9_validation_journal import create_journal, recover
from scripts.backtest import Bar
from tests.test_candidate9_broker_observation import ReadOnlyBroker


class Candidate9PreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.model = base / "model.sqlite"
        self.journal = base / "journal.sqlite"
        self.kill = base / "kill"
        self.now = datetime(2026, 11, 22, 22, 5, tzinfo=timezone.utc)
        initialize_model(self.model, self.now - timedelta(days=1))
        create_journal(self.journal, self.now - timedelta(days=1), self.now + timedelta(days=30))
        self.module = ReadOnlyBroker(self.now)
        friday = datetime(2026, 11, 20, 21, 55, tzinfo=timezone.utc)
        reopening = self.now - timedelta(minutes=5)
        self.arguments = dict(
            module=self.module, model_path=self.model, journal_path=self.journal,
            kill_switch=self.kill, now=self.now, expected_login=123, epoch_is_verified_utc=True,
            friday=Bar(friday, 1.1, 1.1001, 1.0999, 1.1),
            reopening=Bar(reopening, 1.099, 1.0991, 1.0989, 1.099),
            daily_net_pnl_r=0, volume=Decimal("0.01"), risk_budget=Decimal("2"),
            costs_per_lot=Decimal("0"),
            constraints=BrokerConstraints(Decimal("0.00001"), Decimal("0.0002"),
                Decimal("0.01"), Decimal("10"), Decimal("0.01"), Decimal("100")),
        )

    def test_full_read_only_path_never_submits_or_records_intent(self):
        result = inspect_candidate(**self.arguments)
        self.assertEqual(result.status, "READ_ONLY_CHECKS_PASSED_NO_EXECUTION")
        self.assertEqual(result.signal.direction, "long")
        self.assertEqual(result.risk.stop, Decimal("1.0992"))
        self.assertEqual(recover(self.journal, self.now), "IDLE_NO_EXECUTION")

    def test_kill_switch_and_broker_failure_latch(self):
        self.kill.write_text("stop", encoding="utf-8")
        self.assertEqual(inspect_candidate(**self.arguments).status, "KILL_SWITCH_TRIGGERED")
        self.kill.unlink()
        self.assertEqual(inspect_candidate(**self.arguments).status, "KILL_SWITCH_TRIGGERED")

    def test_unexpected_position_latches(self):
        self.module.positions = [object()]
        self.assertEqual(inspect_candidate(**self.arguments).status, "UNEXPECTED_OPEN_POSITION")
        self.module.positions = []
        self.assertEqual(inspect_candidate(**self.arguments).status, "UNEXPECTED_OPEN_POSITION")

    def test_spread_boundary_and_skip(self):
        self.module.tick.ask = 1.1003
        self.assertEqual(inspect_candidate(**self.arguments).status, "READ_ONLY_CHECKS_PASSED_NO_EXECUTION")
        self.module.tick.ask = 1.10031
        self.assertEqual(inspect_candidate(**self.arguments).status, "SIGNAL_SKIPPED_HIGH_SPREAD")

    def test_daily_loss_and_expiry_latch(self):
        self.arguments["daily_net_pnl_r"] = -1
        self.assertEqual(inspect_candidate(**self.arguments).status, "SHUTDOWN_DAILY_LOSS")
        self.arguments["daily_net_pnl_r"] = 0
        self.assertEqual(inspect_candidate(**self.arguments).status, "SHUTDOWN_DAILY_LOSS")

    def test_risk_failure_latches_and_raises(self):
        self.arguments["risk_budget"] = Decimal("0.5")
        with self.assertRaisesRegex(SafeguardError, "exceed"):
            inspect_candidate(**self.arguments)
        self.assertEqual(recover(self.journal, self.now), "RISK_CHECK_FAILURE")

    def test_missed_entry_and_unknown_time(self):
        self.arguments["now"] = self.now + timedelta(seconds=6)
        self.assertEqual(inspect_candidate(**self.arguments).status, "SIGNAL_MISSED")
        self.arguments["now"] = self.now
        self.arguments["epoch_is_verified_utc"] = False
        self.assertEqual(inspect_candidate(**self.arguments).status, "BROKER_HEALTH_FAILURE")
        self.assertEqual(recover(self.journal, self.now), "BROKER_HEALTH_FAILURE")

    def test_broker_exception_stops_and_persists(self):
        def disconnected():
            raise RuntimeError("broker unavailable")
        self.module.terminal_info = disconnected
        self.assertEqual(inspect_candidate(**self.arguments).status, "BROKER_HEALTH_FAILURE")
        self.assertEqual(recover(self.journal, self.now), "BROKER_HEALTH_FAILURE")


if __name__ == "__main__":
    unittest.main()
