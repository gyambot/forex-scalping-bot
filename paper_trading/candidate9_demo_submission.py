"""Candidate 9 submission boundary. Disabled by default; no MT5 connection code.

The caller supplies an already-connected MT5-like module and must independently
establish the cash-risk and daily-P&L inputs. This is not a complete executor.
"""

from __future__ import annotations

import json
import sqlite3
import time
from contextlib import closing
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

from paper_trading.candidate9_broker_observation import observe_broker
from paper_trading.candidate9_lifecycle_simulation import (
    SimulatedSnapshot, _db, _expected, _kill_exists, _move, _record_reconciled,
    _time, begin,
)
from paper_trading.candidate9_mt5_history import read_closed_trade
from paper_trading.candidate9_order_preview import interpret_result, preview_order
from paper_trading.candidate9_position_watch import ExpectedPosition, observe_position
from paper_trading.candidate9_risk import BrokerConstraints
from paper_trading.candidate9_safeguard_model import SafeguardError
from scripts.backtest import Bar

PROJECT_KILL_SWITCH = Path(__file__).with_name("KILL_SWITCH.txt")
EXECUTION_INHIBITED = True


def _failure(db: sqlite3.Connection, now: datetime, reason: str, detail: str) -> str:
    db.execute("UPDATE study SET failures=failures+1 WHERE id=1")
    _move(db, now, "MANUAL_REVIEW_REQUIRED", reason)
    db.execute("UPDATE events SET reason=? WHERE id=(SELECT MAX(id) FROM events)",
               (f"{reason}: {detail}",))
    return "MANUAL_REVIEW_REQUIRED"


def _failure_reason(exc: Exception, fallback: str) -> str:
    allowed = {
        "KILL_SWITCH_TRIGGERED", "VALIDATION_EXPIRED", "SHUTDOWN_DAILY_LOSS",
        "BROKER_HEALTH_FAILURE", "UNEXPECTED_OPEN_POSITION", "UNEXPECTED_PENDING_ORDER",
        "PROTECTION_FAILURE", "HIGH_SPREAD_DURING_POSITION",
        "SIGNAL_SKIPPED_HIGH_SPREAD", "SIGNAL_SKIPPED_EXTREME_GAP",
    }
    return str(exc) if isinstance(exc, SafeguardError) and str(exc) in allowed else fallback


def _broker_constraints(module: Any, configured: BrokerConstraints) -> None:
    info = module.symbol_info("EURUSD")
    if info is None:
        raise SafeguardError("symbol constraints unavailable")
    try:
        tick = Decimal(str(info.trade_tick_size))
        stop = Decimal(str(info.trade_stops_level)) * Decimal(str(info.point))
        minimum = Decimal(str(info.volume_min))
        maximum = Decimal(str(info.volume_max))
        step = Decimal(str(info.volume_step))
    except (AttributeError, ArithmeticError, ValueError, TypeError) as exc:
        raise SafeguardError("invalid broker symbol constraints") from exc
    if (not all(x.is_finite() for x in (tick, stop, minimum, maximum, step))
            or tick != configured.tick_size or stop != configured.min_stop_distance
            or minimum != configured.min_volume or maximum != configured.max_volume
            or step != configured.volume_step):
        raise SafeguardError("configured symbol constraints disagree with broker")


