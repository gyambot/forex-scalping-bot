import csv
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from paper_trading import mt5_connector
from paper_trading.demo_executor import (
    DemoExecutor,
    ExecutorError,
    validate_demo_account,
)
from paper_trading.demo_trade_utils import TRADE_FIELDS, read_trade_log
from paper_trading.execution_logging import EXECUTION_FIELDS, read_events
from paper_trading.execution_reconciliation import build_trade_record
from paper_trading.generate_demo_metrics import calculate_demo_metrics
from paper_trading.manual_trade_capture import append_completed_trade
from paper_trading.mt5_connector import EXPECTED_SERVER, MT5Config
from paper_trading.tests.test_manual_trade_capture import manual_trade


class FakeMT5:
    ACCOUNT_TRADE_MODE_DEMO = 0
    ACCOUNT_TRADE_MODE_REAL = 2
    SYMBOL_TRADE_MODE_DISABLED = 0
    SYMBOL_TRADE_MODE_CLOSEONLY = 3
    SYMBOL_TRADE_MODE_FULL = 4
    SYMBOL_FILLING_FOK = 1
    ORDER_FILLING_FOK = 0
    ORDER_FILLING_IOC = 1
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    TRADE_ACTION_DEAL = 1
    TRADE_ACTION_SLTP = 6
    ORDER_TIME_GTC = 0
    TRADE_RETCODE_DONE = 10009
    TRADE_RETCODE_REJECT = 10006
    TRADE_RETCODE_INVALID = 10013
    TRADE_RETCODE_INVALID_STOPS = 10016
    TRADE_RETCODE_NO_MONEY = 10019
    DEAL_ENTRY_IN = 0
    DEAL_ENTRY_OUT = 1
    DEAL_ENTRY_OUT_BY = 3
    DEAL_TYPE_BUY = 0
    DEAL_TYPE_SELL = 1
    DEAL_REASON_SL = 4
    DEAL_REASON_TP = 5
    TIMEFRAME_M5 = 5

    def __init__(self):
        self.account = SimpleNamespace(
            login=123,
            server=EXPECTED_SERVER,
            trade_mode=self.ACCOUNT_TRADE_MODE_DEMO,
            trade_allowed=True,
            trade_expert=True,
        )
        self.terminal = SimpleNamespace(
            connected=True,
            trade_allowed=True,
            tradeapi_disabled=False,
        )
        self.symbol = SimpleNamespace(
            visible=True,
            trade_mode=self.SYMBOL_TRADE_MODE_FULL,
            volume_min=0.01,
            volume_max=100.0,
            volume_step=0.01,
            filling_mode=self.SYMBOL_FILLING_FOK,
            trade_tick_size=0.00001,
            trade_tick_value=1.0,
        )
        self.tick = SimpleNamespace(bid=1.10000, ask=1.10012)
        self.position = None
        self.order_requests = []
        self.position_queries = 0
        self.order_result = SimpleNamespace(retcode=self.TRADE_RETCODE_DONE, deal=555, order=666)
        self.fill_deal = SimpleNamespace(
            position_id=777,
            time_msc=0,
            price=1.10012,
        )
        self.position_history = []

    def terminal_info(self):
        return self.terminal

    def account_info(self):
        return self.account

    def symbol_info(self, symbol):
        return self.symbol if symbol == "EURUSD" else None

    def symbol_info_tick(self, symbol):
        return self.tick if symbol == "EURUSD" else None

    def positions_get(self, **kwargs):
        self.position_queries += 1
        return [] if self.position is None else [self.position]

    def orders_get(self):
        return []

    def copy_rates_from_pos(self, symbol, timeframe, start_pos, count):
        if start_pos == 0:
            return [{"time": self.current_bar_epoch, "open": 1.10000}]
        return []

    def order_send(self, request):
        self.order_requests.append(request)
        if request["action"] == self.TRADE_ACTION_DEAL:
            if (
                self.order_result is None
                or self.order_result.retcode != self.TRADE_RETCODE_DONE
            ):
                return self.order_result
            self.fill_deal.time_msc = self.planned_epoch_ms
            self.position = SimpleNamespace(
                identifier=777,
                ticket=888,
                sl=request["sl"],
                tp=request["tp"],
                magic=request["magic"],
                symbol="EURUSD",
            )
            return self.order_result
        raise AssertionError("unexpected stop/target modification")

    def history_deals_get(self, **kwargs):
        if "ticket" in kwargs:
            return [self.fill_deal]
        if "position" in kwargs:
            return self.position_history
        return []


def breakout_bars():
    signal_bar_time = datetime(2026, 11, 16, 8, 0, tzinfo=timezone(timedelta(hours=2)))
    bars = []
    for index in range(20):
        stamp = signal_bar_time - timedelta(minutes=5 * (20 - index))
        bars.append(
            {
                "timestamp": stamp.isoformat(),
                "open": 1.1000,
                "high": 1.1005,
                "low": 1.0995,
                "close": 1.1000,
            }
        )
    bars.append(
        {
            "timestamp": signal_bar_time.isoformat(),
            "open": 1.1000,
            "high": 1.1007,
            "low": 1.0999,
            "close": 1.1006,
        }
    )
    return bars


