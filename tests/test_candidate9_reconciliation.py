import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D

from paper_trading.candidate9_reconciliation import Deal, ExpectedTrade, reconcile
from paper_trading.candidate9_safeguard_model import SafeguardError


class Candidate9ReconciliationTests(unittest.TestCase):
    def setUp(self):
        t = datetime(2026, 11, 22, 22, tzinfo=timezone.utc)
        self.expected = ExpectedTrade(10, 20, 30, "long", D("0.02"), D("1.1000"), D("2"))
        self.entry = Deal(1, 10, 20, 30, "EURUSD", "buy", "entry", t,
                          D("0.02"), D("1.1002"), D("0"), D("-0.1"), D("0"), D("0"), "client")
        self.exit = Deal(2, 11, 20, 30, "EURUSD", "sell", "exit", t + timedelta(minutes=5),
                         D("0.02"), D("1.1022"), D("4"), D("-0.1"), D("0"), D("0"), "take_profit")

    def reconcile(self, entries=None, expected=None, closed=True, order=10):
        return reconcile(expected or self.expected, entries or [self.entry, self.exit],
                         position_is_closed=closed, internal_order_ticket=order)

    def test_net_costs_slippage_and_partial_fills(self):
        trade = self.reconcile()
        self.assertEqual(trade.net_cash, D("3.8"))
        self.assertEqual(trade.pnl_r, D("1.9"))
        self.assertEqual(trade.adverse_slippage_pips, D("2"))
        entries = [replace(self.entry, volume=D("0.01")),
                   replace(self.entry, ticket=3, volume=D("0.01")), self.exit]
        self.assertEqual(self.reconcile(entries).entry_price, D("1.1002"))

    def test_short_signed_slippage(self):
        expected = replace(self.expected, direction="short")
        entries = [replace(self.entry, side="sell", price=D("1.0998")),
                   replace(self.exit, side="buy", price=D("1.0978"))]
        self.assertEqual(self.reconcile(entries, expected).adverse_slippage_pips, D("2"))

    def test_unsafe_history_and_unknown_state_rejected(self):
        tests = [
            ([self.entry, self.entry], True, 10),
            ([replace(self.entry, order_ticket=99), self.exit], True, 10),
            ([self.entry, replace(self.exit, position_id=99)], True, 10),
            ([self.entry, replace(self.exit, volume=D("0.01"))], True, 10),
            ([self.entry, replace(self.exit, fee=D("NaN"))], True, 10),
            ([self.entry, replace(self.exit, time=self.entry.time - timedelta(seconds=1))], True, 10),
            ([self.entry, self.exit], False, 10),
            ([self.entry, self.exit], True, 99),
        ]
        for deals, closed, order in tests:
            with self.subTest(deals=deals, closed=closed, order=order):
                with self.assertRaises(SafeguardError):
                    self.reconcile(deals, closed=closed, order=order)


if __name__ == "__main__":
    unittest.main()
