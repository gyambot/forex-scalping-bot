import math
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from candidate_strategies.backtest_ema_pullback_continuation_v1 import run_candidate
from candidate_strategies.ema_pullback_continuation_v1 import Signal, generate_signals
from scripts.backtest import Bar


START = datetime(2025, 1, 1, tzinfo=timezone.utc)


def trending_bars(direction):
    bars = []
    for i in range(199):
        price = 1.1 + direction * i * 0.0001
        bars.append(Bar(START + timedelta(minutes=5 * i), price, price + 0.0002,
                        price - 0.0002, price))
    price = bars[-1].close + direction * 0.0001
    bars.append(Bar(START + timedelta(minutes=995), price - direction * 0.0001,
                    price + 0.004, price - 0.004, price))
    return bars


class EmaPullbackTests(unittest.TestCase):
    def test_long_short_and_strict_candle_confirmation(self):
        for direction, label in ((1, "long"), (-1, "short")):
            with self.subTest(direction=label):
                bars = trending_bars(direction)
                signals = generate_signals(bars)
                self.assertEqual(signals[-1].direction, label)
                expected_tr = max(bars[-1].high - bars[-1].low,
                                  abs(bars[-1].high - bars[-2].close),
                                  abs(bars[-1].low - bars[-2].close))
                self.assertTrue(math.isclose(signals[-1].atr, (13 * 0.0004 + expected_tr) / 14))
                last = bars[-1]
                bars[-1] = Bar(last.timestamp, last.close, last.high, last.low, last.close)
                self.assertIsNone(generate_signals(bars)[-1])

    def test_prefix_causality_and_warmup(self):
        bars = trending_bars(1)
        signals = generate_signals(bars)
        self.assertEqual(signals[:199], [None] * 199)
        for n in (1, 14, 100, 199, 200):
            self.assertEqual(signals[:n], generate_signals(bars[:n]))

    def test_atr_risk_for_long_and_short_including_gap(self):
        bars = [
            Bar(START, 1.1, 1.1001, 1.0999, 1.1),
            Bar(START + timedelta(minutes=5), 1.1, 1.1003, 1.0999, 1.1),
            Bar(START + timedelta(minutes=10), 1.098, 1.0981, 1.0979, 1.098),
        ]
        with patch("candidate_strategies.backtest_ema_pullback_continuation_v1.generate_signals",
                   return_value=[Signal("long", 0.0005), None, None]):
            trades = run_candidate(bars)
        self.assertEqual(trades[0].exit_reason, "stop_loss_gap")
        self.assertEqual(trades[0].pnl_r, -4.2)
        self.assertAlmostEqual(trades[0].entry_price - trades[0].stop_price, 0.0005)
        self.assertAlmostEqual(trades[0].target_price - trades[0].entry_price, 0.001)
        bars[1] = Bar(bars[1].timestamp, 1.1, 1.1008, 1.098, 1.1)
        with patch("candidate_strategies.backtest_ema_pullback_continuation_v1.generate_signals",
                   return_value=[Signal("short", 0.0005), None, None]):
            trades = run_candidate(bars)
        self.assertEqual(trades[0].exit_reason, "stop_loss")
        self.assertEqual(trades[0].pnl_r, -1.0)
        self.assertAlmostEqual(trades[0].stop_price - trades[0].entry_price, 0.0005)

    def test_final_bar_signal_cannot_enter(self):
        bars = trending_bars(1)
        with patch("candidate_strategies.backtest_ema_pullback_continuation_v1.generate_signals",
                   return_value=[None] * 199 + [Signal("long", 0.001)]):
            self.assertEqual(run_candidate(bars), [])


if __name__ == "__main__":
    unittest.main()
