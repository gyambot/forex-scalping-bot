import unittest
from datetime import datetime, timedelta, timezone

from candidate_strategies import bollinger_reentry_v1, daily_momentum_v1, weekend_gap_fade_v1
from candidate_strategies.backtest_opening_range_breakout_v1 import run_signals
from candidate_strategies.london_breakout_v1 import Signal
from scripts.backtest import Bar


def bar(t, price):
    return Bar(t, price, price + 0.0001, price - 0.0001, price)


class ResearchCandidateTests(unittest.TestCase):
    def test_bollinger_reentry_both_directions_and_prefix(self):
        t = datetime(2025, 1, 1, tzinfo=timezone.utc)
        for sign, direction in ((1, "short"), (-1, "long")):
            values = [1.1] * 19 + [1.1 + sign * .01, 1.1]
            bars = [bar(t + timedelta(minutes=5 * i), p) for i, p in enumerate(values)]
            signals = bollinger_reentry_v1.generate_signals(bars)
            self.assertEqual(signals[-1].direction, direction)
            for n in range(len(bars) + 1):
                self.assertEqual(signals[:n], bollinger_reentry_v1.generate_signals(bars[:n]))

    def test_daily_momentum_exact_elapsed_time_and_dst(self):
        for month, hour in ((1, 7), (7, 6)):
            t = datetime(2025, month, 15, hour, 55, tzinfo=timezone.utc)
            for price, direction in ((1.2, "long"), (1.0, "short")):
                bars = [bar(t - timedelta(days=1), 1.1), bar(t, price)]
                self.assertEqual(daily_momentum_v1.generate_signals(bars)[1].direction, direction)
                self.assertIsNone(daily_momentum_v1.generate_signals(bars[1:])[0])
                self.assertEqual(daily_momentum_v1.generate_signals(bars[:1]),
                                 daily_momentum_v1.generate_signals(bars)[:1])

    def test_weekend_gap_only_and_no_future_data(self):
        friday = datetime(2025, 1, 3, 21, 55, tzinfo=timezone.utc)
        sunday = datetime(2025, 1, 5, 22, tzinfo=timezone.utc)
        for price, direction in ((1.101, "short"), (1.099, "long")):
            bars = [bar(friday, 1.1), bar(sunday, price)]
            signals = weekend_gap_fade_v1.generate_signals(bars)
            self.assertEqual(signals[1].direction, direction)
            self.assertEqual(signals[:1], weekend_gap_fade_v1.generate_signals(bars[:1]))
        bars = [bar(friday, 1.1), bar(friday + timedelta(minutes=10), 1.101)]
        self.assertIsNone(weekend_gap_fade_v1.generate_signals(bars)[1])

    def test_research_runner_next_open_and_stop_priority(self):
        t = datetime(2025, 1, 5, 22, tzinfo=timezone.utc)
        bars = [bar(t, 1.1), Bar(t + timedelta(minutes=5), 1.1, 1.103, 1.098, 1.1)]
        trades = run_signals(bars, [Signal("short", .001), None])
        self.assertEqual(trades[0].entry_time, bars[1].timestamp.isoformat())
        self.assertEqual(trades[0].exit_reason, "stop_loss")
        self.assertEqual(trades[0].pnl_r, -1.0)
        with self.assertRaises(ValueError):
            run_signals(bars, [])


if __name__ == "__main__":
    unittest.main()
