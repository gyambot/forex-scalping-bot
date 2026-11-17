import csv
import io
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.backtest import (
    Bar,
    Trade,
    calculate_metrics,
    load_bars,
    run_backtest,
    write_results,
)
from paper_trading.broker_time import parse_broker_timezone


def bar(index, open_price, high, low, close):
    return Bar(
        datetime(2025, 1, 6, tzinfo=timezone.utc) + timedelta(minutes=5 * index),
        open_price,
        high,
        low,
        close,
    )


class BacktestTests(unittest.TestCase):
    def test_loads_valid_offset_aware_m5_csv(self):
        bars = load_bars(
            io.StringIO(
                "timestamp,open,high,low,close\n"
                "2025-01-06T08:00:00Z,1.03000,1.03020,1.02990,1.03010\n"
            )
        )
        self.assertEqual(len(bars), 1)

    def test_accepts_broker_time_offset_and_rejects_naive_timestamp(self):
        broker_bars = load_bars(
            io.StringIO(
                "timestamp,open,high,low,close\n"
                "2025-01-06T08:00:00+02:00,1.03000,1.03020,1.02990,1.03010\n"
            )
        )
        self.assertEqual(broker_bars[0].timestamp.utcoffset(), timedelta(hours=2))
        with self.assertRaisesRegex(ValueError, "explicit broker/source offset"):
            load_bars(
                io.StringIO(
                    "timestamp,open,high,low,close\n"
                    "2025-01-06T08:00:00,1.03000,1.03020,1.02990,1.03010\n"
                )
            )

    def test_rejects_extra_csv_fields(self):
        with self.assertRaisesRegex(ValueError, "too many CSV fields"):
            load_bars(
                io.StringIO(
                    "timestamp,open,high,low,close\n"
                    "2025-01-06T08:00:00Z,1.03000,1.03020,1.02990,1.03010,extra\n"
                )
            )

    def test_rejects_missing_timestamp(self):
        with self.assertRaisesRegex(ValueError, "timestamp is missing"):
            load_bars(
                io.StringIO(
                    "timestamp,open,high,low,close\n"
                    ",1.03000,1.03020,1.02990,1.03010\n"
                )
            )

    def test_breakout_enters_next_bar_and_takes_two_r_target(self):
        bars = [bar(i, 1.1000, 1.1005, 1.0995, 1.1000) for i in range(20)]
        bars.append(bar(20, 1.1000, 1.1007, 1.0999, 1.1006))
        bars.append(bar(21, 1.1000, 1.1025, 1.0999, 1.1020))
        trades = run_backtest(bars)
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].direction, "long")
        self.assertEqual(trades[0].entry_time, bars[21].timestamp.isoformat())
        self.assertEqual(trades[0].exit_reason, "take_profit")
        self.assertAlmostEqual(trades[0].pnl_pips, 20.0)
        self.assertAlmostEqual(trades[0].pnl_r, 2.0)

    def test_broker_offset_preserves_v1_signals_and_trade_metrics(self):
        utc_bars = [bar(i, 1.1000, 1.1005, 1.0995, 1.1000) for i in range(20)]
        utc_bars.extend(
            [
                bar(20, 1.1000, 1.1007, 1.0999, 1.1006),
                bar(21, 1.1000, 1.1025, 1.0999, 1.1020),
            ]
        )
        broker_tz = parse_broker_timezone("+02:00")
        broker_bars = [
            Bar(
                item.timestamp.astimezone(broker_tz),
                item.open,
                item.high,
                item.low,
                item.close,
            )
            for item in utc_bars
        ]

        utc_trades = run_backtest(utc_bars)
        broker_trades = run_backtest(broker_bars)
        self.assertEqual(len(utc_trades), len(broker_trades))
        self.assertEqual(
            [
                (trade.direction, trade.entry_price, trade.stop_price, trade.target_price,
                 trade.exit_price, trade.pnl_pips, trade.pnl_r, trade.hold_minutes)
                for trade in utc_trades
            ],
            [
                (trade.direction, trade.entry_price, trade.stop_price, trade.target_price,
                 trade.exit_price, trade.pnl_pips, trade.pnl_r, trade.hold_minutes)
                for trade in broker_trades
            ],
        )
        self.assertTrue(broker_trades[0].entry_time.endswith("+02:00"))

    def test_broker_offset_change_preserves_next_bar_order_at_dst_boundary(self):
        bars = [
            Bar(
                datetime(2026, 3, 29, 0, 15, tzinfo=parse_broker_timezone("+02:00"))
                + timedelta(minutes=5 * index),
                1.1000,
                1.1005,
                1.0995,
                1.1000,
            )
            for index in range(20)
        ]
        bars.extend(
            [
                Bar(datetime(2026, 3, 29, 1, 55, tzinfo=parse_broker_timezone("+02:00")),
                    1.1000, 1.1007, 1.0999, 1.1006),
                Bar(datetime(2026, 3, 29, 3, 0, tzinfo=parse_broker_timezone("+03:00")),
                    1.1000, 1.1025, 1.0999, 1.1000),
                Bar(datetime(2026, 3, 29, 3, 5, tzinfo=parse_broker_timezone("+03:00")),
                    1.1000, 1.1005, 1.0995, 1.1000),
            ]
        )
        trades = run_backtest(bars)
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].entry_time, "2026-03-29T03:00:00+03:00")
        self.assertEqual(trades[0].exit_time, "2026-03-29T03:05:00+03:00")
        self.assertEqual(trades[0].exit_reason, "take_profit")

    def test_same_bar_stop_and_target_assumes_stop_first(self):
        bars = [bar(i, 1.1000, 1.1005, 1.0995, 1.1000) for i in range(20)]
        bars.append(bar(20, 1.1000, 1.1007, 1.0999, 1.1006))
        bars.append(bar(21, 1.1000, 1.1030, 1.0990, 1.1010))
        trades = run_backtest(bars)
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].exit_reason, "stop_loss")
        self.assertAlmostEqual(trades[0].pnl_r, -1.0)

    def test_metrics_and_output_files_include_required_fields(self):
        bars = [bar(0, 1.1, 1.1001, 1.0999, 1.1)]
        trade = Trade(
            direction="long",
            signal_time="2025-01-06T00:00:00Z",
            entry_time="2025-01-06T00:05:00Z",
            exit_time="2025-01-06T00:10:00Z",
            entry_price=1.1,
            exit_price=1.102,
            stop_price=1.099,
            target_price=1.102,
            exit_reason="take_profit",
            pnl_pips=20.0,
            pnl_r=2.0,
            bars_held=1,
            hold_minutes=5,
        )
        metrics = calculate_metrics([trade], bars)
        self.assertEqual(metrics["trade_count"], 1)
        self.assertEqual(metrics["profit_factor"], None)
        self.assertEqual(metrics["expectancy_r"], 2.0)
        self.assertTrue(
            {
                "net_profit_pips",
                "profit_factor",
                "expectancy_pips",
                "expectancy_r",
                "win_rate_pct",
                "max_drawdown_pips",
                "avg_trade_pips",
                "avg_hold_minutes",
                "trades_per_day",
                "trade_count",
            }.issubset(metrics)
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            write_results([trade], bars, Path(temp_dir))
            with (Path(temp_dir) / "trades.csv").open(newline="", encoding="utf-8") as file:
                self.assertEqual(len(list(csv.DictReader(file))), 1)
            self.assertTrue((Path(temp_dir) / "metrics.json").is_file())


if __name__ == "__main__":
    unittest.main()
