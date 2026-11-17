import csv
import tempfile
import unittest
from pathlib import Path

from paper_trading.check_gate import get_gate_status
from paper_trading.demo_trade_utils import TRADE_FIELDS, validate_trade
from paper_trading.generate_demo_metrics import calculate_demo_metrics
from paper_trading.generate_demo_review import build_report
from paper_trading.trade_recorder import record_trade


def demo_trade(
    trade_id="V1-DEMO-000001",
    pnl=20,
    compliant=True,
    exit_time="2026-11-02T08:10:00+02:00",
):
    return {
        "trade_id": trade_id,
        "strategy_version": "Breakout Scalping V1",
        "account_type": "DEMO",
        "account_alias": "DEMO-TEST",
        "broker": "Test Broker",
        "symbol": "EURUSD",
        "timeframe": "M5",
        "signal_bar_open_time_broker": "2026-11-02T08:00:00+02:00",
        "signal_time_broker": "2026-11-02T08:05:00+02:00",
        "entry_time_broker": "2026-11-02T08:05:00+02:00",
        "exit_time_broker": exit_time,
        "direction": "long",
        "signal_close": "1.10010",
        "prior_20_high": "1.10000",
        "prior_20_low": "1.09900",
        "intended_entry": "1.10000",
        "actual_entry": "1.10000",
        "stop_price": "1.09900",
        "target_price": "1.10200",
        "actual_exit": "1.10200",
        "entry_spread_pips": "1.0",
        "exit_spread_pips": "0.9",
        "gross_pnl_pips": str(pnl),
        "commission_pips": "0",
        "financing_pips": "0",
        "slippage_pips": "0",
        "pnl_pips": str(pnl),
        "pnl_r": str(round(pnl / 10, 4)),
        "hold_minutes": "5",
        "exit_reason": "take_profit",
        "order_reference": f"order-{trade_id}",
        "completed": "true",
        "rule_compliant": str(compliant).lower(),
        "notes": "",
    }


class DemoTradeToolsTests(unittest.TestCase):
    def test_recorder_writes_complete_header_and_trade(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "demo.csv"
            recorded = record_trade(demo_trade(), path)
            self.assertEqual(recorded["trade_id"], "V1-DEMO-000001")
            with path.open(newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                self.assertEqual(tuple(reader.fieldnames), TRADE_FIELDS)
                rows = list(reader)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["completed"], "true")

    def test_recorder_rejects_duplicate_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "demo.csv"
            record_trade(demo_trade(), path)
            with self.assertRaisesRegex(ValueError, "already exists"):
                record_trade(demo_trade(), path)

    def test_validator_rejects_missing_timestamp_price_direction_and_incomplete(self):
        cases = [
            ("entry_time_broker", "", "entry_time_broker is missing"),
            ("actual_entry", "0", "actual_entry must be a positive price"),
            ("direction", "sideways", "direction must be long or short"),
            ("completed", "false", "incomplete trades cannot be recorded"),
        ]
        for field, value, message in cases:
            with self.subTest(field=field):
                trade = demo_trade()
                trade[field] = value
                with self.assertRaisesRegex(ValueError, message):
                    validate_trade(trade)

    def test_validator_requires_explicit_offset_and_rejects_live_account(self):
        trade = demo_trade()
        trade["signal_time_broker"] = "2026-11-02T08:05:00"
        with self.assertRaisesRegex(ValueError, "explicit broker/source offset"):
            validate_trade(trade)
        trade = demo_trade()
        trade["account_type"] = "LIVE"
        with self.assertRaisesRegex(ValueError, "must be DEMO"):
            validate_trade(trade)

    def test_metrics_use_only_rule_compliant_trades(self):
        trades = [
            validate_trade(demo_trade("A", 20)),
            validate_trade(demo_trade("B", -10)),
            validate_trade(demo_trade("C", 5)),
            validate_trade(demo_trade("D", 100, compliant=False)),
        ]
        result = calculate_demo_metrics(trades)
        self.assertEqual(result["eligible_trade_count"], 3)
        self.assertEqual(result["excluded_noncompliant_trade_count"], 1)
        metrics = result["metrics"]
        self.assertEqual(metrics["trade_count"], 3)
        self.assertEqual(metrics["win_rate"], 66.67)
        self.assertEqual(metrics["profit_factor"], 2.5)
        self.assertEqual(metrics["expectancy"], 5)
        self.assertEqual(metrics["net_profit"], 15)
        self.assertEqual(metrics["max_drawdown"], 10)
        self.assertEqual(metrics["average_winner"], 12.5)
        self.assertEqual(metrics["average_loser"], -10)
        self.assertEqual(metrics["average_hold_time"], 5)

    def test_gate_requires_100_unique_compliant_demo_trades(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "demo.csv"
            for index in range(99):
                trade = demo_trade(f"V1-DEMO-{index:06d}")
                record_trade(trade, path)
            self.assertEqual(get_gate_status(path)["eligibility"], "BLOCKED")
            record_trade(demo_trade("V1-DEMO-000099"), path)
            status = get_gate_status(path)
        self.assertEqual(status["completed_trades"], 100)
        self.assertEqual(status["eligibility"], "READY_FOR_V2_REVIEW")

    def test_weekly_review_is_descriptive_and_lists_drawdown_and_changes(self):
        current = validate_trade(demo_trade("WEEK-A", 20))
        loss = demo_trade("WEEK-B", -10, exit_time="2026-11-02T08:20:00+02:00")
        loss["actual_exit"] = "1.09900"
        loss["hold_minutes"] = "15"
        loss["exit_reason"] = "stop_loss"
        report = build_report([current, validate_trade(loss)])
        self.assertIn("Trade summary", report)
        self.assertIn("Best trades", report)
        self.assertIn("Worst trades", report)
        self.assertIn("Drawdown events", report)
        self.assertIn("Metric changes", report)
        self.assertIn("Lessons observed", report)
        self.assertIn("No strategy recommendation is made.", report)

    def test_empty_weekly_report_is_well_formed(self):
        report = build_report([])
        self.assertIn("Trade count: 0", report)
        self.assertIn("No eligible completed demo trades", report)


if __name__ == "__main__":
    unittest.main()
