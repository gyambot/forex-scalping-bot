"""Read-only broker observations for candidate 9; never connects or sends orders."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from paper_trading.candidate9_safeguard_model import SafeguardError
from paper_trading.mt5_connector import EXPECTED_SERVER
from scripts.backtest import BAR_DURATION, Bar, PIP_SIZE


@dataclass(frozen=True)
class BrokerObservation:
    bid: float
    ask: float
    quote_time: datetime
    spread_pips: float
    positions: int
    pending_orders: int


@dataclass(frozen=True)
class WeekendSignal:
    friday_close: float
    reopening_open: float
    gap_pips: float
    direction: str | None
    signal_bar_time: datetime
    nominal_entry_time: datetime


def _instant(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise SafeguardError("explicit-offset timestamp required")
    return value.astimezone(timezone.utc)


def observe_broker(module: Any, *, now: datetime, expected_login: int,
                   epoch_is_verified_utc: bool, max_age: timedelta = timedelta(seconds=5)) -> BrokerObservation:
    """Inspect an already-connected module; never initialize or modify MT5."""
    now = _instant(now)
    if epoch_is_verified_utc is not True:
        raise SafeguardError("BROKER_HEALTH_FAILURE: quote epoch semantics are unverified")
    if type(expected_login) is not int or expected_login <= 0 or max_age <= timedelta(0):
        raise SafeguardError("BROKER_HEALTH_FAILURE: invalid account or quote-age configuration")
    terminal = module.terminal_info()
    account = module.account_info()
    if terminal is None or account is None:
        raise SafeguardError("BROKER_HEALTH_FAILURE: account or terminal unavailable")
    if (getattr(terminal, "connected", None) is not True
            or getattr(terminal, "trade_allowed", None) is not True
            or getattr(terminal, "tradeapi_disabled", None) is not False
            or getattr(account, "trade_allowed", None) is not True
            or getattr(account, "trade_expert", None) is not True):
        raise SafeguardError("BROKER_HEALTH_FAILURE: terminal or account permissions unavailable")
    mode = getattr(module, "ACCOUNT_TRADE_MODE_DEMO", None)
    if (mode is None or getattr(account, "trade_mode", None) != mode
            or getattr(account, "server", None) != EXPECTED_SERVER
            or getattr(account, "login", None) != expected_login):
        raise SafeguardError("BROKER_HEALTH_FAILURE: account is not the expected demo account")
    symbol = module.symbol_info("EURUSD")
    full_mode = getattr(module, "SYMBOL_TRADE_MODE_FULL", None)
    if (symbol is None or full_mode is None or getattr(symbol, "visible", None) is not True
            or getattr(symbol, "trade_mode", None) != full_mode):
        raise SafeguardError("BROKER_HEALTH_FAILURE: EURUSD unavailable or not fully tradable")
    positions = module.positions_get()
    orders = module.orders_get()
    if positions is None or orders is None:
        raise SafeguardError("BROKER_HEALTH_FAILURE: positions or orders unavailable")
    if positions:
        raise SafeguardError("UNEXPECTED_OPEN_POSITION")
    if orders:
        raise SafeguardError("UNEXPECTED_PENDING_ORDER")
    tick = module.symbol_info_tick("EURUSD")
    if tick is None:
        raise SafeguardError("BROKER_HEALTH_FAILURE: quote unavailable")
    try:
        bid, ask = float(tick.bid), float(tick.ask)
        epoch_ms = int(tick.time_msc)
        quote_time = datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc)
    except (AttributeError, TypeError, ValueError, OverflowError, OSError) as exc:
        raise SafeguardError("BROKER_HEALTH_FAILURE: malformed quote") from exc
    if (not math.isfinite(bid) or not math.isfinite(ask) or bid <= 0 or ask < bid
            or epoch_ms <= 0 or not timedelta(0) <= now - quote_time <= max_age):
        raise SafeguardError("BROKER_HEALTH_FAILURE: invalid or stale quote")
    spread = (Decimal(str(ask)) - Decimal(str(bid))) / Decimal("0.0001")
    return BrokerObservation(bid, ask, quote_time, float(spread), len(positions), len(orders))


def derive_weekend_signal(friday: Bar, reopening: Bar, *, observed_at: datetime) -> WeekendSignal:
    """Apply the frozen candidate rule to two explicit-offset completed bid bars."""
    friday_time, reopening_time, now = _instant(friday.timestamp), _instant(reopening.timestamp), _instant(observed_at)
    for bar, stamp in ((friday, friday_time), (reopening, reopening_time)):
        if (stamp.second or stamp.microsecond or stamp.minute % 5
                or not all(math.isfinite(x) and x > 0 for x in (bar.open, bar.high, bar.low, bar.close))
                or bar.high < max(bar.open, bar.close, bar.low)
                or bar.low > min(bar.open, bar.close, bar.high)):
            raise SafeguardError("invalid M5 bar")
    if now < reopening_time + BAR_DURATION:
        raise SafeguardError("reopening bar has not completed")
    if friday_time.weekday() != 4 or reopening_time.weekday() not in (6, 0):
        raise SafeguardError("bar dates do not form the frozen weekend rule")
    if reopening_time - friday_time < timedelta(hours=36):
        raise SafeguardError("bar gap is shorter than 36 hours")
    gap = (reopening.open - friday.close) / PIP_SIZE
    direction = None
    if abs(reopening.open - friday.close) >= 5 * PIP_SIZE:
        direction = "short" if gap > 0 else "long"
    return WeekendSignal(friday.close, reopening.open, gap, direction,
                         reopening_time, reopening_time + BAR_DURATION)