def _daily_loss(module: Any, now: datetime, risk_budget: Decimal) -> Decimal:
    """Conservative closed-deal cash P&L for the UTC day; no silent defaults."""
    now = _time(now)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    deals = module.history_deals_get(midnight, now)
    if deals is None:
        raise SafeguardError("daily account history unavailable")
    buy, sell = getattr(module, "DEAL_TYPE_BUY", None), getattr(module, "DEAL_TYPE_SELL", None)
    if type(buy) is not int or type(sell) is not int or buy == sell:
        raise SafeguardError("daily history deal types unavailable")
    total = Decimal(0)
    for deal in deals:
        try:
            epoch = deal.time_msc
            if type(deal.type) is not int or deal.type not in (buy, sell):
                raise ValueError("unsupported non-trading account deal")
            if type(epoch) is not int or epoch <= 0:
                raise ValueError("invalid deal time")
            timestamp = datetime.fromtimestamp(epoch / 1000, tz=timezone.utc)
            numbers = tuple(Decimal(str(getattr(deal, name)))
                            for name in ("profit", "commission", "swap", "fee"))
        except (AttributeError, ArithmeticError, TypeError, ValueError, OverflowError, OSError) as exc:
            raise SafeguardError("invalid daily account deal") from exc
        if not midnight <= timestamp <= now or any(not item.is_finite() for item in numbers):
            raise SafeguardError("invalid daily account deal")
        total += sum(numbers, Decimal(0))
    if not isinstance(risk_budget, Decimal) or not risk_budget.is_finite() or risk_budget <= 0:
        raise SafeguardError("invalid risk budget")
    return total / risk_budget


