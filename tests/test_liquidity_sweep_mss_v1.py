import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from candidate_strategies.backtest_liquidity_sweep_mss_v1 import run_candidate
from candidate_strategies.liquidity_sweep_mss_v1 import Signal, generate_signals
from scripts.backtest import Bar


START = datetime(2025, 1, 1, tzinfo=timezone.utc)


def bars_for_long():
    values = [
        (1.1010, 1.0994, 1.1000),
        (1.1012, 1.0992, 1.1000),
        (1.1020, 1.0980, 1.1000),
        (1.1013, 1.0991, 1.1000),
        (1.1011, 1.0994, 1.1000),
        (1.1005, 1.0978, 1.0985),
        (1.1025, 1.0986, 1.1022),
    ]
    return [Bar(START + timedelta(minutes=5 * i), close, high, low, close)
            for i, (high, low, close) in enumerate(values)]


class LiquiditySweepTests(unittest.TestCase):
    def test_long_and_short_ordered_sweep_then_break(self):
        long_bars = bars_for_long()
        short_bars = [Bar(b.timestamp, 2.2-b.open, 2.2-b.low, 2.2-b.high, 2.2-b.close)
                      for b in long_bars]
        for bars, direction in ((long_bars, "long"), (short_bars, "short")):
            with self.subTest(direction=direction):
                signals = generate_signals(bars)
                self.assertEqual(signals[:6], [None] * 6)
                self.assertIsNotNone(signals[6])
                self.assertEqual(signals[6].direction, direction)
                self.assertEqual(signals[6].sweep_index, 5)
                self.assertEqual(signals[6].structure_index, 2)

    def test_sweep_requires_reclaim_and_structure_close(self):
        bars = bars_for_long()
        sweep = bars[5]
        bars[5] = Bar(sweep.timestamp, 1.0979, sweep.high, sweep.low, 1.0979)
        self.assertIsNone(generate_signals(bars)[6])

    def test_exact_one_pip_sweep_is_inclusive(self):
        bars = bars_for_long()
        sweep = bars[5]
        bars[5] = Bar(sweep.timestamp, sweep.open, sweep.high, 1.0979, sweep.close)
        self.assertEqual(generate_signals(bars)[6].direction, "long")
        bars = bars_for_long()
        last = bars[6]
        bars[6] = Bar(last.timestamp, 1.101, last.high, last.low, 1.101)
        self.assertIsNone(generate_signals(bars)[6])

    def test_causality_and_expiry(self):
        bars = bars_for_long()
        flat = [Bar(START + timedelta(minutes=5 * i), 1.1000, 1.1001, 1.0999, 1.1000)
                for i in range(6, 18)]
        last = bars[6]
        bars = bars[:6] + flat + [Bar(START + timedelta(minutes=90), last.open, last.high, last.low, last.close)]
        signals = generate_signals(bars)
        self.assertIsNone(signals[-1])
        for n in range(1, len(bars) + 1):
            self.assertEqual(signals[:n], generate_signals(bars[:n]))

    def test_next_open_and_stop_priority(self):
        bars = bars_for_long()
        bars.append(Bar(START + timedelta(minutes=35), 1.1000, 1.1030, 1.0980, 1.1000))
        signal = Signal("long", 5, 2, 1.0980, 2, 1.1020)
        with patch("candidate_strategies.backtest_liquidity_sweep_mss_v1.generate_signals",
                   return_value=[None] * 6 + [signal, None]):
            trades, evidence = run_candidate(bars)
        self.assertEqual(evidence, [signal])
        self.assertEqual(trades[0].entry_time, bars[7].timestamp.isoformat())
        self.assertAlmostEqual(trades[0].entry_price, 1.1001)
        self.assertEqual(trades[0].exit_reason, "stop_loss")
        self.assertEqual(trades[0].pnl_r, -1.0)


if __name__ == "__main__":
    unittest.main()
