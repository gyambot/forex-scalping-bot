import math
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from candidate_strategies.backtest_trendline_stochastic_v1 import run_candidate
from candidate_strategies.trendline_stochastic_v1 import Signal, classify_signal, generate_signals
from scripts.backtest import Bar


def bars_for_test(count):
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return [
        Bar(start + timedelta(minutes=5 * i), 1.1 + i * 0.00001 + math.sin(i / 3) * 0.0005,
            1.1004 + i * 0.00001 + math.sin(i / 3) * 0.0005,
            1.0996 + i * 0.00001 + math.sin(i / 3) * 0.0005,
            1.1 + i * 0.00001 + math.sin(i / 3) * 0.0005)
        for i in range(count)
    ]


class CandidateTests(unittest.TestCase):
    def test_four_setup_rules_and_cross_requirement(self):
        time = datetime(2025, 1, 1, tzinfo=timezone.utc)
        long_bar = Bar(time, 1.0, 1.3, 0.99, 1.2)
        short_bar = Bar(time, 1.0, 1.01, 0.7, 0.8)
        self.assertEqual(classify_signal(long_bar, 1.0, 1.1, 0.05, None, (1.0, -0.01), 60, 50, 55, 50), Signal("long", "breakout"))
        self.assertEqual(classify_signal(short_bar, 1.0, 0.9, 0.05, (1.0, 0.01), None, 40, 50, 45, 50), Signal("short", "breakout"))
        self.assertEqual(classify_signal(long_bar, 1.2, 1.1, 0.05, (1.0, 0.01), None, 15, 14, 12, 14), Signal("long", "bounce"))
        self.assertEqual(classify_signal(short_bar, 0.8, 0.9, 0.05, None, (1.0, -0.01), 85, 86, 88, 86), Signal("short", "bounce"))
        self.assertIsNone(classify_signal(long_bar, 1.2, 1.1, 0.05, (1.0, 0.01), None, 15, 14, 16, 14))

    def test_signals_are_prefix_causal(self):
        bars = bars_for_test(500)
        full = generate_signals(bars)
        for count in (1, 200, 201, 230, 300, 450):
            self.assertEqual(full[:count], generate_signals(bars[:count]))
        self.assertTrue(all(signal is None for signal in full[:199]))

    def test_next_open_and_stop_priority_for_long_and_short(self):
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        bars = [
            Bar(start, 1.1, 1.1001, 1.0999, 1.1),
            Bar(start + timedelta(minutes=5), 1.1, 1.103, 1.098, 1.1),
            Bar(start + timedelta(minutes=10), 1.1, 1.103, 1.098, 1.1),
        ]
        with patch("candidate_strategies.backtest_trendline_stochastic_v1.generate_signals",
                   return_value=[Signal("long", "bounce"), Signal("short", "breakout"), None]):
            trades, setups = run_candidate(bars)
        self.assertEqual(setups, ["bounce", "breakout"])
        self.assertEqual([trade.exit_reason for trade in trades], ["stop_loss", "stop_loss"])
        self.assertEqual(trades[0].entry_time, bars[1].timestamp.isoformat())
        self.assertAlmostEqual(trades[0].entry_price, 1.1001)
        self.assertAlmostEqual(trades[1].entry_price, 1.1)
        self.assertAlmostEqual(trades[0].pnl_r, -1.0)

    def test_last_bar_signal_does_not_create_trade(self):
        bars = bars_for_test(2)
        with patch("candidate_strategies.backtest_trendline_stochastic_v1.generate_signals",
                   return_value=[None, Signal("long", "breakout")]):
            trades, setups = run_candidate(bars)
        self.assertEqual((trades, setups), ([], []))


if __name__ == "__main__":
    unittest.main()
