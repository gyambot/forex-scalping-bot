import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from paper_trading import mt5_connector
from paper_trading.mt5_connector import (
    EXPECTED_SERVER,
    MT5Config,
    MT5ConnectorError,
    MT5DependencyError,
    load_config,
)
from paper_trading.mt5_healthcheck import run_healthcheck
from paper_trading.mt5_price_feed import (
    get_current_spread,
    get_current_tick,
    get_latest_m5_bar,
    get_recent_m5_bars,
)


class FakeMT5:
    ACCOUNT_TRADE_MODE_DEMO = 0
    ACCOUNT_TRADE_MODE_REAL = 2
    SYMBOL_TRADE_MODE_DISABLED = 0
    SYMBOL_TRADE_MODE_CLOSEONLY = 3
    SYMBOL_TRADE_MODE_FULL = 4
    TIMEFRAME_M5 = 5

    def __init__(self):
        self.initialize_result = True
        self.shutdown_called = False
        self.initialize_kwargs = None
        self.symbol_visible = True
        self.symbol_info_value = SimpleNamespace(visible=True, trade_mode=4)
        self.tick_time = int(datetime.now(timezone.utc).timestamp()) + 7200
        self.tick = SimpleNamespace(
            bid=1.10000,
            ask=1.10012,
            time=self.tick_time,
            time_msc=self.tick_time * 1000,
        )
        self.account = SimpleNamespace(
            login=123456,
            server=EXPECTED_SERVER,
            name="Demo Account",
            currency="USD",
            leverage=100,
            balance=10000.0,
            equity=10001.0,
            trade_mode=0,
            trade_allowed=True,
            trade_expert=True,
        )
        self.terminal = SimpleNamespace(
            connected=True,
            build=5000,
            trade_allowed=True,
            tradeapi_disabled=False,
        )
        self.rates_args = None

    def initialize(self, **kwargs):
        self.initialize_kwargs = kwargs
        return self.initialize_result

    def shutdown(self):
        self.shutdown_called = True

    def last_error(self):
        return (-10004, "No connection")

    def terminal_info(self):
        return self.terminal

    def account_info(self):
        return self.account

    def symbol_info(self, symbol):
        if symbol != "EURUSD":
            return None
        self.symbol_info_value.visible = self.symbol_visible
        return self.symbol_info_value

    def symbol_select(self, symbol, visible):
        if symbol != "EURUSD":
            return False
        self.symbol_visible = visible
        return True

    def symbol_info_tick(self, symbol):
        return self.tick if symbol == "EURUSD" else None

    def copy_rates_from_pos(self, symbol, timeframe, start_pos, count):
        self.rates_args = (symbol, timeframe, start_pos, count)
        base = self.tick_time - self.tick_time % 300 - count * 300
        return [
            {
                "time": base + index * 300,
                "open": 1.1,
                "high": 1.1002,
                "low": 1.0998,
                "close": 1.1001,
                "tick_volume": 10,
                "spread": 12,
                "real_volume": 0,
            }
            for index in range(count)
        ]


