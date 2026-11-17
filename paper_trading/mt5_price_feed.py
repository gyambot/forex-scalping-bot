"""Read-only EURUSD MT5 tick and completed M5 bar access."""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any

from paper_trading.broker_time import epoch_to_broker_time, parse_broker_timezone
from paper_trading.mt5_connector import (
    MAX_TICK_AGE_SECONDS,
    MT5ConnectorError,
    _last_error,
    _require_connection,
    verify_symbol,
)


DEFAULT_SYMBOL = "EURUSD"
EURUSD_PIP_SIZE = 0.0001
DEFAULT_BAR_COUNT = 100


def get_current_tick(symbol: str = DEFAULT_SYMBOL) -> dict[str, float | int | str]:
    """Return the latest bid/ask tick tagged with the configured broker offset."""
    module, config = _require_connection()
    verify_symbol(symbol)
    tick = module.symbol_info_tick(symbol)
    if tick is None:
        raise MT5ConnectorError(f"MT5 quote for {symbol!r} is unavailable: {_last_error(module)}")
    bid = float(getattr(tick, "bid", 0.0))
    ask = float(getattr(tick, "ask", 0.0))
    if not (math.isfinite(bid) and math.isfinite(ask) and bid > 0 and ask >= bid):
        raise MT5ConnectorError(f"MT5 returned an invalid bid/ask quote for {symbol!r}")
    tick_time = int(getattr(tick, "time", 0))
    tick_time_msc = int(getattr(tick, "time_msc", tick_time * 1000))
    if tick_time <= 0:
        raise MT5ConnectorError(f"MT5 quote for {symbol!r} has no valid timestamp")
    tick_clock = epoch_to_broker_time(tick_time, config.broker_utc_offset)
    now_clock = datetime.now(parse_broker_timezone(config.broker_utc_offset))
    quote_age = (
        now_clock.replace(tzinfo=None) - tick_clock.replace(tzinfo=None)
    ).total_seconds()
    return {
        "symbol": symbol,
        "bid": bid,
        "ask": ask,
        "time": tick_clock.isoformat(),
        "time_broker": tick_clock.isoformat(),
        "time_epoch": tick_time,
        "time_msc": tick_time_msc,
        "clock_skew_seconds": round(-quote_age, 3),
        "time_within_clock_tolerance": (
            0 <= quote_age <= MAX_TICK_AGE_SECONDS
        ),
    }


def get_current_spread(symbol: str = DEFAULT_SYMBOL) -> float:
    """Return the observed bid/ask spread in EURUSD pips."""
    tick = get_current_tick(symbol)
    return round((float(tick["ask"]) - float(tick["bid"])) / EURUSD_PIP_SIZE, 5)


def _field(rate: Any, name: str) -> Any:
    try:
        return rate[name]
    except (KeyError, TypeError, IndexError):
        return getattr(rate, name)


def _normalize_bar(rate: Any, broker_utc_offset: str) -> dict[str, Any]:
    timestamp = int(_field(rate, "time"))
    if timestamp <= 0:
        raise MT5ConnectorError("MT5 returned an M5 bar without a valid timestamp")
    bar_time = epoch_to_broker_time(timestamp, broker_utc_offset)
    if bar_time.minute % 5 or bar_time.second or bar_time.microsecond:
        raise MT5ConnectorError("MT5 returned a bar timestamp not aligned to an M5 boundary")
    bar: dict[str, Any] = {
        "timestamp": bar_time.isoformat(),
    }
    for name in ("open", "high", "low", "close"):
        value = float(_field(rate, name))
        if not math.isfinite(value) or value <= 0:
            raise MT5ConnectorError(f"MT5 returned an invalid M5 {name} price")
        bar[name] = value
    if bar["high"] < max(bar["open"], bar["close"], bar["low"]):
        raise MT5ConnectorError("MT5 returned an internally inconsistent M5 bar")
    if bar["low"] > min(bar["open"], bar["close"], bar["high"]):
        raise MT5ConnectorError("MT5 returned an internally inconsistent M5 bar")
    for optional in ("tick_volume", "spread", "real_volume"):
        try:
            bar[optional] = int(_field(rate, optional))
        except (KeyError, TypeError, IndexError, AttributeError):
            pass
    return bar


def get_recent_m5_bars(
    count: int = DEFAULT_BAR_COUNT,
    symbol: str = DEFAULT_SYMBOL,
) -> list[dict[str, Any]]:
    """Return completed M5 bars oldest first with explicit broker-time offsets."""
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise ValueError("count must be a positive integer")
    module, config = _require_connection()
    verify_symbol(symbol)
    rates = module.copy_rates_from_pos(symbol, module.TIMEFRAME_M5, 1, count)
    if rates is None:
        raise MT5ConnectorError(f"MT5 M5 bar retrieval failed: {_last_error(module)}")
    ordered_rates = sorted(rates, key=lambda rate: int(_field(rate, "time")))
    bars = [
        _normalize_bar(rate, config.broker_utc_offset) for rate in ordered_rates
    ]
    timestamps = [bar["timestamp"] for bar in bars]
    if len(set(timestamps)) != len(timestamps):
        raise MT5ConnectorError("MT5 returned duplicate M5 bar timestamps")
    if len(bars) != count:
        raise MT5ConnectorError(
            f"MT5 returned {len(bars)} completed M5 bars; {count} were requested"
        )
    return bars


def get_latest_m5_bar(symbol: str = DEFAULT_SYMBOL) -> dict[str, Any]:
    """Return the latest fully closed M5 bar, never the currently forming bar."""
    return get_recent_m5_bars(count=1, symbol=symbol)[0]
