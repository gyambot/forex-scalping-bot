import unittest
from datetime import datetime, timedelta, timezone

from candidate_strategies.backtest_opening_range_breakout_v1 import run_signals
from candidate_strategies.opening_range_breakout_v1 import generate_signals
from scripts.backtest import Bar


class OpeningRangeTests(unittest.TestCase):
    def bars(self, month, hour):
        start = datetime(2025, month, 15, hour, tzinfo=timezone.utc)
        bars = [Bar(start + timedelta(minutes=5 * i), 1.1, 1.1005, 1.0995, 1.1)
                for i in range(12)]
        bars += [Bar(start + timedelta(hours=1), 1.1, 1.1011, 1.0999, 1.101),
                 Bar(start + timedelta(hours=1, minutes=5), 1.101, 1.104, 1.1009, 1.103)]
        return bars

    def test_summer_winter_prefix_and_one_signal(self):
        for month, hour in ((1, 7), (7, 6)):
            bars = self.bars(month, hour)
            signals = generate_signals(bars)
            self.assertEqual(signals[12].direction, "long")
            self.assertIsNone(signals[13])
            for n in range(len(bars) + 1):
                self.assertEqual(signals[:n], generate_signals(bars[:n]))
            trades = run_signals(bars, signals)
            self.assertEqual(len(trades), 1)
            self.assertEqual(trades[0].entry_time, bars[13].timestamp.isoformat())
            self.assertEqual(trades[0].exit_reason, "take_profit")
            self.assertEqual(trades[0].pnl_r, 2.0)

    def test_incomplete_range_and_short(self):
        bars = self.bars(1, 7)
        self.assertFalse(any(generate_signals(bars[:5] + bars[6:])))
        bars[12] = Bar(bars[12].timestamp, 1.1, 1.1001, 1.0989, 1.099)
        self.assertEqual(generate_signals(bars)[12].direction, "short")
        bars[12] = Bar(bars[12].timestamp, 1.1, 1.1001, 1.0995, 1.0995)
        self.assertIsNone(generate_signals(bars)[12])


if __name__ == "__main__":
    unittest.main()
