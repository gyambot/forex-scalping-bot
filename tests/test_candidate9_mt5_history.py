import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

from paper_trading.candidate9_mt5_history import read_closed_trade
from paper_trading.candidate9_reconciliation import ExpectedTrade
from paper_trading.candidate9_safeguard_model import SafeguardError
from tests.test_candidate9_broker_observation import ReadOnlyBroker


class HistoryBroker(ReadOnlyBroker):
    DEAL_ENTRY_IN = 0
    DEAL_ENTRY_OUT = 1
    DEAL_TYPE_BUY = 0
    DEAL_TYPE_SELL = 1
    DEAL_REASON_SL = 4
    DEAL_REASON_TP = 5

    def __init__(self, now):
        super().__init__(now)
        common = dict(position_id=20, magic=30, symbol="EURUSD", volume=0.01,
                      commission=-0.1, swap=0.0, fee=0.0)
        self.deals = [
            SimpleNamespace(**common, ticket=1, order=10, entry=0, type=0, reason=0,
                            time_msc=int((now - timedelta(minutes=10)).timestamp() * 1000),
                            price=1.1002, profit=0),
            SimpleNamespace(**common, ticket=2, order=11, entry=1, type=1, reason=5,
                            time_msc=int((now - timedelta(minutes=5)).timestamp() * 1000),
                            price=1.1022, profit=2),
        ]
        self.history_queries = []

    def history_deals_get(self, **kwargs):
        self.history_queries.append(kwargs)
        return self.deals


class Candidate9HistoryTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 22, 23, tzinfo=timezone.utc)
        self.broker = HistoryBroker(self.now)
        self.expected = ExpectedTrade(10, 20, 30, "long", Decimal("0.01"),
                                      Decimal("1.1000"), Decimal("1"))

    def read(self, **kwargs):
        args = dict(now=self.now, expected_login=123, epoch_is_verified_utc=True,
                    internal_order_ticket=10, not_before=self.now - timedelta(minutes=15))
        args.update(kwargs)
        return read_closed_trade(self.broker, self.expected, **args)

    def test_reads_matching_history_and_costs_without_submission(self):
        trade = self.read()
        self.assertEqual(self.broker.history_queries, [{"position": 20}])
        self.assertEqual(trade.net_cash, Decimal("1.8"))
        self.assertEqual(trade.adverse_slippage_pips, Decimal("2"))
        self.assertEqual(trade.exit_reason, "take_profit")

    def test_unavailable_history_or_open_position_fails_closed(self):
        self.broker.deals = None
        with self.assertRaisesRegex(SafeguardError, "history unavailable"):
            self.read()
        self.broker.positions = [object()]
        with self.assertRaisesRegex(SafeguardError, "UNEXPECTED_OPEN_POSITION"):
            self.read()

    def test_mismatch_and_missing_costs_are_rejected(self):
        self.broker.deals[0].order = 99
        with self.assertRaisesRegex(SafeguardError, "provenance"):
            self.read()
        self.broker.deals[0].order = 10
        self.broker.deals[1].fee = None
        with self.assertRaisesRegex(SafeguardError, "missing fee"):
            self.read()
        self.broker.deals[1].fee = 0
        with self.assertRaisesRegex(SafeguardError, "internal order"):
            self.read(internal_order_ticket=99)

    def test_partial_unknown_and_future_deals_fail(self):
        self.broker.deals[1].volume = 0.005
        with self.assertRaisesRegex(SafeguardError, "fully closed"):
            self.read()
        self.broker.deals[1].volume = 0.01
        self.broker.deals[1].entry = 3
        with self.assertRaisesRegex(SafeguardError, "unsupported"):
            self.read()
        self.broker.deals[1].entry = 1
        self.broker.deals[1].time_msc = int((self.now + timedelta(seconds=1)).timestamp() * 1000)
        with self.assertRaisesRegex(SafeguardError, "future"):
            self.read()
        self.broker.deals[1].time_msc = int((self.now - timedelta(minutes=5)).timestamp() * 1000)
        with self.assertRaisesRegex(SafeguardError, "predates"):
            self.read(not_before=self.now - timedelta(minutes=9))

    def test_unverified_time_fails_before_history_request(self):
        with self.assertRaisesRegex(SafeguardError, "epoch semantics"):
            self.read(epoch_is_verified_utc=False)
        self.assertEqual(self.broker.history_queries, [])


if __name__ == "__main__":
    unittest.main()
