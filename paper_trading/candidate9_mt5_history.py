"""Read-only MT5 deal-history adapter for candidate 9.

The caller supplies an already-connected module. This module never connects,
submits an order, changes protection, writes a trade log, or arms a strategy.
"""

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from paper_trading.candidate9_broker_observation import observe_broker
from paper_trading.candidate9_reconciliation import Deal, ExpectedTrade, ReconciledTrade, reconcile
from paper_trading.candidate9_safeguard_model import SafeguardError


def _integer(item: Any, name: str, *, positive: bool = False) -> int:
    value = getattr(item, name, None)
    if type(value) is not int or (positive and value <= 0):
        raise SafeguardError(f"broker deal has invalid {name}")
    return value


def _decimal(item: Any, name: str) -> Decimal:
    value = getattr(item, name, None)
    if value is None or isinstance(value, bool):
        raise SafeguardError(f"broker deal is missing {name}")
    try:
        converted = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise SafeguardError(f"broker deal has invalid {name}") from exc
    if not converted.is_finite():
        raise SafeguardError(f"broker deal has invalid {name}")
    return converted


def _constant(module: Any, name: str) -> int:
    value = getattr(module, name, None)
    if type(value) is not int:
        raise SafeguardError(f"broker constant {name} is unavailable")
    return value


def read_closed_trade(
    module: Any, expected: ExpectedTrade, *, now: datetime, expected_login: int,
    epoch_is_verified_utc: bool, internal_order_ticket: int, not_before: datetime,
) -> ReconciledTrade:
    """Reconcile a flat account's broker deals against a separately recorded order.

    A fresh quote and verified UTC timestamp semantics are required. The caller
    must obtain the expected order, position and risk independently from durable
    execution records; this adapter cannot itself prove the record's provenance.
    """
    if (not isinstance(not_before, datetime) or not_before.tzinfo is None
            or not_before.utcoffset() is None):
        raise SafeguardError("earliest execution time requires an explicit offset")
    not_before = not_before.astimezone(timezone.utc)
    observe_broker(module, now=now, expected_login=expected_login,
                   epoch_is_verified_utc=epoch_is_verified_utc)
    entry_code = _constant(module, "DEAL_ENTRY_IN")
    exit_code = _constant(module, "DEAL_ENTRY_OUT")
    buy_code = _constant(module, "DEAL_TYPE_BUY")
    sell_code = _constant(module, "DEAL_TYPE_SELL")
    stop_code = _constant(module, "DEAL_REASON_SL")
    target_code = _constant(module, "DEAL_REASON_TP")
    if entry_code == exit_code or buy_code == sell_code or stop_code == target_code:
        raise SafeguardError("broker deal constants are ambiguous")
    history = module.history_deals_get(position=expected.position_id)
    if history is None:
        raise SafeguardError("broker deal history unavailable")
    if not history:
        raise SafeguardError("broker deal history is empty")
    deals = []
    for row in history:
        entry = _integer(row, "entry")
        kind = _integer(row, "type")
        reason = _integer(row, "reason")
        if entry not in (entry_code, exit_code) or kind not in (buy_code, sell_code):
            raise SafeguardError("unsupported broker deal entry or type")
        epoch_ms = _integer(row, "time_msc", positive=True)
        try:
            stamp = datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc)
        except (OverflowError, OSError, ValueError) as exc:
            raise SafeguardError("invalid broker deal timestamp") from exc
        if stamp > now.astimezone(timezone.utc):
            raise SafeguardError("broker deal timestamp is in the future")
        if stamp < not_before:
            raise SafeguardError("broker deal predates the earliest permitted execution")
        symbol = getattr(row, "symbol", None)
        if not isinstance(symbol, str):
            raise SafeguardError("broker deal symbol unavailable")
        deals.append(Deal(
            _integer(row, "ticket", positive=True), _integer(row, "order", positive=True),
            _integer(row, "position_id", positive=True), _integer(row, "magic"),
            symbol, "buy" if kind == buy_code else "sell",
            "entry" if entry == entry_code else "exit", stamp,
            _decimal(row, "volume"), _decimal(row, "price"), _decimal(row, "profit"),
            _decimal(row, "commission"), _decimal(row, "swap"), _decimal(row, "fee"),
            "stop_loss" if reason == stop_code else "take_profit" if reason == target_code else "other",
        ))
    return reconcile(expected, deals, position_is_closed=True, internal_order_ticket=internal_order_ticket)