class DemoExecutorTests(unittest.TestCase):
    def test_validation_does_not_submit_after_planned_open(self):
        fake = FakeMT5()
        bars = breakout_bars()
        planned = datetime.fromisoformat(bars[-1]["timestamp"]) + timedelta(minutes=5)
        fake.current_bar_epoch = int(planned.replace(tzinfo=timezone.utc).timestamp())
        fake.tick.time = fake.current_bar_epoch
        config = MT5Config(login=123, server=EXPECTED_SERVER, broker_utc_offset="+02:00")
        with tempfile.TemporaryDirectory() as folder, patch.dict("os.environ", {"MT5_DEMO_VOLUME": "0.01"}), \
             patch("paper_trading.demo_executor.mt5_connector._require_connection", return_value=(fake, config)), \
             patch("paper_trading.demo_executor.mt5_connector.verify_trade_permissions", return_value={"permitted": True}), \
             patch("paper_trading.demo_executor.mt5_connector.verify_symbol", return_value=fake.symbol), \
             patch("paper_trading.mt5_price_feed.get_recent_m5_bars", return_value=bars), \
             patch("paper_trading.demo_executor.DemoExecutor._time", return_value=planned + timedelta(milliseconds=1)):
            base = Path(folder)
            executor = DemoExecutor(execution_log=base / "events.csv", state_file=base / "state.json",
                                    trade_log=base / "DEMO_TRADING_LOG.csv")
            executor.state_file.write_text(json.dumps({
                "processed_signal_times": [], "active_position": None,
                "single_trade_validation": {"phase": "armed", **executor._validation_descriptor()},
            }), encoding="utf-8")
            executor._process_once(validation_run=True)
            self.assertEqual(fake.order_requests, [])
            self.assertIn("signal_missed", [event["event"] for event in read_events(executor.execution_log)])

    def test_validation_preflight_checks_stale_offset_pending_and_schema(self):
        fake = FakeMT5()
        now = datetime.now(timezone(timedelta(hours=2))).replace(microsecond=0)
        wall = now.replace(tzinfo=timezone.utc)
        fake.tick.time = int(wall.timestamp())
        fake.current_bar_epoch = int(wall.replace(minute=(wall.minute // 5) * 5, second=0).timestamp())
        config = MT5Config(login=123, server=EXPECTED_SERVER, broker_utc_offset="+02:00")
        with tempfile.TemporaryDirectory() as folder, patch.dict(
            "os.environ", {"MT5_BROKER_UTC_OFFSET": "+02:00", "MT5_DEMO_VOLUME": "0.01"}
        ), patch("paper_trading.demo_executor.mt5_connector.initialize_connection", return_value=True), \
             patch("paper_trading.demo_executor.mt5_connector.shutdown_connection"), \
             patch("paper_trading.demo_executor.mt5_connector._require_connection", return_value=(fake, config)), \
             patch("paper_trading.demo_executor.mt5_connector.verify_trade_permissions", return_value={"permitted": True}), \
             patch("paper_trading.demo_executor.DemoExecutor._time", return_value=now):
            base = Path(folder)
            study = base / "DEMO_TRADING_LOG.csv"
            study.write_text(",".join(TRADE_FIELDS) + "\n", encoding="utf-8")
            metrics = base / "metrics.json"
            metrics.write_text(json.dumps(calculate_demo_metrics([])), encoding="utf-8")
            gate = base / "gate.md"
            gate.write_text("- **Demo Trades Completed:** **0 / 100**\n"
                            "- **V2 Eligibility:** **BLOCKED**\n"
                            "- **Reason:** **100 demo trades remain.**\n", encoding="utf-8")
            executor = DemoExecutor(execution_log=base / "events.csv", state_file=base / "state.json",
                                    trade_log=study, metrics_file=metrics, gate_file=gate)
            executor.verify_validation_only()
            self.assertFalse(executor.state_file.exists())
            with patch.object(fake, "orders_get", return_value=[object()]):
                with self.assertRaisesRegex(ExecutorError, "pending orders"):
                    executor.verify_validation_only()
            with patch.dict("os.environ", {"MT5_BROKER_UTC_OFFSET": "+03:00"}):
                with self.assertRaisesRegex(ExecutorError, "broker offset"):
                    executor.verify_validation_only()
            fake.tick.time -= 130
            with self.assertRaisesRegex(ExecutorError, "stale|precedes"):
                executor.verify_validation_only()
            fake.tick.time += 130
            executor._validation_paths()["trade_log"].write_text("wrong,header\n", encoding="utf-8")
            with self.assertRaisesRegex(ExecutorError, "schema"):
                executor.verify_validation_only()
            self.assertEqual(fake.order_requests, [])

    def test_isolated_closure_and_recovery_preserve_study(self):
        for compliant in (True, False):
            with self.subTest(compliant=compliant), tempfile.TemporaryDirectory() as folder:
                base = Path(folder)
                fake = FakeMT5()
                planned = datetime(2026, 11, 16, 8, 5, tzinfo=timezone(timedelta(hours=2)))
                epoch = int(planned.replace(tzinfo=timezone.utc).timestamp() * 1000)
                delay = 0 if compliant else 1000
                fake.position_history = [
                    SimpleNamespace(entry=0, type=0, volume=0.01, price=1.1001,
                                    time_msc=epoch + delay, position_id=777, symbol="EURUSD",
                                    magic=26111601, order=666, profit=0, commission=-0.1, swap=0, fee=0),
                    SimpleNamespace(entry=1, type=1, volume=0.01, price=1.1021,
                                    time_msc=epoch + 300000, position_id=777, symbol="EURUSD",
                                    profit=2, commission=-0.1, swap=0, fee=0, reason=5),
                ]
                study = base / "DEMO_TRADING_LOG.csv"
                seed = manual_trade()
                seed["order_reference"] = "order=1001;position=1001"
                append_completed_trade(seed, study)
                loss = manual_trade("study-loss")
                loss.update({"pnl_pips": "-10", "pnl_r": "-1", "order_reference": "order=1002;position=1002"})
                append_completed_trade(loss, study)
                metrics_file = base / "DEMO_METRICS.json"
                gate_file = base / "DEMO_GATE_STATUS.md"
                metrics = calculate_demo_metrics(read_trade_log(study))
                metrics_file.write_text(json.dumps(metrics), encoding="utf-8")
                gate_file.write_text("unchanged study gate", encoding="utf-8")
                executor = DemoExecutor(execution_log=base / "events.csv", state_file=base / "state.json",
                                        trade_log=study, metrics_file=metrics_file, gate_file=gate_file)
                validation = {"phase": "monitoring", **executor._validation_descriptor()}
                active = {
                    "phase": "open", "position_id": 777, "order_ticket": 666, "deal_ticket": 555,
                    "signal": {"trade_id": "validation-1", "symbol": "EURUSD", "direction": "long",
                               "signal_bar_open_time_broker": "2026-11-16T08:00:00+02:00",
                               "signal_close": 1.1006, "prior_20_high": 1.1005, "prior_20_low": 1.0995},
                    "planned_entry_time_broker": planned.isoformat(), "submission_time_broker": planned.isoformat(),
                    "fill_time_broker": (planned + timedelta(milliseconds=delay)).isoformat(),
                    "fill_delay_ms": delay, "intended_entry": 1.1001, "entry_spread_pips": 1.2,
                    "volume": 0.01, "actual_stop": 1.0991, "actual_target": 1.1021,
                }
                state = {"processed_signal_times": [], "active_position": active,
                         "single_trade_validation": validation}
                executor.state_file.write_text(json.dumps(state), encoding="utf-8")
                before = [path.read_bytes() for path in (study, metrics_file, gate_file)]
                config = MT5Config(login=123, server=EXPECTED_SERVER, broker_utc_offset="+02:00")
                with patch("paper_trading.demo_executor.mt5_connector.initialize_connection", return_value=True), \
                     patch("paper_trading.demo_executor.mt5_connector.shutdown_connection"), \
                     patch("paper_trading.demo_executor.mt5_connector._require_connection", return_value=(fake, config)), \
                     patch("paper_trading.demo_executor.mt5_connector.verify_trade_permissions", return_value={"permitted": True}), \
                     patch("paper_trading.demo_executor.DemoExecutor._time", return_value=planned + timedelta(minutes=10)):
                    with patch.object(executor, "_refresh_validation_reports", side_effect=OSError("interrupted")):
                        with self.assertRaisesRegex(ExecutorError, "interrupted"):
                            executor._monitor_position(fake, config, fake.symbol, state, [])
                    saved = json.loads(executor.state_file.read_text())
                    saved["single_trade_validation"]["phase"] = "failed"
                    executor.state_file.write_text(json.dumps(saved), encoding="utf-8")
                    executor.recover_single_trade_validation()
                    with self.assertRaisesRegex(ExecutorError, "manual reconciliation"):
                        executor.recover_single_trade_validation()
                paths = executor._validation_paths()
                records = read_trade_log(paths["trade_log"])
                self.assertEqual(len(records), 1)
                self.assertEqual(records[0]["rule_compliant"], str(compliant).lower())
                isolated = json.loads(paths["metrics"].read_text())
                gate = json.loads(paths["gate"].read_text())
                self.assertEqual(isolated["eligible_trade_count"], int(compliant))
                self.assertEqual(gate["completed_trades"], int(compliant))
                self.assertEqual(before, [path.read_bytes() for path in (study, metrics_file, gate_file)])
                self.assertEqual(metrics, calculate_demo_metrics(read_trade_log(study)))
                self.assertEqual(metrics["metrics"]["profit_factor"], 2.0)
                self.assertEqual(metrics["metrics"]["expectancy"], 5.0)
                self.assertEqual(json.loads(executor.state_file.read_text())["single_trade_validation"]["phase"], "completed")
                self.assertEqual(fake.order_requests, [])
                duplicate = dict(records[0], trade_id="another-id")
                with self.assertRaisesRegex(ValueError, "broker reference"):
                    append_completed_trade(duplicate, study)

    def test_validation_descriptor_fails_closed_for_legacy_and_alias(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            executor = DemoExecutor(state_file=base / "state.json", execution_log=base / "events.csv",
                                    trade_log=base / "DEMO_TRADING_LOG.csv",
                                    metrics_file=base / "DEMO_METRICS.json", gate_file=base / "gate.md")
            with self.assertRaisesRegex(ExecutorError, "classification"):
                executor._check_validation_descriptor({"phase": "monitoring"})
            invalid = executor._validation_descriptor()
            invalid["destinations"]["trade_log"] = str(executor.trade_log.resolve())
            with self.assertRaisesRegex(ExecutorError, "destinations"):
                executor._check_validation_descriptor(invalid)
            executor.metrics_file = base / "VALIDATION_METRICS.json"
            with self.assertRaisesRegex(ExecutorError, "alias"):
                executor._validation_paths()

    def test_validation_stops_on_unexpected_position_before_signal_evaluation(self):
        fake = FakeMT5()
        fake.position = SimpleNamespace(identifier=11, ticket=11, symbol="EURUSD")
        config = MT5Config(login=123, server=EXPECTED_SERVER, broker_utc_offset="+02:00")
        with tempfile.TemporaryDirectory() as folder, patch(
            "paper_trading.demo_executor.mt5_connector._require_connection",
            return_value=(fake, config),
        ), patch(
            "paper_trading.demo_executor.mt5_connector.verify_trade_permissions",
            return_value={"permitted": True},
        ), patch(
            "paper_trading.demo_executor.mt5_connector.verify_symbol",
            return_value=fake.symbol,
        ), patch("paper_trading.mt5_price_feed.get_recent_m5_bars") as bars:
            base = Path(folder)
            executor = DemoExecutor(
                execution_log=base / "events.csv", state_file=base / "state.json"
            )
            executor.state_file.write_text(
                json.dumps({
                    "processed_signal_times": [],
                    "active_position": None,
                    "single_trade_validation": {"phase": "armed", **executor._validation_descriptor()},
                }),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ExecutorError, "unexpected.*position"):
                executor._process_once(validation_run=True)
            bars.assert_not_called()
            self.assertEqual(fake.order_requests, [])

    def test_validation_runner_failure_is_persistently_disarmed(self):
        fake = FakeMT5()
        config = MT5Config(login=123, server=EXPECTED_SERVER, broker_utc_offset="+02:00")
        with tempfile.TemporaryDirectory() as folder, patch.dict(
            "os.environ", {"MT5_DEMO_VOLUME": "0.01"}
        ), patch(
            "paper_trading.demo_executor.mt5_connector.initialize_connection", return_value=True
        ), patch(
            "paper_trading.demo_executor.mt5_connector.shutdown_connection"
        ), patch(
            "paper_trading.demo_executor.mt5_connector._require_connection", return_value=(fake, config)
        ), patch(
            "paper_trading.demo_executor.mt5_connector.verify_trade_permissions", return_value={"permitted": True}
        ), patch(
            "paper_trading.demo_executor.DemoExecutor._verify_validation_startup"
        ), patch(
            "paper_trading.demo_executor.DemoExecutor._process_once",
            side_effect=ExecutorError("reconciliation failed"),
        ):
            base = Path(folder)
            executor = DemoExecutor(execution_log=base / "events.csv", state_file=base / "state.json")
            with self.assertRaisesRegex(ExecutorError, "reconciliation failed"):
                executor.run_single_trade_validation()
            state = json.loads(executor.state_file.read_text(encoding="utf-8"))
            self.assertEqual(state["single_trade_validation"]["phase"], "failed")
            with self.assertRaisesRegex(ExecutorError, "prior single-trade"):
                executor.run_single_trade_validation()
            self.assertEqual(fake.order_requests, [])

    def test_validation_runner_rejection_stops_and_restart_refuses(self):
        fake = FakeMT5()
        fake.order_result = SimpleNamespace(retcode=fake.TRADE_RETCODE_REJECT)
        bars = breakout_bars()
        planned = datetime.fromisoformat(bars[-1]["timestamp"]) + timedelta(minutes=5)
        fake.current_bar_epoch = int(planned.replace(tzinfo=timezone.utc).timestamp())
        fake.tick.time = fake.current_bar_epoch
        config = MT5Config(login=123, server=EXPECTED_SERVER, broker_utc_offset="+02:00")
        with tempfile.TemporaryDirectory() as folder, patch.dict(
            "os.environ", {"MT5_DEMO_VOLUME": "0.01"}
        ), patch(
            "paper_trading.demo_executor.mt5_connector.initialize_connection", return_value=True
        ), patch(
            "paper_trading.demo_executor.mt5_connector.shutdown_connection"
        ), patch(
            "paper_trading.demo_executor.mt5_connector._require_connection", return_value=(fake, config)
        ), patch(
            "paper_trading.demo_executor.mt5_connector.verify_trade_permissions", return_value={"permitted": True}
        ), patch(
            "paper_trading.demo_executor.mt5_connector.verify_symbol", return_value=fake.symbol
        ), patch(
            "paper_trading.demo_executor.DemoExecutor._verify_validation_startup"
        ), patch(
            "paper_trading.mt5_price_feed.get_recent_m5_bars", return_value=bars
        ), patch(
            "paper_trading.demo_executor.DemoExecutor._time", return_value=planned
        ):
            base = Path(folder)
            executor = DemoExecutor(execution_log=base / "events.csv", state_file=base / "state.json")
            self.assertEqual(executor.run_single_trade_validation(), "rejected")
            with self.assertRaisesRegex(ExecutorError, "prior single-trade"):
                executor.run_single_trade_validation()
            self.assertEqual(len(fake.order_requests), 1)

    def test_validation_single_attempt_rejection_and_ambiguous_result(self):
        for retcode in (FakeMT5.TRADE_RETCODE_REJECT, None):
            with self.subTest(retcode=retcode), tempfile.TemporaryDirectory() as folder:
                fake = FakeMT5()
                fake.order_result = (
                    None if retcode is None else SimpleNamespace(retcode=retcode)
                )
                bars = breakout_bars()
                planned = datetime.fromisoformat(bars[-1]["timestamp"]) + timedelta(minutes=5)
                fake.current_bar_epoch = int(planned.replace(tzinfo=timezone.utc).timestamp())
                fake.tick.time = fake.current_bar_epoch
                config = MT5Config(login=123, server=EXPECTED_SERVER, broker_utc_offset="+02:00")
                base = Path(folder)
                executor = DemoExecutor(execution_log=base / "events.csv", state_file=base / "state.json")
                executor.state_file.write_text(json.dumps({
                    "processed_signal_times": [],
                    "active_position": None,
                    "single_trade_validation": {"phase": "armed", **executor._validation_descriptor()},
                }), encoding="utf-8")
                with patch.dict("os.environ", {"MT5_DEMO_VOLUME": "0.01"}), patch(
                    "paper_trading.demo_executor.mt5_connector._require_connection",
                    return_value=(fake, config),
                ), patch(
                    "paper_trading.demo_executor.mt5_connector.verify_trade_permissions",
                    return_value={"permitted": True},
                ), patch(
                    "paper_trading.demo_executor.mt5_connector.verify_symbol",
                    return_value=fake.symbol,
                ), patch(
                    "paper_trading.mt5_price_feed.get_recent_m5_bars", return_value=bars
                ), patch(
                    "paper_trading.demo_executor.DemoExecutor._time",
                    return_value=planned,
                ):
                    if retcode is None:
                        with self.assertRaises(ExecutorError):
                            executor._process_once(validation_run=True)
                    else:
                        executor._process_once(validation_run=True)
                    with self.assertRaises(ExecutorError):
                        executor._process_once(validation_run=True)
                    with self.assertRaises(ExecutorError):
                        executor.process_once()
                    self.assertEqual(len(fake.order_requests), 1)

    def test_validation_fill_disarms_entries_and_monitors_position(self):
        fake = FakeMT5()
        bars = breakout_bars()
        planned = datetime.fromisoformat(bars[-1]["timestamp"]) + timedelta(minutes=5)
        fake.current_bar_epoch = int(planned.replace(tzinfo=timezone.utc).timestamp())
        fake.tick.time = fake.current_bar_epoch
        fake.planned_epoch_ms = fake.current_bar_epoch * 1000
        config = MT5Config(login=123, server=EXPECTED_SERVER, broker_utc_offset="+02:00")
        with tempfile.TemporaryDirectory() as folder, patch.dict(
            "os.environ", {"MT5_DEMO_VOLUME": "0.01"}
        ), patch(
            "paper_trading.demo_executor.mt5_connector._require_connection", return_value=(fake, config)
        ), patch(
            "paper_trading.demo_executor.mt5_connector.verify_trade_permissions", return_value={"permitted": True}
        ), patch(
            "paper_trading.demo_executor.mt5_connector.verify_symbol", return_value=fake.symbol
        ), patch(
            "paper_trading.mt5_price_feed.get_recent_m5_bars", return_value=bars
        ), patch(
            "paper_trading.demo_executor.DemoExecutor._time", return_value=planned
        ):
            base = Path(folder)
            executor = DemoExecutor(execution_log=base / "events.csv", state_file=base / "state.json",
                                    trade_log=base / "DEMO_TRADING_LOG.csv",
                                    metrics_file=base / "DEMO_METRICS.json", gate_file=base / "gate.md")
            executor.state_file.write_text(json.dumps({
                "processed_signal_times": [], "active_position": None,
                "single_trade_validation": {"phase": "armed", **executor._validation_descriptor()},
            }), encoding="utf-8")
            executor._process_once(validation_run=True)
            self.assertEqual(json.loads(executor.state_file.read_text())["single_trade_validation"]["phase"], "monitoring")
            executor._process_once(validation_run=True)
            with self.assertRaises(ExecutorError):
                executor.process_once()
            self.assertEqual(len(fake.order_requests), 1)

            active = json.loads(executor.state_file.read_text())["active_position"]
            fake.position = None
            fake.position_history = [
                SimpleNamespace(entry=0, type=0, volume=0.01, price=1.10012,
                                time_msc=fake.planned_epoch_ms, position_id=777, symbol="EURUSD",
                                magic=26111601, order=666, profit=0, commission=-0.1, swap=0, fee=0),
                SimpleNamespace(entry=1, type=1, volume=0.01, price=1.10212,
                                time_msc=fake.planned_epoch_ms + 300000, position_id=777, symbol="EURUSD",
                                profit=2, commission=-0.1, swap=0, fee=0, reason=5),
            ]
            executor._process_once(validation_run=True)
            self.assertEqual(len(read_trade_log(executor._validation_paths()["trade_log"])), 1)
            self.assertEqual(active["volume"], 0.01)
            self.assertEqual(json.loads(executor.state_file.read_text())["single_trade_validation"]["phase"], "completed")
            with self.assertRaises(ExecutorError):
                executor._process_once(validation_run=True)
            self.assertEqual(len(fake.order_requests), 1)

    def test_demo_account_validation_and_live_unknown_server_rejection(self):
        fake = FakeMT5()
        with patch(
            "paper_trading.demo_executor.mt5_connector.verify_trade_permissions",
            return_value={"permitted": True},
        ):
            self.assertIs(fake.account, validate_demo_account(fake))
            with self.assertRaisesRegex(ExecutorError, "login mismatch"):
                validate_demo_account(fake, expected_login=999)
            fake.account.trade_mode = fake.ACCOUNT_TRADE_MODE_REAL
            with self.assertRaisesRegex(ExecutorError, "not demo"):
                validate_demo_account(fake)
            fake.account.trade_mode = None
            with self.assertRaisesRegex(ExecutorError, "unknown"):
                validate_demo_account(fake)
            fake.account.trade_mode = fake.ACCOUNT_TRADE_MODE_DEMO
            fake.account.server = "Unexpected-Live"
            with self.assertRaisesRegex(ExecutorError, "server mismatch"):
                validate_demo_account(fake)

    def test_signal_submits_one_market_order_and_persists_fill_and_protection(self):
        fake = FakeMT5()
        bars = breakout_bars()
        planned = datetime.fromisoformat(bars[-1]["timestamp"]) + timedelta(minutes=5)
        fake.current_bar_epoch = int(datetime(
            planned.year, planned.month, planned.day,
            planned.hour, planned.minute, tzinfo=timezone.utc,
        ).timestamp())
        fake.planned_epoch_ms = fake.current_bar_epoch * 1000
        config = MT5Config(login=123, server=EXPECTED_SERVER, broker_utc_offset="+02:00")
        with tempfile.TemporaryDirectory() as folder, patch.dict(
            "os.environ", {"MT5_DEMO_VOLUME": "0.10"}, clear=False
        ), patch(
            "paper_trading.demo_executor.mt5_connector._require_connection",
            return_value=(fake, config),
        ), patch(
            "paper_trading.demo_executor.mt5_connector.verify_trade_permissions",
            return_value={"permitted": True},
        ), patch(
            "paper_trading.demo_executor.mt5_connector.verify_symbol",
            return_value=fake.symbol,
        ), patch(
            "paper_trading.mt5_price_feed.get_recent_m5_bars",
            return_value=bars,
        ), patch(
            "paper_trading.demo_executor.DemoExecutor._time",
            return_value=planned + timedelta(milliseconds=10),
        ):
            base = Path(folder)
            executor = DemoExecutor(
                execution_log=base / "events.csv",
                state_file=base / "state.json",
                trade_log=base / "trades.csv",
                metrics_file=base / "metrics.json",
                gate_file=base / "gate.md",
            )
            executor.gate_file.write_text(
                "# Gate\n- **Demo Trades Completed:** **0 / 100**\n"
                "- **V2 Eligibility:** **BLOCKED**\n"
                "- **Reason:** **100 demo trades not yet completed.**\n",
                encoding="utf-8",
            )
            executor.process_once()
            executor.process_once()

            self.assertEqual(len(fake.order_requests), 1)
            order = fake.order_requests[0]
            self.assertEqual(order["action"], fake.TRADE_ACTION_DEAL)
            self.assertEqual(order["type"], fake.ORDER_TYPE_BUY)
            self.assertEqual(order["sl"], 1.09912)
            self.assertEqual(order["tp"], 1.10212)
            state_text = (base / "state.json").read_text(encoding="utf-8")
            self.assertIn('"phase": "open"', state_text)
            events = read_events(base / "events.csv")
            self.assertEqual(tuple(events[0].keys()), EXECUTION_FIELDS)
            self.assertTrue(
                {"signal_detected", "order_submission_started", "order_submitted", "order_filled",
                 "stop_attached", "take_profit_attached"}.issubset(
                    {event["event"] for event in events}
                )
            )

    def test_single_position_rule_suppresses_signal_submission(self):
        fake = FakeMT5()
        fake.position = SimpleNamespace(identifier=11, ticket=11, magic=1, symbol="EURUSD")
        bars = breakout_bars()
        planned = datetime.fromisoformat(bars[-1]["timestamp"]) + timedelta(minutes=5)
        config = MT5Config(login=123, server=EXPECTED_SERVER, broker_utc_offset="+02:00")
        with tempfile.TemporaryDirectory() as folder, patch(
            "paper_trading.demo_executor.mt5_connector._require_connection",
            return_value=(fake, config),
        ), patch(
            "paper_trading.demo_executor.mt5_connector.verify_trade_permissions",
            return_value={"permitted": True},
        ), patch(
            "paper_trading.demo_executor.mt5_connector.verify_symbol",
            return_value=fake.symbol,
        ), patch(
            "paper_trading.mt5_price_feed.get_recent_m5_bars",
            return_value=bars,
        ), patch(
            "paper_trading.demo_executor.DemoExecutor._time",
            return_value=planned + timedelta(milliseconds=10),
        ):
            base = Path(folder)
            executor = DemoExecutor(
                execution_log=base / "events.csv",
                state_file=base / "state.json",
            )
            executor.process_once()
            self.assertEqual(fake.order_requests, [])
            self.assertIn(
                "signal_ignored_position_open",
                {event["event"] for event in read_events(base / "events.csv")},
            )

    def test_existing_position_with_changed_protection_stops_execution(self):
        fake = FakeMT5()
        fake.position = SimpleNamespace(
            identifier=777,
            ticket=888,
            sl=1.0990,
            tp=1.10212,
            magic=26111601,
            symbol="EURUSD",
        )
        planned = datetime(2026, 11, 16, 8, 5, tzinfo=timezone(timedelta(hours=2)))
        state = {
            "processed_signal_times": [],
            "active_position": {
                "phase": "open",
                "position_id": 777,
                "actual_stop": 1.09912,
                "actual_target": 1.10212,
            },
        }
        config = MT5Config(login=123, server=EXPECTED_SERVER, broker_utc_offset="+02:00")
        with tempfile.TemporaryDirectory() as folder, patch(
            "paper_trading.demo_executor.mt5_connector._require_connection",
            return_value=(fake, config),
        ), patch(
            "paper_trading.demo_executor.mt5_connector.verify_trade_permissions",
            return_value={"permitted": True},
        ), patch(
            "paper_trading.demo_executor.mt5_connector.verify_symbol",
            return_value=fake.symbol,
        ):
            base = Path(folder)
            executor = DemoExecutor(
                execution_log=base / "events.csv",
                state_file=base / "state.json",
            )
            executor.state_file.write_text(json.dumps(state), encoding="utf-8")
            with self.assertRaisesRegex(ExecutorError, "protection changed"):
                executor.process_once()
            self.assertEqual(fake.order_requests, [])

    def test_executor_lock_contention_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder, patch(
            "paper_trading.demo_executor.msvcrt.locking",
            side_effect=OSError("lock held"),
        ):
            executor = DemoExecutor(
                state_file=Path(folder) / "state.json",
                lock_file=Path(folder) / "executor.lock",
            )
            with self.assertRaisesRegex(ExecutorError, "another executor instance"):
                executor.process_once()

    def test_verify_only_runs_preflight_without_mt5_mutations(self):
        fake = FakeMT5()
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        m5_start = now.replace(minute=(now.minute // 5) * 5)
        fake.current_bar_epoch = int(m5_start.timestamp())
        fake.tick.time = int(now.timestamp())
        config = MT5Config(
            login=123,
            server=EXPECTED_SERVER,
            broker_utc_offset="+02:00",
        )
        with tempfile.TemporaryDirectory() as folder, patch.dict(
            "os.environ",
            {
                "MT5_BROKER_UTC_OFFSET": "+02:00",
                "MT5_DEMO_VOLUME": "0.01",
            },
            clear=False,
        ), patch(
            "paper_trading.demo_executor.mt5_connector.initialize_connection",
            return_value=True,
        ), patch(
            "paper_trading.demo_executor.mt5_connector._require_connection",
            return_value=(fake, config),
        ), patch(
            "paper_trading.demo_executor.mt5_connector.verify_trade_permissions",
            return_value={"permitted": True},
        ), patch(
            "paper_trading.demo_executor.mt5_connector.shutdown_connection",
        ) as shutdown:
            base = Path(folder)
            trade_log = base / "trades.csv"
            trade_log.write_text(
                ",".join(TRADE_FIELDS) + "\n",
                encoding="utf-8",
            )
            metrics_file = base / "metrics.json"
            metrics_file.write_text(
                json.dumps(calculate_demo_metrics([]), indent=2) + "\n",
                encoding="utf-8",
            )
            gate_file = base / "gate.md"
            gate_file.write_text(
                "# Gate\n- **Demo Trades Completed:** **0 / 100**\n"
                "- **V2 Eligibility:** **BLOCKED**\n"
                "- **Reason:** **100 demo trades not yet completed.**\n",
                encoding="utf-8",
            )
            original_metrics = metrics_file.read_bytes()
            original_gate = gate_file.read_bytes()
            executor = DemoExecutor(
                execution_log=base / "events.csv",
                state_file=base / "state.json",
                trade_log=trade_log,
                metrics_file=metrics_file,
                gate_file=gate_file,
            )
            report_path = base / "integration.md"

            self.assertTrue(
                executor.verify_only(
                    approved_volume=Decimal("0.01"),
                    report_path=report_path,
                )
            )

            self.assertEqual(fake.order_requests, [])
            self.assertIsNone(fake.position)
            self.assertFalse((base / "state.json").exists())
            self.assertFalse((base / "events.csv").exists())
            self.assertEqual(trade_log.read_text(encoding="utf-8").count("\n"), 1)
            self.assertEqual(metrics_file.read_bytes(), original_metrics)
            self.assertEqual(gate_file.read_bytes(), original_gate)
            self.assertIn("READY_FOR_DEMO_TRADE_1", report_path.read_text(encoding="utf-8"))
            shutdown.assert_called_once()

    def test_verify_only_blocks_when_explicit_runtime_configuration_is_missing(self):
        fake = FakeMT5()
        config = MT5Config(login=123, server=EXPECTED_SERVER, broker_utc_offset="+02:00")
        with tempfile.TemporaryDirectory() as folder, patch.dict(
            "os.environ",
            {"MT5_BROKER_UTC_OFFSET": "", "MT5_DEMO_VOLUME": ""},
            clear=False,
        ), patch(
            "paper_trading.demo_executor.mt5_connector.initialize_connection",
            return_value=True,
        ), patch(
            "paper_trading.demo_executor.mt5_connector._require_connection",
            return_value=(fake, config),
        ), patch(
            "paper_trading.demo_executor.mt5_connector.verify_trade_permissions",
            return_value={"permitted": True},
        ), patch(
            "paper_trading.demo_executor.mt5_connector._read_env_file",
            return_value={},
        ), patch(
            "paper_trading.demo_executor.mt5_connector.shutdown_connection",
        ):
            base = Path(folder)
            trade_log = base / "trades.csv"
            trade_log.write_text(
                "trade_id,strategy_version,account_type,account_alias,broker,symbol,timeframe,"
                "signal_bar_open_time_broker,signal_time_broker,entry_time_broker,exit_time_broker,"
                "direction,signal_close,prior_20_high,prior_20_low,intended_entry,actual_entry,"
                "stop_price,target_price,actual_exit,entry_spread_pips,exit_spread_pips,gross_pnl_pips,"
                "commission_pips,financing_pips,slippage_pips,pnl_pips,pnl_r,hold_minutes,exit_reason,"
                "order_reference,completed,rule_compliant,notes\n",
                encoding="utf-8",
            )
            metrics_file = base / "metrics.json"
            metrics_file.write_text(
                json.dumps(calculate_demo_metrics([]), indent=2) + "\n",
                encoding="utf-8",
            )
            gate_file = base / "gate.md"
            gate_file.write_text(
                "# Gate\n- **Demo Trades Completed:** **0 / 100**\n"
                "- **V2 Eligibility:** **BLOCKED**\n"
                "- **Reason:** **100 demo trades not yet completed.**\n",
                encoding="utf-8",
            )
            executor = DemoExecutor(
                execution_log=base / "events.csv",
                state_file=base / "state.json",
                trade_log=trade_log,
                metrics_file=metrics_file,
                gate_file=gate_file,
            )
            report_path = base / "integration.md"
            self.assertFalse(
                executor.verify_only(
                    approved_volume=Decimal("0.01"),
                    report_path=report_path,
                )
            )
            report = report_path.read_text(encoding="utf-8")
            self.assertIn("MT5_BROKER_UTC_OFFSET is not explicitly set", report)
            self.assertIn("MT5_DEMO_VOLUME is not configured", report)
            self.assertEqual(fake.order_requests, [])

    def test_ambiguous_submission_is_not_retried(self):
        fake = FakeMT5()
        fake.order_result = None
        bars = breakout_bars()
        planned = datetime.fromisoformat(bars[-1]["timestamp"]) + timedelta(minutes=5)
        fake.current_bar_epoch = int(datetime(
            planned.year, planned.month, planned.day,
            planned.hour, planned.minute, tzinfo=timezone.utc,
        ).timestamp())
        config = MT5Config(login=123, server=EXPECTED_SERVER, broker_utc_offset="+02:00")
        with tempfile.TemporaryDirectory() as folder, patch.dict(
            "os.environ", {"MT5_DEMO_VOLUME": "0.10"}, clear=False
        ), patch(
            "paper_trading.demo_executor.mt5_connector._require_connection",
            return_value=(fake, config),
        ), patch(
            "paper_trading.demo_executor.mt5_connector.verify_trade_permissions",
            return_value={"permitted": True},
        ), patch(
            "paper_trading.demo_executor.mt5_connector.verify_symbol",
            return_value=fake.symbol,
        ), patch(
            "paper_trading.mt5_price_feed.get_recent_m5_bars",
            return_value=bars,
        ), patch(
            "paper_trading.demo_executor.DemoExecutor._time",
            return_value=planned + timedelta(milliseconds=10),
        ):
            base = Path(folder)
            executor = DemoExecutor(
                execution_log=base / "events.csv",
                state_file=base / "state.json",
            )
            with self.assertRaisesRegex(ExecutorError, "outcome is unknown"):
                executor.process_once()
            with self.assertRaisesRegex(ExecutorError, "ambiguous"):
                executor.process_once()
            self.assertEqual(len(fake.order_requests), 1)

    def test_definitive_rejection_suppresses_duplicate_signal(self):
        fake = FakeMT5()
        fake.order_result = SimpleNamespace(retcode=fake.TRADE_RETCODE_REJECT, order=0)
        bars = breakout_bars()
        planned = datetime.fromisoformat(bars[-1]["timestamp"]) + timedelta(minutes=5)
        fake.current_bar_epoch = int(datetime(
            planned.year, planned.month, planned.day,
            planned.hour, planned.minute, tzinfo=timezone.utc,
        ).timestamp())
        config = MT5Config(login=123, server=EXPECTED_SERVER, broker_utc_offset="+02:00")
        with tempfile.TemporaryDirectory() as folder, patch.dict(
            "os.environ", {"MT5_DEMO_VOLUME": "0.10"}, clear=False
        ), patch(
            "paper_trading.demo_executor.mt5_connector._require_connection",
            return_value=(fake, config),
        ), patch(
            "paper_trading.demo_executor.mt5_connector.verify_trade_permissions",
            return_value={"permitted": True},
        ), patch(
            "paper_trading.demo_executor.mt5_connector.verify_symbol",
            return_value=fake.symbol,
        ), patch(
            "paper_trading.mt5_price_feed.get_recent_m5_bars",
            return_value=bars,
        ), patch(
            "paper_trading.demo_executor.DemoExecutor._time",
            return_value=planned + timedelta(milliseconds=10),
        ):
            base = Path(folder)
            executor = DemoExecutor(
                execution_log=base / "events.csv",
                state_file=base / "state.json",
            )
            executor.process_once()
            executor.process_once()
            self.assertEqual(len(fake.order_requests), 1)
            events = read_events(base / "events.csv")
            self.assertEqual(
                sum(event["event"] == "order_rejected" for event in events), 1
            )

    def test_reconciliation_generates_trade_accepted_by_existing_schema(self):
        planned = datetime(2026, 11, 16, 8, 5, tzinfo=timezone(timedelta(hours=2)))
        def epoch_millis(clock_time):
            return int(datetime(
                clock_time.year, clock_time.month, clock_time.day,
                clock_time.hour, clock_time.minute, tzinfo=timezone.utc,
            ).timestamp() * 1000)

        entry = SimpleNamespace(
            entry=0, type=0, volume=0.1, price=1.10012,
            time_msc=epoch_millis(planned), profit=0, commission=-2, swap=0, fee=0,
            position_id=2, symbol="EURUSD", magic=26111601, order=1,
        )
        exit_deal = SimpleNamespace(
            entry=1, type=1, volume=0.1, price=1.10212,
            time_msc=epoch_millis(planned + timedelta(minutes=5)),
            profit=20, commission=-2, swap=0, fee=0, reason=5,
            position_id=2, symbol="EURUSD",
        )
        reconciliation = {
            "signal": {
                "trade_id": "V1-DEMO-TEST",
                "symbol": "EURUSD",
                "direction": "long",
                "signal_bar_open_time_broker": "2026-11-16T08:00:00+02:00",
                "signal_close": "1.1006",
                "prior_20_high": "1.1005",
                "prior_20_low": "1.0995",
            },
            "entry_deals": [entry],
            "exit_deals": [exit_deal],
            "symbol_info": SimpleNamespace(
                trade_tick_size=0.00001, trade_tick_value=1.0
            ),
            "broker_offset": "+02:00",
            "account_alias": "ICM-DEMO",
            "intended_entry": 1.10012,
            "entry_spread_pips": 1.2,
            "planned_entry_time": planned.isoformat(),
            "submission_time": (planned + timedelta(milliseconds=5)).isoformat(),
            "fill_delay_ms": 0,
            "order_reference": "order=1;position=2",
            "entry_code": 0,
            "exit_codes": {1, 3},
            "deal_buy_type": 0,
            "deal_sell_type": 1,
            "exit_reason_codes": {5: "take_profit"},
            "expected_volume": 0.1,
            "expected_order_ticket": 1,
            "expected_magic": 26111601,
            "position_id": 2,
        }
        record = build_trade_record(**reconciliation)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "trades.csv"
            accepted = append_completed_trade(record, path)
            self.assertEqual(accepted["completed"], "true")
            self.assertEqual(accepted["rule_compliant"], "true")
            with path.open(newline="", encoding="utf-8") as file:
                self.assertEqual(len(list(csv.DictReader(file))), 1)

        entry.magic = 26111602
        with self.assertRaisesRegex(ValueError, "provenance"):
            build_trade_record(**reconciliation)
        entry.magic = 26111601
        del entry.commission
        with self.assertRaisesRegex(ValueError, "missing commission"):
            build_trade_record(**reconciliation)

    def test_reconciliation_rejects_partially_closed_volume(self):
        planned = datetime(2026, 11, 16, 8, 5, tzinfo=timezone(timedelta(hours=2)))
        def epoch_millis(clock_time):
            return int(datetime(
                clock_time.year, clock_time.month, clock_time.day,
                clock_time.hour, clock_time.minute, tzinfo=timezone.utc,
            ).timestamp() * 1000)

        entry = SimpleNamespace(
            entry=0, type=0, volume=0.1, price=1.10012,
            time_msc=epoch_millis(planned), profit=0, commission=0, swap=0, fee=0,
            position_id=2, symbol="EURUSD", magic=26111601, order=1,
        )
        partial_exit = SimpleNamespace(
            entry=1, type=1, volume=0.05, price=1.10212,
            time_msc=epoch_millis(planned + timedelta(minutes=5)),
            profit=10, commission=0, swap=0, fee=0, reason=5,
            position_id=2, symbol="EURUSD",
        )
        with self.assertRaisesRegex(ValueError, "not fully closed"):
            build_trade_record(
                signal={
                    "trade_id": "V1-DEMO-PARTIAL",
                    "symbol": "EURUSD",
                    "direction": "long",
                    "signal_bar_open_time_broker": "2026-11-16T08:00:00+02:00",
                    "signal_close": "1.1006",
                    "prior_20_high": "1.1005",
                    "prior_20_low": "1.0995",
                },
                entry_deals=[entry],
                exit_deals=[partial_exit],
                symbol_info=SimpleNamespace(
                    trade_tick_size=0.00001, trade_tick_value=1.0
                ),
                broker_offset="+02:00",
                account_alias="ICM-DEMO",
                intended_entry=1.10012,
                entry_spread_pips=1.2,
                planned_entry_time=planned.isoformat(),
                submission_time=planned.isoformat(),
                fill_delay_ms=0,
                order_reference="order=1;position=2",
                entry_code=0,
                exit_codes={1, 3},
                deal_buy_type=0,
                deal_sell_type=1,
                exit_reason_codes={5: "take_profit"},
                expected_volume=0.1,
                expected_order_ticket=1,
                expected_magic=26111601,
                position_id=2,
            )

    def test_closed_position_updates_trade_metrics_and_gate(self):
        fake = FakeMT5()
        planned = datetime(2026, 11, 16, 8, 5, tzinfo=timezone(timedelta(hours=2)))

        def epoch_millis(clock_time):
            wall_time = datetime(
                clock_time.year,
                clock_time.month,
                clock_time.day,
                clock_time.hour,
                clock_time.minute,
                tzinfo=timezone.utc,
            )
            return int(wall_time.timestamp() * 1000)

        fake.position_history = [
            SimpleNamespace(
                entry=fake.DEAL_ENTRY_IN,
                type=fake.DEAL_TYPE_BUY,
                volume=0.1,
                price=1.1001,
                time_msc=epoch_millis(planned),
                position_id=777,
                symbol="EURUSD",
                magic=26111601,
                order=666,
                profit=0,
                commission=0,
                swap=0,
                fee=0,
            ),
            SimpleNamespace(
                entry=fake.DEAL_ENTRY_OUT,
                type=fake.DEAL_TYPE_SELL,
                volume=0.1,
                price=1.1021,
                time_msc=epoch_millis(planned + timedelta(minutes=5)),
                position_id=777,
                symbol="EURUSD",
                profit=20,
                commission=0,
                swap=0,
                fee=0,
                reason=fake.DEAL_REASON_TP,
            ),
        ]
        signal = {
            "trade_id": "V1-DEMO-AUTOMATED-1",
            "symbol": "EURUSD",
            "direction": "long",
            "signal_bar_open_time_broker": "2026-11-16T08:00:00+02:00",
            "signal_close": 1.1006,
            "prior_20_high": 1.1005,
            "prior_20_low": 1.0995,
        }
        state = {
            "processed_signal_times": [signal["signal_bar_open_time_broker"]],
            "active_position": {
                "phase": "open",
                "signal": signal,
                "position_id": 777,
                "planned_entry_time_broker": planned.isoformat(),
                "submission_time_broker": planned.isoformat(),
                "requested_price": 1.1001,
                "intended_entry": 1.1001,
                "entry_spread_pips": 1.2,
                "volume": 0.1,
                "order_ticket": 666,
                "deal_ticket": 555,
                "fill_time_broker": planned.isoformat(),
                "fill_delay_ms": 0,
                "actual_stop": 1.0991,
                "actual_target": 1.1021,
            },
        }
        config = MT5Config(login=123, server=EXPECTED_SERVER, broker_utc_offset="+02:00")
        with tempfile.TemporaryDirectory() as folder, patch(
            "paper_trading.demo_executor.mt5_connector._require_connection",
            return_value=(fake, config),
        ), patch(
            "paper_trading.demo_executor.mt5_connector.verify_trade_permissions",
            return_value={"permitted": True},
        ), patch(
            "paper_trading.demo_executor.mt5_connector.verify_symbol",
            return_value=fake.symbol,
        ), patch(
            "paper_trading.demo_executor.DemoExecutor._time",
            return_value=planned + timedelta(minutes=10),
        ):
            base = Path(folder)
            executor = DemoExecutor(
                execution_log=base / "events.csv",
                state_file=base / "state.json",
                trade_log=base / "trades.csv",
                metrics_file=base / "metrics.json",
                gate_file=base / "gate.md",
            )
            executor.state_file.write_text(json.dumps(state), encoding="utf-8")
            executor.gate_file.write_text(
                "# Gate\n- **Demo Trades Completed:** **0 / 100**\n"
                "- **V2 Eligibility:** **BLOCKED**\n"
                "- **Reason:** **100 demo trades not yet completed.**\n",
                encoding="utf-8",
            )
            executor._process_once()

            trades = read_trade_log(executor.trade_log)
            self.assertEqual(len(trades), 1)
            self.assertEqual(trades[0]["rule_compliant"], "true")
            metrics = json.loads(executor.metrics_file.read_text(encoding="utf-8"))
            self.assertEqual(metrics["eligible_trade_count"], 1)
            gate = executor.gate_file.read_text(encoding="utf-8")
            self.assertIn("**1 / 100**", gate)
            self.assertIn("**99 eligible demo trades remain.**", gate)
            saved = json.loads(executor.state_file.read_text(encoding="utf-8"))
            self.assertIsNone(saved["active_position"])


if __name__ == "__main__":
    unittest.main()