def submit_once(
    path: Path, kill: Path, module: Any, *, enabled: bool = False,
    clock: Callable[[], datetime], expected_login: int, epoch_is_verified_utc: bool,
    friday: Bar, reopening: Bar, volume: Decimal, risk_budget: Decimal,
    costs_per_lot: Decimal, constraints: BrokerConstraints, magic: int,
) -> str:
    """Submit at most once after durable intent and fresh checks.

    Disabled or inhibited calls do not inspect the broker or mutate state. A successful
    response is only a pending verification, not proof of a protected fill.
    No recovery path retries a committed intent.
    """
    if enabled is not True or EXECUTION_INHIBITED:
        raise SafeguardError("candidate 9 submission is disarmed")
    now = _time(clock())
    try:
        killed = _kill_exists(PROJECT_KILL_SWITCH) or _kill_exists(kill)
    except OSError as exc:
        with closing(_db(path)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            return _failure(db, now, "KILL_SWITCH_CHECK_FAILURE", str(exc))
    if killed:
        with closing(_db(path)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            current = db.execute("SELECT state FROM study WHERE id=1").fetchone()[0]
            if current != "IDLE":
                raise SafeguardError("study is not idle")
            _move(db, now, "SHUTDOWN", "KILL_SWITCH_TRIGGERED")
        return "KILL_SWITCH_TRIGGERED"
    try:
        _broker_constraints(module, constraints)
        observation = observe_broker(module, now=now, expected_login=expected_login,
                                     epoch_is_verified_utc=epoch_is_verified_utc)
        daily = _daily_loss(module, now, risk_budget)
    except Exception as exc:
        with closing(_db(path)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            current = db.execute("SELECT state FROM study WHERE id=1").fetchone()[0]
            if current != "IDLE":
                raise SafeguardError("study is not idle") from exc
            return _failure(db, now, "BROKER_HEALTH_FAILURE", f"{type(exc).__name__}: {exc}")
    snapshot = SimulatedSnapshot(True, True, True, 0, 0,
                                 Decimal(str(observation.spread_pips)), daily)
    status = begin(path, now, kill, snapshot, friday, reopening,
                   bid=Decimal(str(observation.bid)), ask=Decimal(str(observation.ask)),
                   volume=volume, risk_budget=risk_budget, costs_per_lot=costs_per_lot,
                   constraints=constraints, magic=magic)
    if status != "ORDER_PENDING":
        return status
    with closing(_db(path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        current, raw, expiry = db.execute("SELECT state,intent,expires FROM study WHERE id=1").fetchone()
        if current != "ORDER_PENDING":
            raise SafeguardError("pending intent unavailable")
        db.execute("INSERT INTO validation_log VALUES(1,?,'')", (raw,))
        try:
            fresh = _time(clock())
            if fresh < now or fresh >= _time(datetime.fromisoformat(expiry)):
                raise SafeguardError("clock moved backward or validation expired")
            if _kill_exists(PROJECT_KILL_SWITCH) or _kill_exists(kill):
                raise SafeguardError("KILL_SWITCH_TRIGGERED")
            _broker_constraints(module, constraints)
            preview = preview_order(module, now=fresh, expected_login=expected_login,
                                    epoch_is_verified_utc=epoch_is_verified_utc,
                                    friday=friday, reopening=reopening, volume=volume,
                                    risk_budget=risk_budget, costs_per_lot=costs_per_lot,
                                    constraints=constraints, magic=magic)
            if _daily_loss(module, fresh, risk_budget) <= -1:
                raise SafeguardError("SHUTDOWN_DAILY_LOSS")
            intent = json.loads(raw)
            if (Decimal(str(preview.request["price"])) != Decimal(intent["entry"])
                    or Decimal(str(preview.request["sl"])) != Decimal(intent["stop"])
                    or Decimal(str(preview.request["tp"])) != Decimal(intent["target"])
                    or Decimal(str(preview.spread_pips)) != Decimal(intent["spread_pips"])):
                raise SafeguardError("quote or protection changed before submission")
            loss = module.order_calc_profit(preview.request["type"], "EURUSD", float(volume),
                                            float(preview.risk.entry), float(preview.risk.stop))
            loss = Decimal(str(loss))
            if (not loss.is_finite() or loss >= 0
                    or -loss + volume * costs_per_lot > risk_budget):
                raise SafeguardError("broker cash risk exceeds approved budget or is unavailable")
            if _kill_exists(PROJECT_KILL_SWITCH) or _kill_exists(kill):
                raise SafeguardError("KILL_SWITCH_TRIGGERED")
            last = _time(clock())
            if not fresh <= last <= fresh + timedelta(seconds=1):
                raise SafeguardError("submission check became stale")
        except Exception as exc:
            return _failure(db, now, _failure_reason(exc, "PRE_SUBMISSION_FAILURE"),
                            f"{type(exc).__name__}: {exc}")
        try:
            response = module.order_send(preview.request)
            result = interpret_result(module, response)
        except Exception as exc:
            return _failure(db, now, "SUBMISSION_UNKNOWN", f"{type(exc).__name__}: {exc}")
        if result.status == "REJECTED":
            db.execute("UPDATE study SET failures=failures+1 WHERE id=1")
            _move(db, now, "SHUTDOWN", "ORDER_REJECTED")
            return "SHUTDOWN"
        if result.status != "FILL_REQUIRES_VERIFICATION":
            return _failure(db, now, "SUBMISSION_UNKNOWN", "broker outcome not definitive")
        intent.update(order_ticket=result.order_ticket, deal_ticket=result.deal_ticket,
                      login=expected_login, epoch_is_verified_utc=epoch_is_verified_utc)
        db.execute("UPDATE study SET intent=? WHERE id=1", (json.dumps(intent, sort_keys=True),))
    return verify_fill(path, kill, module, now=_time(clock()))


def _position_spec(intent: dict) -> ExpectedPosition:
    return ExpectedPosition(intent["login"], intent["position_id"], intent["magic"],
                            intent["direction"], Decimal(intent["volume"]),
                            Decimal(intent["stop"]), Decimal(intent["target"]))


def verify_fill(path: Path, kill: Path, module: Any, *, now: datetime) -> str:
    """Verify an acknowledged fill against broker history and attached protection."""
    now = _time(now)
    with closing(_db(path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        current, raw = db.execute("SELECT state,intent FROM study WHERE id=1").fetchone()
        if current != "ORDER_PENDING":
            raise SafeguardError("no pending fill to verify")
        try:
            if _kill_exists(PROJECT_KILL_SWITCH) or _kill_exists(kill):
                raise SafeguardError("KILL_SWITCH_TRIGGERED")
            intent = json.loads(raw)
            order, ticket = intent["order_ticket"], intent["deal_ticket"]
            if type(order) is not int or order <= 0 or type(ticket) is not int or ticket <= 0:
                raise SafeguardError("fill identifiers unavailable")
            rows = module.history_deals_get(ticket=ticket)
            if rows is None or len(rows) != 1:
                raise SafeguardError("entry deal unavailable or ambiguous")
            deal = rows[0]
            direction = module.DEAL_TYPE_BUY if intent["direction"] == "long" else module.DEAL_TYPE_SELL
            timestamp = datetime.fromtimestamp(deal.time_msc / 1000, tz=timezone.utc)
            earliest = _time(datetime.fromisoformat(intent["signal_time"])) + timedelta(minutes=5)
            if (deal.ticket != ticket or deal.order != order or type(deal.position_id) is not int
                    or deal.position_id <= 0 or deal.magic != intent["magic"]
                    or deal.symbol != "EURUSD" or deal.entry != module.DEAL_ENTRY_IN
                    or deal.type != direction or Decimal(str(deal.volume)) != Decimal(intent["volume"])
                    or Decimal(str(deal.price)) != Decimal(intent["entry"])
                    or not earliest <= timestamp <= now):
                raise SafeguardError("entry deal does not match the committed intent")
            intent["position_id"] = deal.position_id
            risk = Decimal(intent["risk_budget"])
            daily = _daily_loss(module, now, risk)
            status = observe_position(module, _position_spec(intent), now=now,
                                      verified_utc=intent["epoch_is_verified_utc"],
                                      kill_switch=kill, daily_net_pnl_r=daily)
            if status != "POSITION_OBSERVED_NO_EXECUTION":
                raise SafeguardError(status)
            _check_floating_loss(module, intent, daily)
            db.execute("INSERT INTO execution_log VALUES(1,?,?)", (order, deal.position_id))
            db.execute("UPDATE study SET intent=? WHERE id=1", (json.dumps(intent, sort_keys=True),))
            _move(db, now, "POSITION_OPEN", "BROKER_FILL_AND_PROTECTION_VERIFIED")
        except Exception as exc:
            return _failure(db, now, _failure_reason(exc, "FILL_VERIFICATION_FAILURE"),
                            f"{type(exc).__name__}: {exc}")
    return "POSITION_OPEN"


def _check_floating_loss(module: Any, intent: dict, daily: Decimal) -> None:
    positions = module.positions_get()
    if positions is None or len(positions) != 1 or positions[0].identifier != intent["position_id"]:
        raise SafeguardError("position changed during daily loss check")
    floating = Decimal(str(positions[0].profit)) + Decimal(str(positions[0].swap))
    if not floating.is_finite() or daily + floating / Decimal(intent["risk_budget"]) <= -1:
        raise SafeguardError("SHUTDOWN_DAILY_LOSS")


def watch_once(path: Path, kill: Path, module: Any, *, now: datetime) -> str:
    """Poll one broker snapshot and reconcile a verified close, without repairing exposure."""
    now = _time(now)
    with closing(_db(path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        current, raw, expiry = db.execute("SELECT state,intent,expires FROM study WHERE id=1").fetchone()
        if current not in ("POSITION_OPEN", "POSITION_SUPERVISION"):
            raise SafeguardError("no verified position to supervise")
        try:
            intent = json.loads(raw)
            if _kill_exists(PROJECT_KILL_SWITCH) or _kill_exists(kill):
                raise SafeguardError("KILL_SWITCH_TRIGGERED")
            if now >= _time(datetime.fromisoformat(expiry)):
                raise SafeguardError("VALIDATION_EXPIRED")
            daily = _daily_loss(module, now, Decimal(intent["risk_budget"]))
            status = observe_position(module, _position_spec(intent), now=now,
                                      verified_utc=intent["epoch_is_verified_utc"],
                                      kill_switch=kill, daily_net_pnl_r=daily)
            if status not in ("POSITION_OBSERVED_NO_EXECUTION", "CLOSURE_RECONCILIATION_REQUIRED"):
                raise SafeguardError(status)
            if status == "POSITION_OBSERVED_NO_EXECUTION":
                _check_floating_loss(module, intent, daily)
                if current == "POSITION_OPEN":
                    _move(db, now, "POSITION_SUPERVISION", "PROTECTION_VERIFIED")
                return "POSITION_SUPERVISION"
            if current == "POSITION_OPEN":
                _move(db, now, "POSITION_SUPERVISION", "PROTECTION_PREVIOUSLY_VERIFIED")
            _move(db, now, "POSITION_CLOSED", "BROKER_FLAT_HISTORY_REQUIRED")
            execution = db.execute("SELECT order_ticket,position_id FROM execution_log WHERE id=1").fetchone()
            journal = db.execute("SELECT intent,result FROM validation_log WHERE id=1").fetchone()
            initial = dict(intent, order_ticket=None, position_id=None)
            for key in ("login", "deal_ticket", "epoch_is_verified_utc"):
                initial.pop(key)
            if (execution != (intent["order_ticket"], intent["position_id"])
                    or journal is None or journal[1] or json.loads(journal[0]) != initial):
                raise SafeguardError("execution record and validation journal disagree")
            trade = read_closed_trade(module, _expected(intent), now=now,
                                      expected_login=intent["login"],
                                      epoch_is_verified_utc=intent["epoch_is_verified_utc"],
                                      internal_order_ticket=execution[0],
                                      not_before=_time(datetime.fromisoformat(intent["signal_time"]))
                                      + timedelta(minutes=5))
            result = {key: str(value) for key, value in asdict(trade).items()}
            db.execute("UPDATE validation_log SET result=? WHERE id=1", (json.dumps(result, sort_keys=True),))
            _record_reconciled(db, now, intent, trade)
            return "SHUTDOWN"
        except Exception as exc:
            current = db.execute("SELECT state FROM study WHERE id=1").fetchone()[0]
            reason = "RECONCILIATION_FAILURE" if current == "POSITION_CLOSED" else "SUPERVISION_FAILURE"
            if reason == "SUPERVISION_FAILURE":
                reason = _failure_reason(exc, reason)
            return _failure(db, now, reason, f"{type(exc).__name__}: {exc}")


def supervise_until_shutdown(path: Path, kill: Path, module: Any, *,
                             clock: Callable[[], datetime],
                             stop_requested: Callable[[], bool],
                             sleep: Callable[[float], None] = time.sleep,
                             poll_seconds: float = 1.0) -> str:
    """Poll until closure or manual review. Stopping never closes exposure."""
    if not isinstance(poll_seconds, (int, float)) or not 0 < poll_seconds <= 1:
        raise SafeguardError("poll interval must be greater than zero and at most one second")
    while True:
        now = datetime.now(timezone.utc)
        try:
            now = _time(clock())
            stop = stop_requested()
            if type(stop) is not bool:
                raise SafeguardError("stop signal must be a boolean")
            if stop:
                with closing(_db(path)) as db, db:
                    db.execute("BEGIN IMMEDIATE")
                    current = db.execute("SELECT state FROM study WHERE id=1").fetchone()[0]
                    if current not in ("POSITION_OPEN", "POSITION_SUPERVISION"):
                        raise SafeguardError("no open position to supervise")
                    return _failure(db, now, "SUPERVISION_STOPPED", "manual intervention required")
            status = watch_once(path, kill, module, now=now)
            if status != "POSITION_SUPERVISION":
                return status
            sleep(poll_seconds)
        except Exception as exc:
            with closing(_db(path)) as db, db:
                db.execute("BEGIN IMMEDIATE")
                current = db.execute("SELECT state FROM study WHERE id=1").fetchone()[0]
                if current not in ("POSITION_OPEN", "POSITION_SUPERVISION"):
                    raise
                return _failure(db, now, "SUPERVISION_FAILURE", f"{type(exc).__name__}: {exc}")
