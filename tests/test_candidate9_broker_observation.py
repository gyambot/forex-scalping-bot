import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from paper_trading.candidate9_broker_observation import derive_weekend_signal, observe_broker
from paper_trading.candidate9_safeguard_model import SafeguardError
from paper_trading.mt5_connector import EXPECTED_SERVER
from scripts.backtest import Bar


class ReadOnlyBroker:
    ACCOUNT_TRADE_MODE_DEMO = 0
    SYMBOL_TRADE_MODE_FULL = 4

    def __init__(self, now):
        self.terminal = SimpleNamespace(connected=True, trade_allowed=True, tradeapi_disabled=False)
        self.account = SimpleNamespace(login=123, server=EXPECTED_SERVER, trade_mode=0,
                                       trade_allowed=True, trade_expert=True)
        self.symbol = SimpleNamespace(visible=True, trade_mode=4)
        self.tick = SimpleNamespace(bid=1.1, ask=1.1002, time_msc=int(now.timestamp() * 1000))
        self.positions = []
        self.orders = []

    def terminal_info(self):
        return self.terminal

    def account_info(self):
        return self.account

    def symbol_info(self, symbol):
        return self.symbol if symbol == "EURUSD" else None

    def symbol_info_tick(self, symbol):
        return self.tick

    def positions_get(self):
        return self.positions

    def orders_get(self):
        return self.orders

    def order_send(self, request):
        raise AssertionError("read-only observer must never submit orders")


class Candidate9BrokerObservationTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 22, 22, 5, tzinfo=timezone.utc)
        self.broker = ReadOnlyBroker(self.now)

    def observe(self, verified=True):
        return observe_broker(self.broker, now=self.now, expected_login=123, epoch_is_verified_utc=verified)

    def test_demo_flat_fresh_quote_is_read_only(self):
        obs = self.observe()
        self.assertAlmostEqual(obs.spread_pips, 2)
        self.assertEqual(obs.positions, 0)
        self.assertEqual(obs.pending_orders, 0)

    def test_unverified_time_stale_and_future_quotes_fail(self):
        with self.assertRaisesRegex(SafeguardError, "epoch semantics"):
            self.observe(False)
        for seconds in (-6, 1):
            self.broker.tick.time_msc = int((self.now + timedelta(seconds=seconds)).timestamp() * 1000)
            with self.assertRaisesRegex(SafeguardError, "stale quote"):
                self.observe()

    def test_real_unknown_and_unavailable_account_or_positions_fail(self):
        for attr, value, message in (
            ("account", None, "account or terminal"),
            ("positions", None, "positions or orders"),
            ("positions", [1], "UNEXPECTED_OPEN_POSITION"),
            ("orders", [1], "UNEXPECTED_PENDING_ORDER"),
        ):
            with self.subTest(attr=attr, value=value):
                original = getattr(self.broker, attr)
                setattr(self.broker, attr, value)
                with self.assertRaisesRegex(SafeguardError, message):
                    self.observe()
                setattr(self.broker, attr, original)
        self.broker.account.trade_mode = 2
        with self.assertRaisesRegex(SafeguardError, "expected demo"):
            self.observe()
        self.broker.account.trade_mode = 0
        self.broker.terminal.trade_allowed = None
        with self.assertRaisesRegex(SafeguardError, "permissions"):
            self.observe()

    def test_weekend_signal_both_directions_and_bar_close(self):
        friday_time = datetime(2026, 11, 20, 21, 55, tzinfo=timezone.utc)
        sunday_time = datetime(2026, 11, 22, 22, tzinfo=timezone.utc)
        friday = Bar(friday_time, 1.1, 1.1001, 1.0999, 1.1)
        for price, direction in ((1.101, "short"), (1.099, "long"), (1.1001, None)):
            reopening = Bar(sunday_time, price, price + .0001, price - .0001, price)
            result = derive_weekend_signal(friday, reopening, observed_at=self.now)
            self.assertEqual(result.direction, direction)
            self.assertEqual(result.nominal_entry_time, sunday_time + timedelta(minutes=5))
            with self.assertRaisesRegex(SafeguardError, "not completed"):
                derive_weekend_signal(friday, reopening, observed_at=self.now - timedelta(seconds=1))
        with self.assertRaisesRegex(SafeguardError, "explicit-offset"):
            derive_weekend_signal(friday, Bar(sunday_time.replace(tzinfo=None), 1.1, 1.1, 1.1, 1.1),
                                  observed_at=self.now)


if __name__ == "__main__":
    unittest.main()
