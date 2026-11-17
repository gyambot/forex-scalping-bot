"""Read-only MT5 request preview and result interpretation for candidate 9.

This module cannot submit an order or authorize execution. A request preview is
not permission to trade; its observations are stale as soon as they are read.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from paper_trading.candidate9_broker_observation import derive_weekend_signal, observe_broker
from paper_trading.candidate9_risk import BrokerConstraints, PreparedRisk, prepare_risk
from paper_trading.candidate9_safeguard_model import SafeguardError
from scripts.backtest import Bar


@dataclass(frozen=True)
class OrderPreview:
    request: dict[str, int | float | str]
    risk: PreparedRisk
    gap_pips: float
    spread_pips: float


@dataclass(frozen=True)
class InterpretedResult:
    status: str
    order_ticket: int | None = None
    deal_ticket: int | None = None


def _constant(module: Any, name: str) -> int:
    value = getattr(module, name, None)
    if type(value) is not int:
        raise SafeguardError(f"broker constant {name} is unavailable")
    return value


def preview_order(module: Any, *, now: datetime, expected_login: int,
                  epoch_is_verified_utc: bool, friday: Bar, reopening: Bar,
                  volume: Decimal, risk_budget: Decimal, costs_per_lot: Decimal,
                  constraints: BrokerConstraints, magic: int) -> OrderPreview:
    """Construct an unsubmitted request after read-only account and risk checks."""
    signal = derive_weekend_signal(friday, reopening, observed_at=now)
    if signal.direction is None:
        raise SafeguardError("NO_SIGNAL")
    if not signal.nominal_entry_time <= now <= signal.nominal_entry_time + timedelta(seconds=5):
        raise SafeguardError("SIGNAL_MISSED")
    if abs(signal.gap_pips) > 20:
        raise SafeguardError("SIGNAL_SKIPPED_EXTREME_GAP")
    if type(magic) is not int or magic <= 0:
        raise SafeguardError("INVALID_MAGIC")
    observation = observe_broker(module, now=now, expected_login=expected_login,
                                 epoch_is_verified_utc=epoch_is_verified_utc)
    if observation.spread_pips > 3:
        raise SafeguardError("SIGNAL_SKIPPED_HIGH_SPREAD")
    risk = prepare_risk(signal.direction, Decimal(str(observation.bid)),
                        Decimal(str(observation.ask)), volume, risk_budget,
                        costs_per_lot, constraints)
    symbol = module.symbol_info("EURUSD")
    modes = getattr(symbol, "filling_mode", None)
    fok_flag, ioc_flag = _constant(module, "SYMBOL_FILLING_FOK"), _constant(module, "SYMBOL_FILLING_IOC")
    if type(modes) is not int or fok_flag <= 0 or ioc_flag <= 0 or fok_flag & ioc_flag:
        raise SafeguardError("invalid broker filling modes")
    if modes & fok_flag:
        filling = _constant(module, "ORDER_FILLING_FOK")
    elif modes & ioc_flag:
        filling = _constant(module, "ORDER_FILLING_IOC")
    else:
        raise SafeguardError("no supported FOK/IOC market filling mode")
    request: dict[str, int | float | str] = {
        "action": _constant(module, "TRADE_ACTION_DEAL"),
        "symbol": "EURUSD",
        "volume": float(risk.volume),
        "type": _constant(module, "ORDER_TYPE_BUY" if signal.direction == "long" else "ORDER_TYPE_SELL"),
        "price": float(risk.entry),
        "sl": float(risk.stop),
        "tp": float(risk.target),
        "deviation": 0,
        "magic": magic,
        "comment": "candidate9-validation",
        "type_time": _constant(module, "ORDER_TIME_GTC"),
        "type_filling": filling,
    }
    return OrderPreview(request, risk, signal.gap_pips, observation.spread_pips)


def interpret_result(module: Any, result: Any) -> InterpretedResult:
    """Classify an MT5-like response; unknown and partial outcomes never retry."""
    done = _constant(module, "TRADE_RETCODE_DONE")
    rejection_codes = {
        _constant(module, "TRADE_RETCODE_REJECT"),
        _constant(module, "TRADE_RETCODE_INVALID"),
        _constant(module, "TRADE_RETCODE_INVALID_STOPS"),
        _constant(module, "TRADE_RETCODE_NO_MONEY"),
    }
    if done in rejection_codes or len(rejection_codes) != 4:
        raise SafeguardError("ambiguous broker result constants")
    code = getattr(result, "retcode", None)
    if type(code) is not int:
        return InterpretedResult("UNKNOWN")
    if code in rejection_codes:
        return InterpretedResult("REJECTED")
    if code != done:
        return InterpretedResult("UNKNOWN")
    order, deal = getattr(result, "order", None), getattr(result, "deal", None)
    if type(order) is not int or order <= 0 or type(deal) is not int or deal <= 0:
        return InterpretedResult("UNKNOWN")
    return InterpretedResult("FILL_REQUIRES_VERIFICATION", order, deal)
