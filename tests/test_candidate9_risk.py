import unittest
from dataclasses import replace
from decimal import Decimal as D

from paper_trading.candidate9_risk import BrokerConstraints, prepare_risk
from paper_trading.candidate9_safeguard_model import SafeguardError


class Candidate9RiskTests(unittest.TestCase):
    def setUp(self):
        self.constraints = BrokerConstraints(D("0.00001"), D("0.0002"), D("0.01"),
                                             D("10"), D("0.01"), D("100"))

    def prepare(self, direction="long", bid=D("1.10000"), ask=D("1.10020"),
                volume=D("0.01"), budget=D("1.1"), costs=D("10"), constraints=None):
        return prepare_risk(direction, bid, ask, volume, budget, costs,
                            constraints or self.constraints)

    def test_long_and_short_protection_and_risk(self):
        long = self.prepare()
        self.assertEqual((long.entry, long.stop, long.target, long.modeled_loss),
                         (D("1.10020"), D("1.09920"), D("1.10220"), D("1.10")))
        short = self.prepare(direction="short")
        self.assertEqual((short.entry, short.stop, short.target),
                         (D("1.10000"), D("1.10100"), D("1.09800")))

    def test_volume_and_budget_refused(self):
        for kwargs in ({"volume": D("0.015")}, {"volume": D("0.001")},
                       {"budget": D("1.09")}, {"costs": D("-1")}):
            with self.subTest(kwargs=kwargs), self.assertRaises(SafeguardError):
                self.prepare(**kwargs)

    def test_tick_grid_and_spread_sensitive_stop_distance(self):
        with self.assertRaisesRegex(SafeguardError, "tick grid"):
            self.prepare(ask=D("1.100205"))
        with self.assertRaisesRegex(SafeguardError, "minimum stop distance"):
            self.prepare(constraints=replace(self.constraints, min_stop_distance=D("0.0009")))
        with self.assertRaisesRegex(SafeguardError, "minimum stop distance"):
            self.prepare(direction="short", constraints=replace(self.constraints, min_stop_distance=D("0.0009")))

    def test_unknown_values_fail(self):
        for kwargs in ({"bid": D("NaN")}, {"ask": D("1.0")},
                       {"constraints": replace(self.constraints, loss_per_lot_at_stop=D("0"))}):
            with self.subTest(kwargs=kwargs), self.assertRaises(SafeguardError):
                self.prepare(**kwargs)


if __name__ == "__main__":
    unittest.main()
