"""Read-only active-position checks; not an automated position manager."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from paper_trading.candidate9_safeguard_model import SafeguardError
from paper_trading.candidate9_validation_journal import shutdown
from paper_trading.mt5_connector import EXPECTED_SERVER


@dataclass(frozen=True)
class ExpectedPosition:
    login: int
    position_id: int
    magic: int
    direction: str
    volume: Decimal
    stop: Decimal
    target: Decimal


def _decimal(value: Any) -> Decimal:
    try:
        result = Decimal(str(value))
    except (ValueError, InvalidOperation) as exc:
        raise ValueError("broker position contains invalid numbers") from exc
    if not result.is_finite():
        raise ValueError("broker position contains invalid numbers")
    return result


def inspect_position(module: Any, expected: ExpectedPosition, *, now: datetime,
                     verified_utc: bool, kill_switch: Path, journal_path: Path,
                     daily_net_pnl_r: Decimal) -> str:
    """Check once and persist a shutdown on unsafe states; never modifies orders.

    The caller must independently verify the supplied daily P&L, and arrange
    polling and manual intervention. A detected shutdown does not flatten a
    position or cancel an order.
    """
    result = observe_position(module, expected, now=now, verified_utc=verified_utc,
                              kill_switch=kill_switch, daily_net_pnl_r=daily_net_pnl_r)
    if result not in ("POSITION_OBSERVED_NO_EXECUTION", "CLOSURE_RECONCILIATION_REQUIRED"):
        shutdown(journal_path, now, result)
    return result


def observe_position(module: Any, expected: ExpectedPosition, *, now: datetime,
                     verified_utc: bool, kill_switch: Path,
                     daily_net_pnl_r: Decimal) -> str:
    """Inspect one position without writing state or changing broker exposure."""
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise SafeguardError("explicit-offset timestamp required")
    now = now.astimezone(timezone.utc)
    if (expected.direction not in ("long", "short")
            or any(type(value) is not int or value <= 0
                   for value in (expected.login, expected.position_id, expected.magic))
            or any(not isinstance(value, Decimal) or not value.is_finite() or value <= 0
                   for value in (expected.volume, expected.stop, expected.target))):
        raise SafeguardError("invalid expected position")

    def halt(reason: str) -> str:
        return reason

    try:
        kill_switch.stat()
    except FileNotFoundError:
        pass
    except OSError:
        return halt("BROKER_HEALTH_FAILURE")
    else:
        return halt("KILL_SWITCH_TRIGGERED")
    if verified_utc is not True:
        return halt("BROKER_HEALTH_FAILURE")
    if not isinstance(daily_net_pnl_r, Decimal) or not daily_net_pnl_r.is_finite():
        return halt("BROKER_HEALTH_FAILURE")
    if daily_net_pnl_r <= -1:
        return halt("SHUTDOWN_DAILY_LOSS")
    try:
        terminal, account = module.terminal_info(), module.account_info()
        mode = getattr(module, "ACCOUNT_TRADE_MODE_DEMO", None)
        if (terminal is None or account is None or mode is None
                or getattr(terminal, "connected", None) is not True
                or getattr(terminal, "trade_allowed", None) is not True
                or getattr(terminal, "tradeapi_disabled", None) is not False
                or getattr(account, "trade_allowed", None) is not True
                or getattr(account, "trade_expert", None) is not True
                or getattr(account, "trade_mode", None) != mode
                or getattr(account, "server", None) != EXPECTED_SERVER
                or getattr(account, "login", None) != expected.login):
            return halt("BROKER_HEALTH_FAILURE")
        symbol = module.symbol_info("EURUSD")
        full_mode = getattr(module, "SYMBOL_TRADE_MODE_FULL", None)
        if (symbol is None or full_mode is None or getattr(symbol, "visible", None) is not True
                or getattr(symbol, "trade_mode", None) != full_mode):
            return halt("BROKER_HEALTH_FAILURE")
        positions, orders = module.positions_get(), module.orders_get()
        if positions is None or orders is None:
            return halt("BROKER_HEALTH_FAILURE")
        if orders:
            return halt("UNEXPECTED_PENDING_ORDER")
        tick = module.symbol_info_tick("EURUSD")
        if tick is None:
            return halt("BROKER_HEALTH_FAILURE")
        epoch = int(tick.time_msc)
        stamp = datetime.fromtimestamp(epoch / 1000, tz=timezone.utc)
        bid, ask = _decimal(tick.bid), _decimal(tick.ask)
        if epoch <= 0 or bid <= 0 or ask < bid or not timedelta(0) <= now - stamp <= timedelta(seconds=5):
            return halt("BROKER_HEALTH_FAILURE")
        if (ask - bid) / Decimal("0.0001") > Decimal("3"):
            return halt("HIGH_SPREAD_DURING_POSITION")
        if not positions:
            return "CLOSURE_RECONCILIATION_REQUIRED"
        if len(positions) != 1:
            return halt("UNEXPECTED_OPEN_POSITION")
        pos = positions[0]
        buy_type = getattr(module, "POSITION_TYPE_BUY", None)
        sell_type = getattr(module, "POSITION_TYPE_SELL", None)
        if buy_type is None or sell_type is None:
            return halt("BROKER_HEALTH_FAILURE")
        expected_type = buy_type if expected.direction == "long" else sell_type
        if (getattr(pos, "identifier", None) != expected.position_id
                or getattr(pos, "magic", None) != expected.magic
                or getattr(pos, "symbol", None) != "EURUSD"
                or getattr(pos, "type", None) != expected_type
                or _decimal(getattr(pos, "volume", None)) != expected.volume):
            return halt("UNEXPECTED_OPEN_POSITION")
        if (_decimal(getattr(pos, "sl", None)) != expected.stop
                or _decimal(getattr(pos, "tp", None)) != expected.target):
            return halt("PROTECTION_FAILURE")
    except (AttributeError, TypeError, ValueError, OverflowError, OSError, RuntimeError) as exc:
        if isinstance(exc, SafeguardError):
            raise
        return halt("BROKER_HEALTH_FAILURE")
    return "POSITION_OBSERVED_NO_EXECUTION"
