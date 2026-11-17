import csv
import tempfile
import unittest
from pathlib import Path

from paper_trading.demo_trade_utils import TRADE_FIELDS
from paper_trading.manual_trade_capture import (
    append_completed_trade,
    read_trade_import,
)


def manual_trade(trade_id="V1-DEMO-MANUAL-000001"):
    return {
        "trade_id": trade_id,
        "strategy_version": "Breakout Scalping V1",
        "account_type": "DEMO",
        "account_alias": "ICM-DEMO",
        "broker": "IC Markets MT5",
        "symbol": "EURUSD",
        "timeframe": "M5",
        "signal_bar_open_time_broker": "2026-11-02T08:00:00+02:00",
        "signal_time_broker": "2026-11-02T08:05:00+02:00",
        "entry_time_broker": "2026-11-02T08:05:00+02:00",
        "exit_time_broker": "2026-11-02T08:10:00+02:00",
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
        "gross_pnl_pips": "20",
        "commission_pips": "0",
        "financing_pips": "0",
        "slippage_pips": "0",
        "pnl_pips": "20",
        "pnl_r": "2",
        "hold_minutes": "5",
        "exit_reason": "take_profit",
        "order_reference": "mt5-position-1001",
        "completed": "true",
        "rule_compliant": "true",
        "notes": "Reconciled against retained MT5 demo history export.",
    }


class ManualTradeCaptureTests(unittest.TestCase):
    def test_valid_completed_trade_is_accepted_and_appended(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "DEMO_TRADING_LOG.csv"
            accepted = append_completed_trade(manual_trade(), path)
            self.assertEqual(accepted["trade_id"], "V1-DEMO-MANUAL-000001")
            with path.open("r", newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                self.assertEqual(tuple(reader.fieldnames or ()), TRADE_FIELDS)
                rows = list(reader)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["completed"], "true")

    def test_duplicate_trade_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "DEMO_TRADING_LOG.csv"
            append_completed_trade(manual_trade(), path)
            with self.assertRaisesRegex(ValueError, "already exists"):
                append_completed_trade(manual_trade(), path)

    def test_invalid_timestamps_are_rejected(self):
        cases = (
            ("entry_time_broker", "2026-11-02T08:05:00"),
            ("exit_time_broker", "not-a-timestamp"),
            ("signal_time_broker", "2026-11-02T08:06:00+02:00"),
        )
        for field, value in cases:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp_dir:
                trade = manual_trade()
                trade[field] = value
                with self.assertRaises(ValueError):
                    append_completed_trade(trade, Path(temp_dir) / "trades.csv")

    def test_explicit_offset_change_keeps_trade_hold_duration_elapsed_time(self):
        trade = manual_trade()
        trade["signal_bar_open_time_broker"] = "2026-03-29T01:50:00+02:00"
        trade["signal_time_broker"] = "2026-03-29T01:55:00+02:00"
        trade["entry_time_broker"] = "2026-03-29T03:00:00+03:00"
        trade["exit_time_broker"] = "2026-03-29T03:05:00+03:00"
        with tempfile.TemporaryDirectory() as temp_dir:
            accepted = append_completed_trade(
                trade, Path(temp_dir) / "trades.csv"
            )
        self.assertEqual(accepted["hold_minutes"], "5")

    def test_incomplete_or_missing_field_trade_is_rejected(self):
        cases = (("completed", "false"), ("actual_exit", ""))
        for field, value in cases:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp_dir:
                trade = manual_trade()
                trade[field] = value
                with self.assertRaises(ValueError):
                    append_completed_trade(trade, Path(temp_dir) / "trades.csv")

    def test_existing_log_must_have_exact_schema(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "trades.csv"
            path.write_text("trade_id,completed\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "exactly match"):
                append_completed_trade(manual_trade(), path)

    def test_reads_exactly_one_template_shaped_csv_row(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "trade_import.csv"
            with path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=TRADE_FIELDS)
                writer.writeheader()
                writer.writerow(manual_trade())
            loaded = read_trade_import(path)
            self.assertEqual(loaded, manual_trade())

    def test_import_csv_rejects_multiple_rows_and_wrong_schema(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "trade_import.csv"
            with path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=TRADE_FIELDS)
                writer.writeheader()
                writer.writerow(manual_trade())
                writer.writerow(manual_trade("V1-DEMO-MANUAL-000002"))
            with self.assertRaisesRegex(ValueError, "exactly one"):
                read_trade_import(path)

            path.write_text("trade_id,completed\nA,true\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "schema must exactly match"):
                read_trade_import(path)


if __name__ == "__main__":
    unittest.main()
