"""Candidate 9 read-only preflight; never sends, modifies or closes an order."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from paper_trading.candidate9_broker_observation import (
    BrokerObservation,
    WeekendSignal,
    derive_weekend_signal,
    observe_broker,
)
from paper_trading.candidate9_risk import BrokerConstraints, PreparedRisk, prepare_risk
from paper_trading.candidate9_safeguard_model import SafeguardError, Snapshot, check_model
from paper_trading.candidate9_validation_journal import recover, shutdown
from scripts.backtest import Bar


@dataclass(frozen=True)
class PreflightResult:
    status: str
    observation: BrokerObservation | None = None
    signal: WeekendSignal | None = None
    risk: PreparedRisk | None = None


def _is_killed(kill_switch: Path) -> bool:
    try:
        kill_switch.stat()
    except FileNotFoundError:
        return False
    return True


def inspect_candidate(
    *, module: Any, model_path: Path, journal_path: Path, kill_switch: Path,
    now: datetime, expected_login: int, epoch_is_verified_utc: bool,
    friday: Bar, reopening: Bar, daily_net_pnl_r: float, volume: Decimal,
    risk_budget: Decimal, costs_per_lot: Decimal, constraints: BrokerConstraints,
    max_entry_delay: timedelta = timedelta(seconds=5),
) -> PreflightResult:
    """Run isolated checks only; caller-supplied data is not execution evidence.

    The result cannot be used as authority to trade. No submission method is
    called, and no intent is recorded.
    """
    if now.tzinfo is None or now.utcoffset() is None:
        raise SafeguardError("explicit-offset timestamp required")
    now = now.astimezone(timezone.utc)
    if max_entry_delay <= timedelta(0) or max_entry_delay > timedelta(minutes=5):
        raise SafeguardError("invalid maximum entry delay")
    status = recover(journal_path, now)
    if status != "IDLE_NO_EXECUTION":
        return PreflightResult(status)
    if _is_killed(kill_switch):
        shutdown(journal_path, now, "KILL_SWITCH_TRIGGERED")
        return PreflightResult("KILL_SWITCH_TRIGGERED")
    signal = derive_weekend_signal(friday, reopening, observed_at=now)
    if signal.direction is None:
        return PreflightResult("NO_SIGNAL", signal=signal)
    if not signal.nominal_entry_time <= now <= signal.nominal_entry_time + max_entry_delay:
        return PreflightResult("SIGNAL_MISSED", signal=signal)
    try:
        observation = observe_broker(module, now=now, expected_login=expected_login,
                                     epoch_is_verified_utc=epoch_is_verified_utc)
    except (RuntimeError, OSError) as exc:
        message = str(exc)
        if message.startswith("UNEXPECTED_OPEN_POSITION"):
            reason = "UNEXPECTED_OPEN_POSITION"
        elif message.startswith("UNEXPECTED_PENDING_ORDER"):
            reason = "UNEXPECTED_PENDING_ORDER"
        else:
            reason = "BROKER_HEALTH_FAILURE"
        shutdown(journal_path, now, reason)
        return PreflightResult(reason, signal=signal)
    snapshot = Snapshot(True, True, True, True, True, True, observation.positions,
                        observation.pending_orders, daily_net_pnl_r,
                        observation.spread_pips, signal.gap_pips)
    status = check_model(model_path, kill_switch, now, snapshot)
    if status != "MODEL_CHECKS_PASSED_NO_EXECUTION":
        if status not in ("SIGNAL_SKIPPED_HIGH_SPREAD", "SIGNAL_SKIPPED_EXTREME_GAP"):
            shutdown(journal_path, now, status)
        return PreflightResult(status, observation, signal)
    try:
        risk = prepare_risk(signal.direction, Decimal(str(observation.bid)), Decimal(str(observation.ask)),
                            volume, risk_budget, costs_per_lot, constraints)
    except SafeguardError:
        shutdown(journal_path, now, "RISK_CHECK_FAILURE")
        raise
    return PreflightResult("READ_ONLY_CHECKS_PASSED_NO_EXECUTION", observation, signal, risk)
