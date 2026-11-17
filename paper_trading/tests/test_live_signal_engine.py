import csv
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from paper_trading.live_signal_engine import (
    evaluate_v1_signal,
    generate_v1_signals,
)
from paper_trading.live_signal_monitor import monitor_signals
from scripts.backtest import load_bars, run_backtest


def bar(index, close=1.1000, high=1.1005, low=1.0995):
    return {
        "timestamp": (
            datetime(2025, 1, 6, tzinfo=timezone.utc) + timedelta(minutes=5 * index)
        ).isoformat(),
        "open": 1.1000,
        "high": high,
        "low": low,
        "close": close,
    }


class LiveSignalEngineTests(unittest.TestCase):
    def test_detects_long_and_short_from_prior_twenty_bars(self):
        baseline = [bar(index) for index in range(20)]
        long_signal = evaluate_v1_signal(baseline + [bar(20, close=1.1006, high=1.1007)])
        self.assertEqual(long_signal.signal_type, "LONG")
        self.assertEqual(long_signal.breakout_level, 1.1005)
        self.assertEqual(long_signal.current_price, 1.1006)
        self.assertIsNone(long_signal.stop_price)
        self.assertIsNone(long_signal.target_price)

        short_signal = evaluate_v1_signal(
            baseline + [bar(20, close=1.0994, low=1.0993)]
        )
        self.assertEqual(short_signal.signal_type, "SHORT")
        self.assertEqual(short_signal.breakout_level, 1.0995)

    def test_strict_boundary_and_insufficient_history_produce_no_signal(self):
        baseline = [bar(index) for index in range(20)]
        equal_high = evaluate_v1_signal(
            baseline + [bar(20, close=1.1005, high=1.1006)]
        )
        self.assertEqual(equal_high.signal_type, "NO SIGNAL")
        self.assertIsNone(equal_high.breakout_level)

        insufficient = evaluate_v1_signal(baseline[:20])
        self.assertEqual(insufficient.signal_type, "NO SIGNAL")
        self.assertIn("Need 20 prior", insufficient.notes)

    def test_rejects_bad_bars_and_non_chronological_data(self):
        with self.assertRaisesRegex(ValueError, "at least one"):
            evaluate_v1_signal([])
        bad_time = bar(0)
        bad_time["timestamp"] = "2025-01-06T00:01:00Z"
        with self.assertRaisesRegex(ValueError, "M5 boundary"):
            evaluate_v1_signal([bad_time])

        inconsistent = bar(0)
        inconsistent["high"] = 1.0
        with self.assertRaisesRegex(ValueError, "inconsistent OHLC"):
            evaluate_v1_signal([inconsistent])

        duplicate = [bar(0), bar(0)]
        with self.assertRaisesRegex(ValueError, "strictly chronological"):
            evaluate_v1_signal(duplicate)

    def test_accepts_broker_time_without_changing_breakout_result(self):
        baseline = [bar(index) for index in range(20)]
        for item in baseline:
            item["timestamp"] = item["timestamp"].replace("+00:00", "+02:00")
        breakout = bar(20, close=1.1006, high=1.1007)
        breakout["timestamp"] = breakout["timestamp"].replace("+00:00", "+02:00")
        signal = evaluate_v1_signal(baseline + [breakout])
        self.assertEqual(signal.signal_type, "LONG")
        self.assertEqual(signal.timestamp, "2025-01-06T01:40:00+02:00")

    def test_historical_2025_breakouts_match_independent_frozen_rule(self):
        data_path = Path(__file__).resolve().parents[2] / "data" / "eurusd_m5_2025.csv"
        with data_path.open("r", newline="", encoding="utf-8-sig") as file:
            bars = load_bars(file)

        actual = generate_v1_signals(bars)
        expected = []
        for index in range(20, len(bars)):
            previous = bars[index - 20 : index]
            prior_high = max(item.high for item in previous)
            prior_low = min(item.low for item in previous)
            current = bars[index]
            if current.close > prior_high:
                expected.append(
                    (
                        current.timestamp.isoformat(),
                        "LONG",
                        prior_high,
                        current.close,
                    )
                )
            elif current.close < prior_low:
                expected.append(
                    (
                        current.timestamp.isoformat(),
                        "SHORT",
                        prior_low,
                        current.close,
                    )
                )

        actual_values = [
            (item.timestamp, item.signal_type, item.breakout_level, item.current_price)
            for item in actual
        ]
        self.assertEqual(actual_values, expected)
        self.assertEqual(len(actual), 8733)

        historical_trades = run_backtest(bars)
        executed_signal_events = {
            (trade.signal_time, trade.direction.upper()) for trade in historical_trades
        }
        candidate_events = {(item.timestamp, item.signal_type) for item in actual}
        self.assertEqual(len(historical_trades), 2260)
        self.assertTrue(executed_signal_events.issubset(candidate_events))
        self.assertEqual(len(candidate_events - executed_signal_events), 6473)

    def test_monitor_logs_new_bar_once_and_always_shuts_down(self):
        bars = [bar(index) for index in range(21)]
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "LIVE_SIGNAL_LOG.csv"
            with (
                patch("paper_trading.live_signal_monitor.mt5_connector.initialize_connection"),
                patch("paper_trading.live_signal_monitor.mt5_connector.shutdown_connection") as shutdown,
                patch(
                    "paper_trading.live_signal_monitor.get_recent_m5_bars",
                    return_value=bars,
                ),
                patch("paper_trading.live_signal_monitor.time.sleep"),
            ):
                monitor_signals(
                    poll_interval_seconds=0.1,
                    log_path=log_path,
                    max_polls=2,
                )

            with log_path.open("r", newline="", encoding="utf-8") as file:
                rows = list(csv.DictReader(file))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["signal_type"], "NO SIGNAL")
            self.assertEqual(
                tuple(rows[0].keys()),
                (
                    "timestamp",
                    "signal_type",
                    "breakout_level",
                    "current_price",
                    "stop_price",
                    "target_price",
                    "notes",
                ),
            )
            shutdown.assert_called_once()


if __name__ == "__main__":
    unittest.main()
