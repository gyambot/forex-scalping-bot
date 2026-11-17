import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from candidate_strategies.backtest_london_breakout_v1 import run_candidate
from candidate_strategies.london_breakout_v1 import Signal, generate_signals, london_session_at_close
from scripts.backtest import Bar


class LondonBreakoutTests(unittest.TestCase):
    def test_london_session_boundaries_winter_summer_and_broker_offset(self):
        utc = timezone.utc
        for month, start_utc in ((1, 7), (7, 6)):
            day = datetime(2025, month, 15, start_utc, tzinfo=utc)
            self.assertFalse(london_session_at_close(day - timedelta(minutes=10)))
            self.assertTrue(london_session_at_close(day - timedelta(minutes=5)))
            self.assertTrue(london_session_at_close(day + timedelta(hours=4) - timedelta(minutes=10)))
            self.assertFalse(london_session_at_close(day + timedelta(hours=4) - timedelta(minutes=5)))
            broker = (day - timedelta(minutes=5)).astimezone(timezone(timedelta(hours=2)))
            self.assertTrue(london_session_at_close(broker))
        with self.assertRaises(ValueError):
            london_session_at_close(datetime(2025, 1, 1))

    def test_prior_range_excludes_current_and_both_directions(self):
        start = datetime(2025, 1, 15, 7, tzinfo=timezone.utc) - timedelta(minutes=5 * 199)
        for sign, expected in ((1, "long"), (-1, "short")):
            bars = []
            for i in range(200):
                price = 1.1 + sign * i * 0.0001
                bars.append(Bar(start + timedelta(minutes=5*i), price, price + 0.00005,
                                price - 0.00005, price))
            signals = generate_signals(bars)
            self.assertEqual(signals[-1].direction, expected)
            self.assertGreater(signals[-1].atr, 0)
            self.assertEqual(signals[:199], [None] * 199)
            for n in (1, 13, 100, 199, 200):
                self.assertEqual(signals[:n], generate_signals(bars[:n]))
            last = bars[-1]
            close = bars[-2].high if sign == 1 else bars[-2].low
            bars[-1] = Bar(last.timestamp, close, max(last.high, close), min(last.low, close), close)
            self.assertIsNone(generate_signals(bars)[-1])

    def test_next_open_atr_r_and_gap_for_both_sides(self):
        t = datetime(2025, 1, 15, 7, tzinfo=timezone.utc)
        bars = [Bar(t, 1.1, 1.1001, 1.0999, 1.1),
                Bar(t + timedelta(minutes=5), 1.1, 1.1003, 1.0999, 1.1),
                Bar(t + timedelta(minutes=10), 1.098, 1.0981, 1.0979, 1.098)]
        with patch("candidate_strategies.backtest_london_breakout_v1.generate_signals",
                   return_value=[Signal("long", 0.0005), None, None]):
            trades = run_candidate(bars)
        self.assertEqual(trades[0].entry_time, bars[1].timestamp.isoformat())
        self.assertEqual(trades[0].exit_reason, "stop_loss_gap")
        self.assertEqual(trades[0].pnl_r, -4.2)
        self.assertAlmostEqual(trades[0].target_price - trades[0].entry_price, 0.001)
        bars[1] = Bar(bars[1].timestamp, 1.1, 1.1008, 1.098, 1.1)
        with patch("candidate_strategies.backtest_london_breakout_v1.generate_signals",
                   return_value=[Signal("short", 0.0005), None, None]):
            trades = run_candidate(bars)
        self.assertEqual(trades[0].exit_reason, "stop_loss")
        self.assertEqual(trades[0].pnl_r, -1.0)
        self.assertAlmostEqual(trades[0].stop_price - trades[0].entry_price, 0.0005)

    def test_last_bar_signal_not_entered(self):
        t = datetime(2025, 1, 15, 7, tzinfo=timezone.utc)
        bars = [Bar(t, 1.1, 1.101, 1.099, 1.1)]
        with patch("candidate_strategies.backtest_london_breakout_v1.generate_signals",
                   return_value=[Signal("long", 0.0005)]):
            self.assertEqual(run_candidate(bars), [])


if __name__ == "__main__":
    unittest.main()
