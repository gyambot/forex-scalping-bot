"""End-to-end candidate 9 simulation. This module cannot call a real broker.

The only accepted submission object is the concrete, in-memory SimulatedBroker
below. Nothing in this module initializes MT5 or submits a demo or live order.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from paper_trading.candidate9_lifecycle_simulation import (
    SimulatedPosition, SimulatedSnapshot, _db, _expected, _kill_exists, _move,
    _record_reconciled, _time, begin, restart, state, supervise,
)
from paper_trading.candidate9_reconciliation import Deal, reconcile
from paper_trading.candidate9_risk import BrokerConstraints
from paper_trading.candidate9_safeguard_model import SafeguardError
from scripts.backtest import Bar


@dataclass(frozen=True)
class SimulatedOrderResult:
    outcome: str
    order_ticket: int | None = None
    position_id: int | None = None


@dataclass(frozen=True)
class SupervisionSample:
    at: datetime
    snapshot: SimulatedSnapshot
    position: SimulatedPosition | None


class SimulatedBroker:
    """Scripted in-memory evidence, deliberately not an MT5 adapter."""

    def __init__(self, precheck: SimulatedSnapshot, before_submit: SimulatedSnapshot,
                 result: SimulatedOrderResult, deals: list[Deal]) -> None:
        self.precheck = precheck
        self.before_submit = before_submit
        self.result = result
        self.deals = list(deals)
        self.submit_calls = 0

    def submit(self) -> SimulatedOrderResult:
        self.submit_calls += 1
        if self.result.outcome == "exception":
            raise RuntimeError("scripted simulated submission exception")
        return self.result


def _failure(db: sqlite3.Connection, now: datetime, reason: str, detail: str) -> str:
    db.execute("UPDATE study SET failures=failures+1 WHERE id=1")
    _move(db, now, "MANUAL_REVIEW_REQUIRED", reason)
    db.execute("UPDATE events SET reason=? WHERE id=(SELECT MAX(id) FROM events)",
               (f"{reason}: {detail}",))
    return "MANUAL_REVIEW_REQUIRED"


def _ready(snapshot: SimulatedSnapshot, intended_spread: Decimal) -> str:
    if (snapshot.demo_verified is not True or snapshot.healthy is not True
            or snapshot.quote_fresh is not True
            or type(snapshot.positions) is not int or snapshot.positions < 0
            or type(snapshot.pending_orders) is not int or snapshot.pending_orders < 0
            or not isinstance(snapshot.daily_net_pnl_r, Decimal)
            or not snapshot.daily_net_pnl_r.is_finite()
            or not isinstance(snapshot.spread_pips, Decimal)
            or not snapshot.spread_pips.is_finite() or snapshot.spread_pips < 0):
        return "BROKER_HEALTH_FAILURE"
    if snapshot.positions:
        return "UNEXPECTED_OPEN_POSITION"
    if snapshot.pending_orders:
        return "UNEXPECTED_PENDING_ORDER"
    if snapshot.daily_net_pnl_r <= -1:
        return "SHUTDOWN_DAILY_LOSS"
    if snapshot.spread_pips > 3:
        return "SIGNAL_SKIPPED_HIGH_SPREAD"
    if snapshot.spread_pips != intended_spread:
        return "QUOTE_CHANGED"
    return ""


def start(path: Path, now: datetime, kill: Path, broker: SimulatedBroker,
          friday: Bar, reopening: Bar, *, bid: Decimal, ask: Decimal, volume: Decimal,
          risk_budget: Decimal, costs_per_lot: Decimal, constraints: BrokerConstraints,
          magic: int) -> str:
    """Commit intent, recheck, and invoke one strictly in-memory submission."""
    if type(broker) is not SimulatedBroker:
        raise SafeguardError("only the built-in simulated broker is permitted")
    now = _time(now)
    result = begin(path, now, kill, broker.precheck, friday, reopening, bid=bid, ask=ask,
                   volume=volume, risk_budget=risk_budget, costs_per_lot=costs_per_lot,
                   constraints=constraints, magic=magic)
    if result != "ORDER_PENDING":
        return result
    with closing(_db(path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        current, raw = db.execute("SELECT state,intent FROM study WHERE id=1").fetchone()
        if current != "ORDER_PENDING":
            raise SafeguardError("simulated pending intent changed")
        db.execute("INSERT INTO validation_log VALUES(1,?,'')", (raw,))
    with closing(_db(path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        current, raw, expiry = db.execute("SELECT state,intent,expires FROM study WHERE id=1").fetchone()
        if current != "ORDER_PENDING":
            raise SafeguardError("simulated pending intent changed")
        try:
            if _kill_exists(kill):
                return _failure(db, now, "KILL_SWITCH_TRIGGERED", "before simulated submission")
        except OSError as exc:
            return _failure(db, now, "BROKER_HEALTH_FAILURE", f"kill switch check: {exc}")
        if now >= _time(datetime.fromisoformat(expiry)):
            return _failure(db, now, "VALIDATION_EXPIRED", "before simulated submission")
        intent = json.loads(raw)
        reason = _ready(broker.before_submit, Decimal(intent["spread_pips"]))
        if reason:
            return _failure(db, now, reason, "before simulated submission")
        try:
            response = SimulatedBroker.submit(broker)
        except Exception as exc:
            return _failure(db, now, "SUBMISSION_UNKNOWN", f"{type(exc).__name__}: {exc}")
        if not isinstance(response, SimulatedOrderResult):
            return _failure(db, now, "SUBMISSION_UNKNOWN", "malformed response")
        if response.outcome == "rejected":
            db.execute("UPDATE study SET failures=failures+1 WHERE id=1")
            _move(db, now, "SHUTDOWN", "ORDER_REJECTED")
            return "SHUTDOWN"
        if (response.outcome != "accepted"
                or type(response.order_ticket) is not int or response.order_ticket <= 0
                or type(response.position_id) is not int or response.position_id <= 0):
            return _failure(db, now, "SUBMISSION_UNKNOWN", response.outcome)
        db.execute("INSERT INTO execution_log VALUES(1,?,?)",
                   (response.order_ticket, response.position_id))
        intent.update(order_ticket=response.order_ticket, position_id=response.position_id)
        db.execute("UPDATE study SET intent=? WHERE id=1", (json.dumps(intent, sort_keys=True),))
        _move(db, now, "POSITION_OPEN", "SIMULATED_ACCEPTED")
    return "POSITION_OPEN"


def watch(path: Path, now: datetime, kill: Path, snapshot: SimulatedSnapshot,
          position: SimulatedPosition | None) -> str:
    """One supervision iteration; the caller controls the polling schedule."""
    return supervise(path, now, kill, snapshot, position, require_open_observation=True)


def close(path: Path, now: datetime, broker: SimulatedBroker) -> str:
    """Compare separately recorded intent and execution evidence with fake deals."""
    if type(broker) is not SimulatedBroker:
        raise SafeguardError("only the built-in simulated broker is permitted")
    with closing(_db(path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        current, raw = db.execute("SELECT state,intent FROM study WHERE id=1").fetchone()
        if current != "POSITION_CLOSED":
            raise SafeguardError("position closure not observed")
        try:
            intent = json.loads(raw)
            execution = db.execute(
                "SELECT order_ticket,position_id FROM execution_log WHERE id=1").fetchone()
            journal = db.execute(
                "SELECT intent,result FROM validation_log WHERE id=1").fetchone()
            if execution is None or journal is None or journal[1]:
                raise SafeguardError("execution log or validation journal missing or already completed")
            recorded_intent = json.loads(journal[0])
            expected_intent = dict(intent, order_ticket=None, position_id=None)
            if (recorded_intent != expected_intent
                    or execution != (intent["order_ticket"], intent["position_id"])):
                raise SafeguardError("execution log or validation journal disagrees with lifecycle")
            earliest = _time(datetime.fromisoformat(intent["signal_time"])) + timedelta(minutes=5)
            if any(not earliest <= _time(deal.time) <= _time(now) for deal in broker.deals):
                raise SafeguardError("deal timestamp outside the observation window")
            trade = reconcile(_expected(intent), broker.deals, position_is_closed=True,
                              internal_order_ticket=execution[0])
        except (SafeguardError, ValueError, TypeError, KeyError, sqlite3.Error) as exc:
            return _failure(db, now, "RECONCILIATION_FAILURE", f"{type(exc).__name__}: {exc}")
        result = {key: str(value) for key, value in asdict(trade).items()}
        db.execute("UPDATE validation_log SET result=? WHERE id=1", (json.dumps(result, sort_keys=True),))
        _record_reconciled(db, now, intent, trade)
    return "SHUTDOWN"


def run_supervision(path: Path, started: datetime, kill: Path, broker: SimulatedBroker,
                    samples: list[SupervisionSample]) -> str:
    """Consume a finite scripted poll sequence; exhausted supervision fails closed."""
    if type(broker) is not SimulatedBroker:
        raise SafeguardError("only the built-in simulated broker is permitted")
    last = _time(started)
    for sample in samples:
        try:
            stamp = _time(sample.at)
            if stamp < last:
                raise SafeguardError("supervision timestamps are not monotonic")
            result = watch(path, stamp, kill, sample.snapshot, sample.position)
        except (SafeguardError, AttributeError, TypeError, ValueError, OSError) as exc:
            with closing(_db(path)) as db, db:
                db.execute("BEGIN IMMEDIATE")
                current = db.execute("SELECT state FROM study WHERE id=1").fetchone()[0]
                if current not in ("POSITION_OPEN", "POSITION_SUPERVISION"):
                    raise
                return _failure(db, last, "SUPERVISION_FAILURE", f"{type(exc).__name__}: {exc}")
        last = stamp
        if result == "POSITION_CLOSED":
            return close(path, stamp, broker)
        if result != "POSITION_SUPERVISION":
            return state(path)[0]
    with closing(_db(path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        current = db.execute("SELECT state FROM study WHERE id=1").fetchone()[0]
        if current not in ("POSITION_OPEN", "POSITION_SUPERVISION"):
            raise SafeguardError("no open position to supervise")
        return _failure(db, last, "SUPERVISION_ENDED", "script exhausted before position closed")


def recover(path: Path, now: datetime) -> str:
    """Never re-submit or resume an interrupted simulated attempt."""
    return restart(path, now)
