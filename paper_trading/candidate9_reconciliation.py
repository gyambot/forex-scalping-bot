"""Reconcile candidate 9 deal evidence without accessing or mutating MT5."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from paper_trading.candidate9_safeguard_model import SafeguardError


@dataclass(frozen=True)
class Deal:
    ticket: int
    order_ticket: int
    position_id: int
    magic: int
    symbol: str
    side: str
    phase: str
    time: datetime
    volume: Decimal
    price: Decimal
    profit: Decimal
    commission: Decimal
    swap: Decimal
    fee: Decimal
    reason: str


@dataclass(frozen=True)
class ExpectedTrade:
    order_ticket: int
    position_id: int
    magic: int
    direction: str
    volume: Decimal
    intended_entry: Decimal
    risk_cash: Decimal


@dataclass(frozen=True)
class ReconciledTrade:
    entry_price: Decimal
    exit_price: Decimal
    net_cash: Decimal
    pnl_r: Decimal
    adverse_slippage_pips: Decimal
    entry_time: datetime
    exit_time: datetime
    exit_reason: str


def _time(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise SafeguardError("deal timestamp must have an explicit offset")
    return value.astimezone(timezone.utc)


def reconcile(expected: ExpectedTrade, deals: list[Deal], *,
              position_is_closed: bool, internal_order_ticket: int) -> ReconciledTrade:
    """Validate all partial fills, identity, closure and costs against recorded intent."""
    if position_is_closed is not True:
        raise SafeguardError("position closure is unverified")
    if (expected.direction not in ("long", "short")
            or any(type(x) is not int or x <= 0 for x in
                   (expected.order_ticket, expected.position_id, expected.magic))
            or internal_order_ticket != expected.order_ticket):
        raise SafeguardError("invalid or inconsistent internal order identity")
    for number in (expected.volume, expected.intended_entry, expected.risk_cash):
        if not isinstance(number, Decimal) or not number.is_finite() or number <= 0:
            raise SafeguardError("invalid volume, intended entry or cash risk")
    if not deals or len({d.ticket for d in deals}) != len(deals):
        raise SafeguardError("missing or duplicate deals")
    entry_side = "buy" if expected.direction == "long" else "sell"
    exit_side = "sell" if entry_side == "buy" else "buy"
    for deal in deals:
        if (type(deal.ticket) is not int or deal.ticket <= 0
                or type(deal.order_ticket) is not int or deal.order_ticket <= 0
                or deal.position_id != expected.position_id
                or deal.symbol != "EURUSD" or deal.phase not in ("entry", "exit")):
            raise SafeguardError("deal identity, symbol or phase mismatch")
        if deal.side != (entry_side if deal.phase == "entry" else exit_side):
            raise SafeguardError("deal direction mismatch")
        if deal.phase == "entry" and (deal.order_ticket != expected.order_ticket or deal.magic != expected.magic):
            raise SafeguardError("entry provenance mismatch")
        for value in (deal.volume, deal.price, deal.profit, deal.commission, deal.swap, deal.fee):
            if not isinstance(value, Decimal) or not value.is_finite():
                raise SafeguardError("deal contains missing or invalid values")
        if deal.volume <= 0 or deal.price <= 0:
            raise SafeguardError("deal has invalid volume or price")
        if not isinstance(deal.reason, str) or not deal.reason:
            raise SafeguardError("deal reason unavailable")
        _time(deal.time)
    entries = [d for d in deals if d.phase == "entry"]
    exits = [d for d in deals if d.phase == "exit"]
    if not entries or not exits:
        raise SafeguardError("entry and exit deals both required")
    entry_volume = sum((d.volume for d in entries), Decimal(0))
    exit_volume = sum((d.volume for d in exits), Decimal(0))
    if entry_volume != expected.volume or exit_volume != expected.volume:
        raise SafeguardError("position is partially filled or not fully closed")
    if max(_time(d.time) for d in entries) > min(_time(d.time) for d in exits):
        raise SafeguardError("exit precedes completion of entry fills")
    entry = sum((d.price * d.volume for d in entries), Decimal(0)) / entry_volume
    exit_price = sum((d.price * d.volume for d in exits), Decimal(0)) / exit_volume
    cash = sum((d.profit + d.commission + d.swap + d.fee for d in deals), Decimal(0))
    slip = (entry - expected.intended_entry) if expected.direction == "long" else (expected.intended_entry - entry)
    reasons = {d.reason for d in exits}
    return ReconciledTrade(entry, exit_price, cash, cash / expected.risk_cash,
                           slip / Decimal("0.0001"), min(_time(d.time) for d in entries),
                           max(_time(d.time) for d in exits),
                           next(iter(reasons)) if len(reasons) == 1 else "multiple_exit_reasons")
