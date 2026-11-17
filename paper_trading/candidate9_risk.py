"""Pure risk and broker-constraint checks; no broker or order interface."""

from dataclasses import dataclass
from decimal import Decimal

from paper_trading.candidate9_safeguard_model import SafeguardError


PIP = Decimal("0.0001")


@dataclass(frozen=True)
class BrokerConstraints:
    tick_size: Decimal
    min_stop_distance: Decimal
    min_volume: Decimal
    max_volume: Decimal
    volume_step: Decimal
    loss_per_lot_at_stop: Decimal


@dataclass(frozen=True)
class PreparedRisk:
    entry: Decimal
    stop: Decimal
    target: Decimal
    volume: Decimal
    modeled_loss: Decimal


def prepare_risk(direction: str, bid: Decimal, ask: Decimal, volume: Decimal,
                 risk_budget: Decimal, costs_per_lot: Decimal,
                 constraints: BrokerConstraints) -> PreparedRisk:
    """Validate fixed 10/20-pip levels and an explicitly configured demo volume.

    The supplied stop-loss estimate must be independently verified in account
    currency. Stops and estimated costs cannot guarantee a maximum realized loss.
    """
    if direction not in ("long", "short"):
        raise SafeguardError("direction must be long or short")
    numbers = (
        bid, ask, volume, risk_budget, costs_per_lot, constraints.tick_size,
        constraints.min_stop_distance, constraints.min_volume, constraints.max_volume,
        constraints.volume_step, constraints.loss_per_lot_at_stop,
    )
    if any(not isinstance(value, Decimal) or not value.is_finite() for value in numbers):
        raise SafeguardError("all risk inputs must be finite Decimal values")
    if (bid <= 0 or ask < bid or volume <= 0 or risk_budget <= 0 or costs_per_lot < 0
            or constraints.tick_size <= 0 or constraints.min_stop_distance < 0
            or constraints.min_volume <= 0 or constraints.max_volume < constraints.min_volume
            or constraints.volume_step <= 0 or constraints.loss_per_lot_at_stop <= 0):
        raise SafeguardError("invalid risk or broker constraints")
    if (volume < constraints.min_volume or volume > constraints.max_volume
            or (volume - constraints.min_volume) % constraints.volume_step != 0):
        raise SafeguardError("volume is outside broker limits or volume step")
    sign = 1 if direction == "long" else -1
    entry = ask if direction == "long" else bid
    stop = entry - sign * 10 * PIP
    target = entry + sign * 20 * PIP
    if stop <= 0 or target <= 0:
        raise SafeguardError("protective price is nonpositive")
    if any(price % constraints.tick_size != 0 for price in (entry, stop, target)):
        raise SafeguardError("entry or protective prices are not on the broker tick grid")
    # Broker protection is evaluated against the current close-side quote.
    close_side = bid if direction == "long" else ask
    if (sign * (close_side - stop) < constraints.min_stop_distance
            or sign * (target - close_side) < constraints.min_stop_distance):
        raise SafeguardError("protective prices violate broker minimum stop distance")
    modeled_loss = volume * (constraints.loss_per_lot_at_stop + costs_per_lot)
    if modeled_loss > risk_budget:
        raise SafeguardError("modeled stop loss and costs exceed approved 1R budget")
    return PreparedRisk(entry, stop, target, volume, modeled_loss)
