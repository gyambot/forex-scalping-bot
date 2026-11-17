import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from paper_trading.candidate9_demo_submission import submit_once, supervise_until_shutdown, watch_once
from paper_trading.candidate9_lifecycle_simulation import create, restart, state
from paper_trading.candidate9_risk import BrokerConstraints
from paper_trading.candidate9_safeguard_model import SafeguardError
from scripts.backtest import Bar
from tests.test_candidate9_order_preview import PreviewBroker


class SubmissionBroker(PreviewBroker):
    DEAL_ENTRY_IN = 0
    DEAL_ENTRY_OUT = 1
    DEAL_TYPE_BUY = 0
    DEAL_TYPE_SELL = 1
    DEAL_REASON_SL = 4
    DEAL_REASON_TP = 5
    POSITION_TYPE_BUY = 0
    POSITION_TYPE_SELL = 1

    def __init__(self, now):
        super().__init__(now)
        self.symbol.trade_tick_size = 0.00001
        self.symbol.trade_stops_level = 20
        self.symbol.point = 0.00001
        self.symbol.volume_min = 0.01
        self.symbol.volume_max = 10
        self.symbol.volume_step = 0.01
        self.result = SimpleNamespace(retcode=10009, order=10, deal=20)
        self.calls = []
        self.profit = -1
        self.history = []
        self.entry_deal = None
        self.position_deals = []

    def history_deals_get(self, *_args, **kwargs):
        if "ticket" in kwargs:
            return [] if self.entry_deal is None else [self.entry_deal]
        if "position" in kwargs:
            return self.position_deals
        return self.history

    def order_calc_profit(self, *_args):
        return self.profit

    def prepare_fill(self, now):
        common = dict(position_id=42, magic=77, symbol="EURUSD", volume=0.01,
                      commission=0.0, swap=0.0, fee=0.0, time_msc=int(now.timestamp() * 1000))
        self.entry_deal = SimpleNamespace(**common, ticket=20, order=10, entry=0, type=0,
                                          reason=0, price=1.1002, profit=0.0)
        exit_deal = SimpleNamespace(**common, ticket=21, order=11, entry=1, type=1,
                                    reason=5, price=1.1022, profit=2.0)
        self.position_deals = [self.entry_deal, exit_deal]
        self.next_position = SimpleNamespace(identifier=42, magic=77, symbol="EURUSD", type=0,
                                             volume=0.01, sl=1.0992, tp=1.1022,
                                             profit=0, swap=0)

    def order_send(self, request):
        self.calls.append(request)
        if isinstance(self.result, Exception):
            raise self.result
        if hasattr(self, "next_position"):
            self.positions = [self.next_position]
        return self.result


class DemoSubmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / "state.sqlite"
        self.kill = self.root / "kill"
        self.project_kill = self.root / "project_kill"
        self.now = datetime(2026, 11, 22, 22, 5, tzinfo=timezone.utc)
        create(self.path, self.now - timedelta(days=1), self.now + timedelta(days=1))
        self.broker = SubmissionBroker(self.now)
        self.friday = Bar(datetime(2026, 11, 20, 21, 55, tzinfo=timezone.utc),
                          1.1, 1.1001, 1.0999, 1.1)
        self.reopening = Bar(self.now - timedelta(minutes=5), 1.099, 1.0991, 1.0989, 1.099)
        self.constraints = BrokerConstraints(D("0.00001"), D("0.0002"), D("0.01"),
                                             D("10"), D("0.01"), D("100"))

    def submit(self, enabled=True):
        with patch("paper_trading.candidate9_demo_submission.EXECUTION_INHIBITED", False):
            return self.call(enabled)

    def call(self, enabled):
        return submit_once(self.path, self.kill, self.broker, enabled=enabled,
                           clock=lambda: self.now, expected_login=123, epoch_is_verified_utc=True,
                           friday=self.friday, reopening=self.reopening, volume=D("0.01"),
                           risk_budget=D("2"), costs_per_lot=D("0"),
                           constraints=self.constraints, magic=77)

    def test_disarmed_and_project_kill_never_query_or_submit(self):
        with self.assertRaisesRegex(SafeguardError, "disarmed"):
            self.submit(False)
        with self.assertRaisesRegex(SafeguardError, "disarmed"):
            self.call(True)
        self.assertEqual(state(self.path)[0], "IDLE")
        self.project_kill.touch()
        with patch("paper_trading.candidate9_demo_submission.PROJECT_KILL_SWITCH", self.project_kill):
            self.assertEqual(self.submit(), "KILL_SWITCH_TRIGGERED")
        self.assertEqual(self.broker.calls, [])
        self.assertEqual(state(self.path), ("SHUTDOWN", "KILL_SWITCH_TRIGGERED"))

    def test_accepted_is_manual_review_not_protected_position(self):
        with patch("paper_trading.candidate9_demo_submission.PROJECT_KILL_SWITCH", self.project_kill):
            self.assertEqual(self.submit(), "MANUAL_REVIEW_REQUIRED")
            self.assertEqual(state(self.path)[1], "FILL_VERIFICATION_FAILURE")
            self.assertEqual(restart(self.path, self.now), "MANUAL_REVIEW_REQUIRED")
            with self.assertRaises(SafeguardError):
                self.submit()
        self.assertEqual(len(self.broker.calls), 1)

    def test_verified_fill_watch_close_and_history_reconciliation(self):
        self.broker.prepare_fill(self.now)
        with patch("paper_trading.candidate9_demo_submission.PROJECT_KILL_SWITCH", self.project_kill):
            self.assertEqual(self.submit(), "POSITION_OPEN")
            self.assertEqual(watch_once(self.path, self.kill, self.broker, now=self.now),
                             "POSITION_SUPERVISION")
            self.broker.positions = []
            self.assertEqual(watch_once(self.path, self.kill, self.broker, now=self.now), "SHUTDOWN")
        self.assertEqual(state(self.path), ("SHUTDOWN", "ONE_TRADE_COMPLETED"))
        self.assertEqual(len(self.broker.calls), 1)

    def test_missing_protection_reconciliation_and_floating_loss_latch(self):
        for variant in ("stop", "target", "history", "loss", "kill"):
            with self.subTest(variant=variant):
                self.path = self.root / (variant + "_open.sqlite")
                create(self.path, self.now - timedelta(days=1), self.now + timedelta(days=1))
                self.broker = SubmissionBroker(self.now)
                self.broker.prepare_fill(self.now)
                with patch("paper_trading.candidate9_demo_submission.PROJECT_KILL_SWITCH", self.project_kill):
                    self.assertEqual(self.submit(), "POSITION_OPEN")
                    if variant == "stop":
                        self.broker.next_position.sl = 0
                    elif variant == "target":
                        self.broker.next_position.tp = 0
                    elif variant == "history":
                        self.broker.positions = []
                        self.broker.position_deals = []
                    elif variant == "loss":
                        self.broker.next_position.profit = -2
                    else:
                        self.kill.touch()
                    self.assertEqual(watch_once(self.path, self.kill, self.broker, now=self.now),
                                     "MANUAL_REVIEW_REQUIRED")
                    expected_reason = {
                        "stop": "PROTECTION_FAILURE", "target": "PROTECTION_FAILURE",
                        "history": "RECONCILIATION_FAILURE", "loss": "SHUTDOWN_DAILY_LOSS",
                        "kill": "KILL_SWITCH_TRIGGERED",
                    }
                    self.assertEqual(state(self.path)[1], expected_reason[variant])
                    self.assertEqual(restart(self.path, self.now), "MANUAL_REVIEW_REQUIRED")
                    if variant == "kill":
                        self.kill.unlink()
                self.assertEqual(len(self.broker.calls), 1)

    def test_supervision_loop_reconciles_close_and_stop_latches(self):
        self.broker.prepare_fill(self.now)
        with patch("paper_trading.candidate9_demo_submission.PROJECT_KILL_SWITCH", self.project_kill):
            self.assertEqual(self.submit(), "POSITION_OPEN")
            def close_after_poll(_seconds):
                self.broker.positions = []
            self.assertEqual(supervise_until_shutdown(
                self.path, self.kill, self.broker, clock=lambda: self.now,
                stop_requested=lambda: False, sleep=close_after_poll), "SHUTDOWN")
        self.assertEqual(state(self.path), ("SHUTDOWN", "ONE_TRADE_COMPLETED"))

        self.path = self.root / "manual_stop.sqlite"
        create(self.path, self.now - timedelta(days=1), self.now + timedelta(days=1))
        self.broker = SubmissionBroker(self.now)
        self.broker.prepare_fill(self.now)
        with patch("paper_trading.candidate9_demo_submission.PROJECT_KILL_SWITCH", self.project_kill):
            self.assertEqual(self.submit(), "POSITION_OPEN")
            self.assertEqual(supervise_until_shutdown(
                self.path, self.kill, self.broker, clock=lambda: self.now,
                stop_requested=lambda: True), "MANUAL_REVIEW_REQUIRED")
        self.assertEqual(state(self.path)[1], "SUPERVISION_STOPPED")
        self.assertEqual(len(self.broker.positions), 1)

    def test_fill_mismatch_and_supervision_failure_are_terminal(self):
        for variant in ("partial", "slippage", "clock", "stale_close"):
            with self.subTest(variant=variant):
                self.path = self.root / (variant + "_verify.sqlite")
                create(self.path, self.now - timedelta(days=1), self.now + timedelta(days=1))
                self.broker = SubmissionBroker(self.now)
                self.broker.prepare_fill(self.now)
                if variant == "partial":
                    self.broker.entry_deal.volume = 0.005
                elif variant == "slippage":
                    self.broker.entry_deal.price = 1.10021
                with patch("paper_trading.candidate9_demo_submission.PROJECT_KILL_SWITCH", self.project_kill):
                    result = self.submit()
                    if variant in ("partial", "slippage"):
                        self.assertEqual(result, "MANUAL_REVIEW_REQUIRED")
                        self.assertEqual(state(self.path)[1], "FILL_VERIFICATION_FAILURE")
                    else:
                        self.assertEqual(result, "POSITION_OPEN")
                        if variant == "clock":
                            result = supervise_until_shutdown(
                                self.path, self.kill, self.broker,
                                clock=lambda: datetime(2026, 1, 1),
                                stop_requested=lambda: False)
                        else:
                            self.broker.positions = []
                            self.broker.tick.time_msc -= 6000
                            result = watch_once(self.path, self.kill, self.broker, now=self.now)
                        self.assertEqual(result, "MANUAL_REVIEW_REQUIRED")
                        self.assertEqual(state(self.path)[1], "SUPERVISION_FAILURE" if variant == "clock"
                                         else "BROKER_HEALTH_FAILURE")
                self.assertEqual(len(self.broker.calls), 1)

    def test_rejected_unknown_and_exception_never_retry(self):
        for name, response, expected in (
            ("rejected", SimpleNamespace(retcode=10006), "SHUTDOWN"),
            ("partial", SimpleNamespace(retcode=10010), "MANUAL_REVIEW_REQUIRED"),
            ("none", None, "MANUAL_REVIEW_REQUIRED"),
            ("exception", RuntimeError("timeout"), "MANUAL_REVIEW_REQUIRED"),
        ):
            with self.subTest(name=name):
                self.path = self.root / (name + ".sqlite")
                create(self.path, self.now - timedelta(days=1), self.now + timedelta(days=1))
                self.broker = SubmissionBroker(self.now)
                self.broker.result = response
                with patch("paper_trading.candidate9_demo_submission.PROJECT_KILL_SWITCH", self.project_kill):
                    self.assertEqual(self.submit(), expected)
                    self.assertEqual(restart(self.path, self.now), expected)
                    with self.assertRaises(SafeguardError):
                        self.submit()
                self.assertEqual(len(self.broker.calls), 1)

    def test_bad_risk_daily_loss_and_missing_history_do_not_submit(self):
        for name in ("risk", "daily", "history", "constraints"):
            with self.subTest(name=name):
                self.path = self.root / (name + ".sqlite")
                create(self.path, self.now - timedelta(days=1), self.now + timedelta(days=1))
                self.broker = SubmissionBroker(self.now)
                if name == "risk":
                    self.broker.profit = -3
                elif name == "daily":
                    self.broker.history = [SimpleNamespace(type=0, time_msc=int(self.now.timestamp() * 1000),
                                                           profit=-2, commission=0, swap=0, fee=0)]
                elif name == "history":
                    self.broker.history = None
                else:
                    self.broker.symbol.trade_tick_size = 0.0001
                with patch("paper_trading.candidate9_demo_submission.PROJECT_KILL_SWITCH", self.project_kill):
                    self.assertNotEqual(self.submit(), "POSITION_OPEN")
                self.assertEqual(len(self.broker.calls), 0)
                self.assertIn(state(self.path)[0], ("SHUTDOWN", "MANUAL_REVIEW_REQUIRED"))

    def test_concurrent_requests_submit_only_once(self):
        def run():
            try:
                return self.call(True)
            except SafeguardError:
                return "REFUSED"
        with patch("paper_trading.candidate9_demo_submission.PROJECT_KILL_SWITCH", self.project_kill):
            with patch("paper_trading.candidate9_demo_submission.EXECUTION_INHIBITED", False):
                with ThreadPoolExecutor(max_workers=2) as pool:
                    results = list(pool.map(lambda _: run(), range(2)))
        self.assertCountEqual(results, ["MANUAL_REVIEW_REQUIRED", "REFUSED"])
        self.assertEqual(len(self.broker.calls), 1)


if __name__ == "__main__":
    unittest.main()
