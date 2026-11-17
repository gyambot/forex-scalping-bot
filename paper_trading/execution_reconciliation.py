"""Reconcile MT5 position deals into the existing V1 demo-trade schema."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Any, Mapping, Sequence

from paper_trading.broker_time import epoch_to_broker_time, parse_broker_timestamp
from paper_trading.demo_trade_utils import PIP_SIZE, STOP_LOSS_PIPS


class ReconciliationError(ValueError):
    """Raised when broker history cannot safely produce a complete trade."""


def _value(item: Any, name: str, default: Any = None) -> Any:
    if isinstance(item, Mapping):
        return item.get(name, default)
    return getattr(item, name, default)


def _deal_time(deal: Any, broker_offset: str):
    time_msc = int(_value(deal, "time_msc", 0) or 0)
    if time_msc:
        timestamp = epoch_to_broker_time(time_msc // 1000, broker_offset)
        return timestamp.replace(microsecond=(time_msc % 1000) * 1000)
    seconds = int(_value(deal, "time", 0) or 0)
    if seconds <= 0:
        raise ReconciliationError("broker deal is missing a valid fill timestamp")
    return epoch_to_broker_time(seconds, broker_offset)


def build_trade_record(
    *,
    signal: Mapping[str, Any],
    entry_deals: Sequence[Any],
    exit_deals: Sequence[Any],
    symbol_info: Any,
    broker_offset: str,
    account_alias: str,
    intended_entry: float,
    entry_spread_pips: float,
    planned_entry_time: str,
    submission_time: str,
    fill_delay_ms: float,
    order_reference: str,
    entry_code: int,
    exit_codes: set[int],
    deal_buy_type: int,
    deal_sell_type: int,
    exit_reason_codes: Mapping[int, str] | None = None,
    expected_volume: float,
    expected_order_ticket: int,
    expected_magic: int,
    position_id: int,
) -> dict[str, str]:
    """Build one fully closed record; raises if fills/costs cannot be reconciled."""
    if not entry_deals or not exit_deals:
        raise ReconciliationError("position history must contain entry and exit deals")
    direction = str(signal["direction"]).lower()
    if direction not in {"long", "short"}:
        raise ReconciliationError("signal direction must be long or short")

    entries = sorted(entry_deals, key=lambda deal: int(_value(deal, "time_msc", 0) or 0))
    exits = sorted(exit_deals, key=lambda deal: int(_value(deal, "time_msc", 0) or 0))
    if any(int(_value(deal, "entry", -1)) != entry_code for deal in entries):
        raise ReconciliationError("entry history contains a non-entry deal")
    if any(int(_value(deal, "entry", -1)) not in exit_codes for deal in exits):
        raise ReconciliationError("exit history contains an unsupported exit deal")

    expected_volume_decimal = Decimal(str(expected_volume))
    if expected_volume_decimal <= 0 or expected_order_ticket <= 0 or position_id <= 0:
        raise ReconciliationError("executor order and volume references are invalid")
    all_deals = (*entries, *exits)
    for deal in all_deals:
        for field in ("profit", "commission", "swap", "fee"):
            raw = _value(deal, field)
            if raw is None:
                raise ReconciliationError(f"broker deal is missing {field}; costs cannot be reconciled")
            try:
                amount = Decimal(str(raw))
            except ArithmeticError as exc:
                raise ReconciliationError(f"broker deal has invalid {field}") from exc
            if not amount.is_finite():
                raise ReconciliationError(f"broker deal has invalid {field}")
    if any(int(_value(deal, "position_id", 0) or 0) != position_id for deal in all_deals):
        raise ReconciliationError("position history contains a deal for another position")
    if any(str(_value(deal, "symbol", "")) != str(signal.get("symbol", "EURUSD")) for deal in all_deals):
        raise ReconciliationError("position history contains a deal for another symbol")
    if any(
        int(_value(deal, "magic", -1)) != expected_magic
        or int(_value(deal, "order", 0) or 0) != expected_order_ticket
        for deal in entries
    ):
        raise ReconciliationError("entry deal provenance does not match the executor order")

    expected_entry_type = deal_buy_type if direction == "long" else deal_sell_type
    expected_exit_type = deal_sell_type if direction == "long" else deal_buy_type
    if any(int(_value(deal, "type", -1)) != expected_entry_type for deal in entries):
        raise ReconciliationError("entry deal direction conflicts with the signal")
    if any(int(_value(deal, "type", -1)) != expected_exit_type for deal in exits):
        raise ReconciliationError("exit deal direction conflicts with the signal")

    def weighted_price(deals: Sequence[Any], label: str) -> tuple[Decimal, Decimal]:
        total_volume = sum(
            (Decimal(str(_value(deal, "volume", 0))) for deal in deals), Decimal(0)
        )
        if total_volume <= 0:
            raise ReconciliationError(f"{label} deals have no positive volume")
        weighted = sum(
            (
                Decimal(str(_value(deal, "price", 0)))
                * Decimal(str(_value(deal, "volume", 0)))
                for deal in deals
            ),
            Decimal(0),
        )
        return weighted / total_volume, total_volume

    entry_price, entry_volume = weighted_price(entries, "entry")
    exit_price, exit_volume = weighted_price(exits, "exit")
    if entry_volume != expected_volume_decimal:
        raise ReconciliationError("entry volume does not match the configured executor volume")
    if exit_volume != expected_volume_decimal:
        raise ReconciliationError("position is not fully closed; exit volume differs")
    if entry_volume != exit_volume:
        raise ReconciliationError("position is not fully closed; entry/exit volumes differ")

    tick_size = Decimal(str(_value(symbol_info, "trade_tick_size", 0) or 0))
    tick_value = Decimal(str(_value(symbol_info, "trade_tick_value", 0) or 0))
    if tick_size <= 0 or tick_value <= 0:
        raise ReconciliationError(
            "symbol tick size/value is unavailable; cannot reconcile account costs to pips"
        )
    pip_value = tick_value * PIP_SIZE / tick_size * entry_volume
    if pip_value <= 0:
        raise ReconciliationError("calculated pip value is not positive")

    gross_cash = sum((Decimal(str(_value(deal, "profit", 0))) for deal in exits), Decimal(0))
    commission_cash = sum(
        (Decimal(str(_value(deal, "commission", 0))) for deal in (*entries, *exits)),
        Decimal(0),
    )
    financing_cash = sum(
        (Decimal(str(_value(deal, "swap", 0))) for deal in (*entries, *exits)),
        Decimal(0),
    )
    fee_cash = sum(
        (Decimal(str(_value(deal, "fee", 0))) for deal in (*entries, *exits)),
        Decimal(0),
    )
    net_cash = gross_cash + commission_cash + financing_cash + fee_cash
    gross_pips = gross_cash / pip_value
    commission_pips = (commission_cash + fee_cash) / pip_value
    financing_pips = financing_cash / pip_value
    net_pips = net_cash / pip_value

    actual_entry_time = _deal_time(entries[0], broker_offset)
    actual_exit_time = _deal_time(exits[-1], broker_offset)
    planned = parse_broker_timestamp(planned_entry_time, "planned_entry_time")
    submitted = parse_broker_timestamp(submission_time, "submission_time")
    if submitted < planned:
        raise ReconciliationError("submission time precedes the planned entry time")
    if actual_exit_time <= actual_entry_time:
        raise ReconciliationError("exit time must follow entry time")

    risk = PIP_SIZE * STOP_LOSS_PIPS
    target_distance = PIP_SIZE * Decimal("20")
    if direction == "long":
        stop = entry_price - risk
        target = entry_price + target_distance
        slippage = entry_price - Decimal(str(intended_entry))
    else:
        stop = entry_price + risk
        target = entry_price - target_distance
        slippage = Decimal(str(intended_entry)) - entry_price

    reason_map = exit_reason_codes or {}
    reasons = {
        reason_map.get(int(_value(deal, "reason", -1)), "other")
        for deal in exits
    }
    exit_reason = next(iter(reasons)) if len(reasons) == 1 else "multiple_exit_reasons"
    timestamps_exact = actual_entry_time == planned
    protective_exit = reasons in ({"stop_loss"}, {"take_profit"})
    rule_compliant = timestamps_exact and slippage == 0 and protective_exit
    symbol = str(signal.get("symbol", "EURUSD"))
    signal_bar_time = parse_broker_timestamp(
        str(signal["signal_bar_open_time_broker"]), "signal_bar_open_time_broker"
    )
    signal_time = signal_bar_time + timedelta(minutes=5)

    return {
        "trade_id": str(signal["trade_id"]),
        "strategy_version": "Breakout Scalping V1",
        "account_type": "DEMO",
        "account_alias": account_alias,
        "broker": "IC Markets MT5",
        "symbol": symbol,
        "timeframe": "M5",
        "signal_bar_open_time_broker": signal_bar_time.isoformat(),
        "signal_time_broker": signal_time.isoformat(),
        "entry_time_broker": actual_entry_time.isoformat(),
        "exit_time_broker": actual_exit_time.isoformat(),
        "direction": direction,
        "signal_close": str(signal["signal_close"]),
        "prior_20_high": str(signal["prior_20_high"]),
        "prior_20_low": str(signal["prior_20_low"]),
        "intended_entry": str(intended_entry),
        "actual_entry": str(entry_price),
        "stop_price": str(stop),
        "target_price": str(target),
        "actual_exit": str(exit_price),
        "entry_spread_pips": str(entry_spread_pips),
        "exit_spread_pips": "unavailable: broker exit quote was not captured",
        "gross_pnl_pips": str(gross_pips),
        "commission_pips": str(commission_pips),
        "financing_pips": str(financing_pips),
        "slippage_pips": str(slippage / PIP_SIZE),
        "pnl_pips": str(net_pips),
        "pnl_r": str(net_pips / STOP_LOSS_PIPS),
        "hold_minutes": str(
            Decimal(str((actual_exit_time - actual_entry_time).total_seconds())) / Decimal(60)
        ),
        "exit_reason": exit_reason,
        "order_reference": order_reference,
        "completed": "true",
        "rule_compliant": str(rule_compliant).lower(),
        "notes": (
            f"Automated demo reconciliation; planned={planned_entry_time}; "
            f"submitted={submission_time}; fill_delay_ms={fill_delay_ms}; "
            f"pip_value_account_currency={pip_value}; fee costs included with commission."
        ),
    }
