import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from types import SimpleNamespace

from paper_trading.candidate9_order_preview import interpret_result, preview_order
from paper_trading.candidate9_risk import BrokerConstraints
from paper_trading.candidate9_safeguard_model import SafeguardError
from scripts.backtest import Bar
from tests.test_candidate9_broker_observation import ReadOnlyBroker


class PreviewBroker(ReadOnlyBroker):
    SYMBOL_FILLING_FOK = 1
    SYMBOL_FILLING_IOC = 2
    ORDER_FILLING_FOK = 0
    ORDER_FILLING_IOC = 1
    TRADE_ACTION_DEAL = 1
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    ORDER_TIME_GTC = 0
    TRADE_RETCODE_DONE = 10009
    TRADE_RETCODE_REJECT = 10006
    TRADE_RETCODE_INVALID = 10013
    TRADE_RETCODE_INVALID_STOPS = 10016
    TRADE_RETCODE_NO_MONEY = 10019

    def __init__(self, now):
        super().__init__(now)
        self.symbol.filling_mode = 1


class OrderPreviewTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 22, 22, 5, tzinfo=timezone.utc)
        self.broker = PreviewBroker(self.now)
        self.friday = Bar(datetime(2026, 11, 20, 21, 55, tzinfo=timezone.utc),
                          1.1, 1.1001, 1.0999, 1.1)
        self.reopening = Bar(self.now - timedelta(minutes=5), 1.099, 1.0991, 1.0989, 1.099)
        self.constraints = BrokerConstraints(D("0.00001"), D("0.0002"), D("0.01"),
                                             D("10"), D("0.01"), D("100"))

    def preview(self, **overrides):
        args = dict(now=self.now, expected_login=123, epoch_is_verified_utc=True,
                    friday=self.friday, reopening=self.reopening, volume=D("0.01"),
                    risk_budget=D("2"), costs_per_lot=D("0"),
                    constraints=self.constraints, magic=77)
        args.update(overrides)
        return preview_order(self.broker, **args)

    def test_long_and_short_preview_exact_protective_levels(self):
        long = self.preview()
        self.assertEqual((long.request["type"], long.request["price"], long.request["sl"],
                          long.request["tp"]), (0, 1.1002, 1.0992, 1.1022))
        short_bar = Bar(self.now - timedelta(minutes=5), 1.101, 1.1011, 1.1009, 1.101)
        short = self.preview(reopening=short_bar)
        self.assertEqual((short.request["type"], short.request["price"], short.request["sl"],
                          short.request["tp"]), (1, 1.1, 1.101, 1.098))
        self.assertEqual(short.request["deviation"], 0)

    def test_preflight_rejects_unsafe_inputs(self):
        for field, value, message in (
            ("epoch_is_verified_utc", False, "epoch semantics"),
            ("expected_login", 999, "expected demo"),
            ("risk_budget", D("0.5"), "1R budget"),
            ("magic", 0, "INVALID_MAGIC"),
        ):
            with self.subTest(field=field):
                with self.assertRaisesRegex(SafeguardError, message):
                    self.preview(**{field: value})
        self.broker.tick.ask = 1.10031
        with self.assertRaisesRegex(SafeguardError, "HIGH_SPREAD"):
            self.preview()
        self.broker.tick.ask = 1.1002
        self.broker.positions = [1]
        with self.assertRaisesRegex(SafeguardError, "UNEXPECTED_OPEN_POSITION"):
            self.preview()
        self.broker.positions = []
        self.broker.symbol.filling_mode = 0
        with self.assertRaisesRegex(SafeguardError, "filling mode"):
            self.preview()

    def test_result_classification_never_assumes_partial_or_unknown_is_filled(self):
        for code in (10006, 10013, 10016, 10019):
            self.assertEqual(interpret_result(self.broker, SimpleNamespace(retcode=code)).status,
                             "REJECTED")
        for result in (None, SimpleNamespace(retcode=10010), SimpleNamespace(retcode=10008),
                       SimpleNamespace(retcode=10009, order=1, deal=0)):
            self.assertEqual(interpret_result(self.broker, result).status, "UNKNOWN")
        result = interpret_result(self.broker, SimpleNamespace(retcode=10009, order=10, deal=20))
        self.assertEqual((result.status, result.order_ticket, result.deal_ticket),
                         ("FILL_REQUIRES_VERIFICATION", 10, 20))
        self.broker.TRADE_RETCODE_REJECT = self.broker.TRADE_RETCODE_DONE
        with self.assertRaisesRegex(SafeguardError, "ambiguous"):
            interpret_result(self.broker, result)


if __name__ == "__main__":
    unittest.main()
