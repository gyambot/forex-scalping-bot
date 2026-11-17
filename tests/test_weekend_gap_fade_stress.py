import unittest
from datetime import datetime, timedelta, timezone

from candidate_strategies.backtest_opening_range_breakout_v1 import run_signals
from candidate_strategies.london_breakout_v1 import Signal
from candidate_strategies.stress_weekend_gap_fade import SCENARIOS, Scenario, run_stress
from scripts.backtest import Bar


class StressTests(unittest.TestCase):
    def setUp(self):
        t = datetime(2025, 1, 5, 22, tzinfo=timezone.utc)
        self.bars = [
            Bar(t, 1.1, 1.1001, 1.0999, 1.1),
            Bar(t + timedelta(minutes=5), 1.1, 1.1008, 1.0994, 1.1),
        ]

    def test_baseline_matches_existing_and_spread_changes_stops(self):
        for direction in ("long", "short"):
            signals = [Signal(direction, 0.001), None]
            self.assertEqual(run_stress(self.bars, signals, SCENARIOS["A"]),
                             run_signals(self.bars, signals))
            base = run_stress(self.bars, signals, SCENARIOS["A"])[0]
            stressed = run_stress(self.bars, signals, SCENARIOS["D"])[0]
            self.assertEqual(base.exit_reason, "end_of_data")
            self.assertEqual(stressed.exit_reason, "stop_loss")
            self.assertEqual(stressed.pnl_r, -1.0)

    def test_slippage_entry_and_fixed_risk_both_sides(self):
        for direction, expected in (("long", 1.1003), ("short", 1.0999)):
            trade = run_stress(self.bars, [Signal(direction, 0.001), None], SCENARIOS["E"])[0]
            self.assertAlmostEqual(trade.entry_price, expected)
            self.assertAlmostEqual(abs(trade.entry_price - trade.stop_price), 0.001)
            self.assertAlmostEqual(abs(trade.entry_price - trade.target_price), 0.002)

    def test_short_gap_and_stop_priority(self):
        t = self.bars[1].timestamp + timedelta(minutes=5)
        bars = [self.bars[0], Bar(self.bars[1].timestamp, 1.1, 1.1002, 1.0999, 1.1),
                Bar(t, 1.101, 1.102, 1.097, 1.101)]
        trade = run_stress(bars, [Signal("short", .001), None, None], SCENARIOS["B"])[0]
        self.assertEqual(trade.exit_reason, "stop_loss_gap")
        self.assertAlmostEqual(trade.exit_price, 1.1012)
        self.assertEqual(trade.pnl_pips, -12.0)
        bars[1] = Bar(bars[1].timestamp, 1.1, 1.101, 1.097, 1.1)
        trade = run_stress(bars, [Signal("short", .001), None, None], SCENARIOS["B"])[0]
        self.assertEqual(trade.exit_reason, "stop_loss")

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            run_stress(self.bars, [], SCENARIOS["A"])
        for scenario in (Scenario(-1, 0), Scenario(1, float("nan"))):
            with self.assertRaises(ValueError):
                run_stress(self.bars, [None, None], scenario)


if __name__ == "__main__":
    unittest.main()
