import unittest
from datetime import datetime, timedelta, timezone
import csv
import tempfile
from pathlib import Path

from scripts.backtest import Bar
from scripts.generate_weekly_review import _read_trades, build_report


class WeeklyReviewTests(unittest.TestCase):
    def test_report_contains_requested_sections_and_honest_spread_limit(self):
        start = datetime(2025, 1, 6, 8, 0, tzinfo=timezone.utc)
        bars = [
            Bar(start + timedelta(minutes=5 * index), 1.1, 1.101, 1.099, 1.1)
            for index in range(3)
        ]
        trades = [
            {
                "direction": "long",
                "entry_time": start,
                "exit_time": start + timedelta(minutes=5),
                "entry_price": 1.1,
                "exit_price": 1.102,
                "exit_reason": "take_profit",
                "pnl_pips": 20.0,
                "pnl_r": 2.0,
                "hold_minutes": 5.0,
            },
            {
                "direction": "short",
                "entry_time": start + timedelta(minutes=5),
                "exit_time": start + timedelta(minutes=10),
                "entry_price": 1.1,
                "exit_price": 1.101,
                "exit_reason": "stop_loss",
                "pnl_pips": -10.0,
                "pnl_r": -1.0,
                "hold_minutes": 5.0,
            },
        ]
        report = build_report(bars, trades)
        for expected in (
            "Best session",
            "Worst session",
            "Largest winners",
            "Largest losers",
            "Spread analysis",
            "Volatility analysis",
            "Drawdown event",
            "Lesson:",
            "flat 1.0 pip",
        ):
            self.assertIn(expected, report)

    def test_demo_csv_counts_only_completed_trades_and_reads_actual_spreads(self):
        fields = [
            "signal_time_broker",
            "entry_time_broker",
            "exit_time_broker",
            "direction",
            "actual_entry",
            "actual_exit",
            "exit_reason",
            "entry_spread_pips",
            "exit_spread_pips",
            "pnl_pips",
            "pnl_r",
            "hold_minutes",
            "completed",
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "demo.csv"
            with path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=fields)
                writer.writeheader()
                base = {
                    "signal_time_broker": "2025-01-06T08:00:00+02:00",
                    "entry_time_broker": "2025-01-06T08:05:00+02:00",
                    "exit_time_broker": "2025-01-06T08:10:00+02:00",
                    "direction": "long",
                    "actual_entry": "1.1001",
                    "actual_exit": "1.1020",
                    "exit_reason": "take_profit",
                    "entry_spread_pips": "1.2",
                    "exit_spread_pips": "0.9",
                    "pnl_pips": "19",
                    "pnl_r": "1.9",
                    "hold_minutes": "5",
                }
                writer.writerow({**base, "completed": "false"})
                writer.writerow({**base, "completed": "true"})
            trades = _read_trades(path)

        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0]["entry_spread_pips"], 1.2)
        self.assertEqual(trades[0]["exit_spread_pips"], 0.9)
        bars = [
            Bar(
                datetime(2025, 1, 6, 8, 0, tzinfo=timezone.utc),
                1.1,
                1.101,
                1.099,
                1.1,
            )
        ]
        report = build_report(bars, trades)
        self.assertIn("observed entry spread avg 1.20 pips", report)


if __name__ == "__main__":
    unittest.main()