class MT5ConnectorTests(unittest.TestCase):
    def setUp(self):
        mt5_connector.shutdown_connection()
        self.fake = FakeMT5()
        self.config = MT5Config(login=123456, server=EXPECTED_SERVER)
        self.load_config_patch = patch(
            "paper_trading.mt5_connector.load_config", return_value=self.config
        )
        self.load_config_patch.start()
        self.mt5_patch = patch("paper_trading.mt5_connector._load_mt5", return_value=self.fake)
        self.mt5_patch.start()

    def tearDown(self):
        mt5_connector.shutdown_connection()
        self.mt5_patch.stop()
        self.load_config_patch.stop()

    def connect(self):
        self.assertTrue(mt5_connector.initialize_connection())

    def test_configuration_loading_and_environment_precedence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            env_file.write_text(
                "MT5_LOGIN=100\nMT5_PASSWORD='file-secret'\n"
                "MT5_SERVER=ICMarketsSC-Demo\n",
                encoding="utf-8",
            )
            config = load_config(env_file, environ={})
            self.assertEqual(config.login, 100)
            self.assertEqual(config.password, "file-secret")
            self.assertEqual(config.broker_utc_offset, "+02:00")
            overridden = load_config(
                env_file,
                environ={
                    "MT5_LOGIN": "200",
                    "MT5_PASSWORD": "environment-secret",
                    "MT5_SERVER": EXPECTED_SERVER,
                    "MT5_BROKER_UTC_OFFSET": "+03:00",
                },
            )
            self.assertEqual(overridden.login, 200)
            self.assertEqual(overridden.password, "environment-secret")
            self.assertEqual(overridden.broker_utc_offset, "+03:00")
            self.assertNotIn("environment-secret", repr(overridden))

    def test_configuration_rejects_missing_credentials_and_non_demo_server(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            with self.assertRaisesRegex(MT5ConnectorError, "MT5_LOGIN is required"):
                load_config(env_file, environ={})
            env_file.write_text(
                "MT5_LOGIN=100\nMT5_SERVER=ICMarketsSC-Demo\n",
                encoding="utf-8",
            )
            config = load_config(env_file, environ={})
            self.assertIsNone(config.password)
            self.assertEqual(config.login, 100)
            env_file.write_text(
                "MT5_LOGIN=100\nMT5_PASSWORD=secret\nMT5_SERVER=ICMarketsSC-Live\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(MT5ConnectorError, "refusing any other server"):
                load_config(env_file, environ={})
            env_file.write_text(
                "MT5_LOGIN=100\nMT5_SERVER=ICMarketsSC-Demo\n"
                "MT5_BROKER_UTC_OFFSET=not-an-offset\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(MT5ConnectorError, "MT5_BROKER_UTC_OFFSET"):
                load_config(env_file, environ={})

    def test_initialize_uses_requested_login_and_demo_server(self):
        self.connect()
        self.assertEqual(self.fake.initialize_kwargs, {})
        self.assertTrue(mt5_connector.verify_terminal_status()["connected"])
        self.assertEqual(mt5_connector.verify_account().server, EXPECTED_SERVER)

    def test_account_server_and_live_account_fail_closed(self):
        self.fake.account.server = "ICMarketsSC-Live"
        with self.assertRaisesRegex(MT5ConnectorError, "expected 'ICMarketsSC-Demo'"):
            mt5_connector.initialize_connection()
        self.assertTrue(self.fake.shutdown_called)

        self.fake = FakeMT5()
        self.fake.account.trade_mode = self.fake.ACCOUNT_TRADE_MODE_REAL
        with patch("paper_trading.mt5_connector._load_mt5", return_value=self.fake):
            with self.assertRaisesRegex(MT5ConnectorError, "not a demo account"):
                mt5_connector.initialize_connection()
        self.assertTrue(self.fake.shutdown_called)

    def test_missing_terminal_initialization_reports_error_and_shutdown_is_safe(self):
        self.fake.initialize_result = False
        with self.assertRaisesRegex(MT5ConnectorError, "Unable to initialize"):
            mt5_connector.initialize_connection()
        with self.assertRaisesRegex(MT5ConnectorError, "not connected"):
            mt5_connector.verify_terminal_status()
        self.assertFalse(mt5_connector.shutdown_connection())
        self.assertTrue(self.fake.shutdown_called)

    def test_missing_mt5_package_is_reported(self):
        with patch(
            "paper_trading.mt5_connector._load_mt5",
            side_effect=MT5DependencyError("package unavailable"),
        ):
            with self.assertRaisesRegex(MT5DependencyError, "package unavailable"):
                mt5_connector.initialize_connection()

    def test_symbol_visibility_permissions_and_market_status(self):
        self.connect()
        self.fake.symbol_visible = False
        info = mt5_connector.verify_symbol("EURUSD")
        self.assertTrue(info.visible)
        permissions = mt5_connector.verify_trade_permissions()
        self.assertTrue(permissions["permitted"])
        status = mt5_connector.verify_market_status()
        self.assertTrue(status["market_open"])
        self.assertTrue(status["quote_available"])

        self.fake.terminal.trade_allowed = False
        self.assertFalse(mt5_connector.verify_trade_permissions()["permitted"])
        self.fake.tick.time -= 1000
        self.assertFalse(mt5_connector.verify_market_status()["market_open"])

    def test_healthcheck_has_required_fields_and_reads_demo_account(self):
        self.connect()
        expected = {
            "connected": True,
            "login": 123456,
            "server": EXPECTED_SERVER,
            "account_name": "Demo Account",
            "currency": "USD",
            "leverage": 100,
            "balance": 10000.0,
            "equity": 10001.0,
            "trade_allowed": True,
            "terminal_build": 5000,
            "eurusd_available": True,
            "demo_or_live": "demo",
        }
        with (
            patch("paper_trading.mt5_healthcheck.load_config", return_value=self.config),
            patch("paper_trading.mt5_connector.initialize_connection", return_value=True),
            patch("paper_trading.mt5_healthcheck.mt5_connector.shutdown_connection"),
        ):
            report = run_healthcheck()
        for field, value in expected.items():
            self.assertEqual(report[field], value)
        self.assertTrue(report["success"])

    def test_healthcheck_warns_on_disabled_trade_permission_but_allows_read_only_success(self):
        self.connect()
        self.fake.terminal.trade_allowed = False
        with (
            patch("paper_trading.mt5_healthcheck.load_config", return_value=self.config),
            patch("paper_trading.mt5_connector.initialize_connection", return_value=True),
            patch("paper_trading.mt5_healthcheck.mt5_connector.shutdown_connection"),
        ):
            report = run_healthcheck()
        self.assertTrue(report["eurusd_available"])
        self.assertFalse(report["trade_allowed"])
        self.assertTrue(report["success"])
        self.assertTrue(any("will not enable" in warning for warning in report["warnings"]))

    def test_healthcheck_keeps_future_dated_quote_available_and_warns(self):
        self.connect()
        self.fake.tick.time += 7200
        with (
            patch("paper_trading.mt5_healthcheck.load_config", return_value=self.config),
            patch("paper_trading.mt5_connector.initialize_connection", return_value=True),
            patch("paper_trading.mt5_healthcheck.mt5_connector.shutdown_connection"),
        ):
            report = run_healthcheck()
        self.assertTrue(report["eurusd_available"])
        self.assertFalse(report["quote_fresh_vs_broker_clock"])
        self.assertFalse(report["market_open"])
        self.assertTrue(report["success"])
        self.assertTrue(any("MT5_BROKER_UTC_OFFSET" in warning for warning in report["warnings"]))

    def test_healthcheck_reports_missing_terminal_without_raising(self):
        with (
            patch(
                "paper_trading.mt5_healthcheck.load_config",
                side_effect=MT5ConnectorError("MT5_LOGIN is required"),
            ),
            patch("paper_trading.mt5_healthcheck.mt5_connector.shutdown_connection"),
        ):
            report = run_healthcheck()
        self.assertFalse(report["connected"])
        self.assertFalse(report["success"])
        self.assertIn("MT5_LOGIN is required", report["errors"])

    def test_price_feed_returns_bid_ask_spread_and_closed_bars(self):
        self.connect()
        tick = get_current_tick()
        self.assertEqual(tick["bid"], 1.1)
        self.assertEqual(tick["ask"], 1.10012)
        self.assertAlmostEqual(get_current_spread(), 1.2)

        latest = get_latest_m5_bar()
        self.assertTrue(latest["timestamp"].endswith("+02:00"))
        self.assertEqual(self.fake.rates_args, ("EURUSD", self.fake.TIMEFRAME_M5, 1, 1))

        bars = get_recent_m5_bars()
        self.assertEqual(len(bars), 100)
        self.assertEqual(
            self.fake.rates_args,
            ("EURUSD", self.fake.TIMEFRAME_M5, 1, 100),
        )
        self.assertLess(bars[0]["timestamp"], bars[-1]["timestamp"])
        self.assertFalse(hasattr(self.fake, "order_send"))

    def test_price_feed_rejects_missing_or_invalid_quote_and_bad_count(self):
        self.connect()
        self.fake.tick.ask = 0
        with self.assertRaisesRegex(MT5ConnectorError, "invalid bid/ask"):
            get_current_tick()
        with self.assertRaisesRegex(ValueError, "positive integer"):
            get_recent_m5_bars(count=0)
        self.fake.tick.ask = 1.10012
        self.fake.tick.time -= 1000
        tick = get_current_tick()
        self.assertFalse(tick["time_within_clock_tolerance"])


if __name__ == "__main__":
    unittest.main()
