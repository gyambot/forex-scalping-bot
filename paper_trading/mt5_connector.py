"""Read-only connection and account validation for the IC Markets MT5 demo."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from paper_trading.broker_time import (
    DEFAULT_BROKER_UTC_OFFSET,
    epoch_to_broker_time,
    parse_broker_timezone,
)


EXPECTED_SERVER = "ICMarketsSC-Demo"
DEFAULT_ENV_FILE = Path(__file__).with_name(".env")
MAX_TICK_AGE_SECONDS = 120


class MT5ConnectorError(RuntimeError):
    """Raised when MT5 setup, connection, or validation fails."""


class MT5DependencyError(MT5ConnectorError):
    """Raised when the MetaTrader5 Python package is unavailable."""


@dataclass(frozen=True)
class MT5Config:
    login: int
    password: str | None = field(default=None, repr=False)
    server: str = EXPECTED_SERVER
    terminal_path: str | None = None
    broker_utc_offset: str = DEFAULT_BROKER_UTC_OFFSET


_mt5: Any | None = None
_config: MT5Config | None = None
_connected = False


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise MT5ConnectorError(f"Unable to read MT5 configuration file: {path}") from exc
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, separator, raw_value = line.partition("=")
        key = key.strip()
        if not separator or not key:
            raise MT5ConnectorError(
                f"Invalid MT5 configuration at {path}:{line_number}; expected KEY=VALUE"
            )
        value = raw_value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        elif " #" in value:
            value = value.partition(" #")[0].rstrip()
        values[key] = value
    return values


def load_config(
    env_file: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> MT5Config:
    """Load credentials from the environment, overriding a local .env file."""
    file_values = _read_env_file(env_file or DEFAULT_ENV_FILE)
    process_values = os.environ if environ is None else environ
    values = {**file_values, **process_values}

    raw_login = values.get("MT5_LOGIN", "").strip()
    password = values.get("MT5_PASSWORD", "").strip() or None
    server = values.get("MT5_SERVER", EXPECTED_SERVER).strip()
    terminal_path = values.get("MT5_TERMINAL_PATH", "").strip() or None
    broker_utc_offset = values.get(
        "MT5_BROKER_UTC_OFFSET", DEFAULT_BROKER_UTC_OFFSET
    ).strip()

    if not raw_login:
        raise MT5ConnectorError("MT5_LOGIN is required in the environment or local .env file")
    try:
        login = int(raw_login)
    except ValueError as exc:
        raise MT5ConnectorError("MT5_LOGIN must be a numeric account login") from exc
    if login <= 0:
        raise MT5ConnectorError("MT5_LOGIN must be a positive account login")
    if server != EXPECTED_SERVER:
        raise MT5ConnectorError(
            f"MT5_SERVER must be {EXPECTED_SERVER!r}; refusing any other server"
        )
    try:
        parse_broker_timezone(broker_utc_offset)
    except ValueError as exc:
        raise MT5ConnectorError(f"Invalid MT5_BROKER_UTC_OFFSET: {exc}") from exc
    if terminal_path and not Path(terminal_path).is_file():
        raise MT5ConnectorError("MT5_TERMINAL_PATH does not point to an existing terminal file")
    return MT5Config(
        login=login,
        password=password,
        server=server,
        terminal_path=terminal_path,
        broker_utc_offset=broker_utc_offset,
    )


def get_broker_utc_offset() -> str:
    """Return the configured source offset without requiring account credentials."""
    values = {**_read_env_file(DEFAULT_ENV_FILE), **os.environ}
    offset = values.get("MT5_BROKER_UTC_OFFSET", DEFAULT_BROKER_UTC_OFFSET).strip()
    try:
        parse_broker_timezone(offset)
    except ValueError as exc:
        raise MT5ConnectorError(f"Invalid MT5_BROKER_UTC_OFFSET: {exc}") from exc
    return offset


def _load_mt5() -> Any:
    try:
        import MetaTrader5
    except ImportError as exc:
        raise MT5DependencyError(
            "MetaTrader5 package is unavailable; install the official MetaTrader5 Python package"
        ) from exc
    return MetaTrader5


def _require_connection() -> tuple[Any, MT5Config]:
    if _mt5 is None or not _connected or _config is None:
        raise MT5ConnectorError("MT5 is not connected; call initialize_connection() first")
    return _mt5, _config


def _last_error(module: Any) -> str:
    try:
        error = module.last_error()
    except (AttributeError, RuntimeError):
        return "MT5 did not provide an error code"
    return f"MT5 error {error!r}"


def initialize_connection() -> bool:
    """Connect to the configured MT5 terminal and IC Markets demo server."""
    global _mt5, _config, _connected

    if _connected:
        verify_account()
        return True

    config = load_config()
    module = _load_mt5()
    _mt5 = module
    _config = config
    _connected = False

    if config.password:
        kwargs = {
            "login": config.login,
            "password": config.password,
            "server": config.server,
        }
        initialized = (
            module.initialize(config.terminal_path, **kwargs)
            if config.terminal_path
            else module.initialize(**kwargs)
        )
    else:
        initialized = (
            module.initialize(config.terminal_path)
            if config.terminal_path
            else module.initialize()
        )
    if not initialized:
        error = _last_error(module)
        shutdown_connection()
        raise MT5ConnectorError(
            f"Unable to initialize the configured MT5 demo terminal: {error}"
        )
    _connected = True
    try:
        verify_terminal_status()
        verify_account()
    except MT5ConnectorError:
        shutdown_connection()
        raise
    return True


def shutdown_connection() -> bool:
    """Gracefully disconnect from MT5; safe to call when already disconnected."""
    global _mt5, _config, _connected

    module = _mt5
    was_connected = _connected
    _connected = False
    _config = None
    _mt5 = None
    if module is None:
        return False
    try:
        module.shutdown()
    except (AttributeError, RuntimeError) as exc:
        raise MT5ConnectorError("MT5 terminal shutdown failed") from exc
    return was_connected


def verify_terminal_status() -> dict[str, Any]:
    """Return terminal connection and trade-permission state without changing it."""
    module, _ = _require_connection()
    terminal = module.terminal_info()
    if terminal is None:
        raise MT5ConnectorError(f"MT5 terminal status is unavailable: {_last_error(module)}")
    connected = bool(getattr(terminal, "connected", False))
    if not connected:
        raise MT5ConnectorError("MT5 terminal is not connected to its trade server")
    return {
        "connected": connected,
        "build": getattr(terminal, "build", None),
        "trade_allowed": bool(getattr(terminal, "trade_allowed", False)),
        "tradeapi_disabled": bool(getattr(terminal, "tradeapi_disabled", False)),
    }


def verify_account() -> Any:
    """Require the configured login and exact IC Markets demo server."""
    module, config = _require_connection()
    account = module.account_info()
    if account is None:
        raise MT5ConnectorError(f"MT5 account information is unavailable: {_last_error(module)}")
    actual_server = str(getattr(account, "server", ""))
    if actual_server != EXPECTED_SERVER or actual_server != config.server:
        raise MT5ConnectorError(
            f"Connected MT5 server is {actual_server!r}, expected {EXPECTED_SERVER!r}"
        )
    actual_login = int(getattr(account, "login", 0))
    if actual_login != config.login:
        raise MT5ConnectorError("Connected MT5 login does not match MT5_LOGIN")
    demo_mode = getattr(module, "ACCOUNT_TRADE_MODE_DEMO", 0)
    if getattr(account, "trade_mode", None) != demo_mode:
        raise MT5ConnectorError("Connected MT5 account is not a demo account")
    return account


def verify_trade_permissions() -> dict[str, bool]:
    """Read terminal/account trade permissions; this function never submits orders."""
    module, _ = _require_connection()
    terminal = module.terminal_info()
    account = module.account_info()
    if terminal is None or account is None:
        raise MT5ConnectorError(f"Unable to read MT5 trade permissions: {_last_error(module)}")
    terminal_allowed = bool(getattr(terminal, "trade_allowed", False))
    api_disabled = bool(getattr(terminal, "tradeapi_disabled", False))
    account_allowed = bool(getattr(account, "trade_allowed", False))
    expert_allowed = bool(getattr(account, "trade_expert", False))
    return {
        "terminal_trade_allowed": terminal_allowed,
        "terminal_api_disabled": api_disabled,
        "account_trade_allowed": account_allowed,
        "account_expert_allowed": expert_allowed,
        "permitted": terminal_allowed and not api_disabled and account_allowed and expert_allowed,
    }


def verify_symbol(symbol: str = "EURUSD") -> Any:
    """Make a symbol visible in Market Watch and verify it is available."""
    module, _ = _require_connection()
    info = module.symbol_info(symbol)
    if info is None:
        raise MT5ConnectorError(f"MT5 symbol {symbol!r} is unavailable: {_last_error(module)}")
    if not bool(getattr(info, "visible", False)):
        if not module.symbol_select(symbol, True):
            raise MT5ConnectorError(
                f"Unable to make MT5 symbol {symbol!r} visible: {_last_error(module)}"
            )
        info = module.symbol_info(symbol)
        if info is None or not bool(getattr(info, "visible", False)):
            raise MT5ConnectorError(f"MT5 symbol {symbol!r} did not become visible")
    return info


def verify_market_status(symbol: str = "EURUSD") -> dict[str, Any]:
    """Report whether a valid quote is available for a non-disabled symbol."""
    module, config = _require_connection()
    info = verify_symbol(symbol)
    tick = module.symbol_info_tick(symbol)
    if tick is None:
        raise MT5ConnectorError(f"MT5 quote for {symbol!r} is unavailable: {_last_error(module)}")
    bid = float(getattr(tick, "bid", 0.0))
    ask = float(getattr(tick, "ask", 0.0))
    quote_available = bid > 0 and ask >= bid
    disabled_mode = getattr(module, "SYMBOL_TRADE_MODE_DISABLED", 0)
    close_only_mode = getattr(module, "SYMBOL_TRADE_MODE_CLOSEONLY", 3)
    trade_mode = getattr(info, "trade_mode", disabled_mode)
    market_open = quote_available and trade_mode not in {disabled_mode, close_only_mode}
    tick_time = int(getattr(tick, "time", 0))
    broker_timezone = parse_broker_timezone(config.broker_utc_offset)
    tick_time_broker = (
        epoch_to_broker_time(tick_time, config.broker_utc_offset).isoformat()
        if tick_time > 0
        else None
    )
    quote_age_seconds = None
    if tick_time > 0:
        tick_clock = epoch_to_broker_time(tick_time, config.broker_utc_offset)
        now_clock = datetime.now(broker_timezone)
        quote_age_seconds = (
            now_clock.replace(tzinfo=None) - tick_clock.replace(tzinfo=None)
        ).total_seconds()
    quote_fresh = (
        quote_age_seconds is not None
        and 0 <= quote_age_seconds <= MAX_TICK_AGE_SECONDS
    )
    market_open = market_open and quote_fresh
    return {
        "symbol": symbol,
        "market_open": market_open,
        "quote_available": quote_available,
        "quote_fresh": quote_fresh,
        "quote_age_seconds": quote_age_seconds,
        "trade_mode": trade_mode,
        "bid": bid,
        "ask": ask,
        "tick_time_broker": tick_time_broker,
    }
