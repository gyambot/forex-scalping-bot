"""Persistent candidate 9 lifecycle simulation. No MT5 or order API is called."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from paper_trading.candidate9_broker_observation import derive_weekend_signal
from paper_trading.candidate9_mt5_history import read_closed_trade
from paper_trading.candidate9_reconciliation import Deal, ExpectedTrade, ReconciledTrade, reconcile
from paper_trading.candidate9_risk import BrokerConstraints, prepare_risk
from paper_trading.candidate9_safeguard_model import SafeguardError
from scripts.backtest import Bar


TRANSITIONS = {
    "IDLE": {"PRECHECK", "SHUTDOWN", "MANUAL_REVIEW_REQUIRED"},
    "PRECHECK": {"SIGNAL_DETECTED", "SHUTDOWN", "MANUAL_REVIEW_REQUIRED"},
    "SIGNAL_DETECTED": {"ORDER_PENDING", "SHUTDOWN", "MANUAL_REVIEW_REQUIRED"},
    "ORDER_PENDING": {"POSITION_OPEN", "SHUTDOWN", "MANUAL_REVIEW_REQUIRED"},
    "POSITION_OPEN": {"POSITION_SUPERVISION", "MANUAL_REVIEW_REQUIRED"},
    "POSITION_SUPERVISION": {"POSITION_CLOSED", "MANUAL_REVIEW_REQUIRED"},
    "POSITION_CLOSED": {"RECONCILED", "MANUAL_REVIEW_REQUIRED"},
    "RECONCILED": {"SHUTDOWN", "MANUAL_REVIEW_REQUIRED"},
    "SHUTDOWN": set(),
    "MANUAL_REVIEW_REQUIRED": set(),
}


def _time(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise SafeguardError("time requires an explicit offset")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class SimulatedSnapshot:
    demo_verified: bool
    healthy: bool
    quote_fresh: bool
    positions: int
    pending_orders: int
    spread_pips: Decimal
    daily_net_pnl_r: Decimal


@dataclass(frozen=True)
class SimulatedPosition:
    position_id: int
    magic: int
    direction: str
    volume: Decimal
    stop: Decimal
    target: Decimal


def create(path: Path, now: datetime, expires: datetime) -> None:
    now, expires = _time(now), _time(expires)
    if not now < expires <= now + timedelta(days=90):
        raise SafeguardError("expiry must be within 90 days")
    if not path.parent.is_dir():
        raise SafeguardError("state directory missing")
    with path.open("xb"):
        pass
    with closing(sqlite3.connect(path)) as db, db:
        db.executescript("""
            CREATE TABLE study (id INTEGER PRIMARY KEY CHECK(id=1), state TEXT NOT NULL,
                started TEXT NOT NULL, expires TEXT NOT NULL, completed INTEGER NOT NULL,
                failures INTEGER NOT NULL, reason TEXT NOT NULL, intent TEXT NOT NULL);
            CREATE TABLE events (id INTEGER PRIMARY KEY, at TEXT NOT NULL,
                old_state TEXT NOT NULL, new_state TEXT NOT NULL, reason TEXT NOT NULL);
            CREATE TABLE trade_log (id INTEGER PRIMARY KEY CHECK(id=1), record TEXT NOT NULL);
            CREATE TABLE execution_log (id INTEGER PRIMARY KEY CHECK(id=1), order_ticket INTEGER NOT NULL,
                position_id INTEGER NOT NULL);
            CREATE TABLE validation_log (id INTEGER PRIMARY KEY CHECK(id=1), intent TEXT NOT NULL,
                result TEXT NOT NULL);
        """)
        db.execute("INSERT INTO study VALUES(1,'IDLE',?,?,0,0,'','')",
                   (now.isoformat(), expires.isoformat()))


def _db(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise SafeguardError("lifecycle state missing")
    db = sqlite3.connect(path)
    try:
        row = db.execute("SELECT state,started,expires,completed,failures,reason,intent FROM study WHERE id=1").fetchone()
        if row is None or db.execute("SELECT count(*) FROM study").fetchone()[0] != 1:
            raise SafeguardError("lifecycle state invalid")
        state, start, end, completed, failures, reason, intent = row
        start, end = _time(datetime.fromisoformat(start)), _time(datetime.fromisoformat(end))
        if (state not in TRANSITIONS or not start < end <= start + timedelta(days=90)
                or type(completed) is not int or completed < 0
                or type(failures) is not int or failures < 0
                or not isinstance(reason, str) or not isinstance(intent, str)):
            raise SafeguardError("lifecycle state invalid")
        db.execute("SELECT id,at,old_state,new_state,reason FROM events LIMIT 1").fetchone()
        db.execute("SELECT record FROM trade_log LIMIT 1").fetchone()
    except (sqlite3.Error, ValueError, TypeError, SafeguardError) as exc:
        db.close()
        raise SafeguardError("lifecycle state unreadable") from exc
    return db


def _move(db: sqlite3.Connection, now: datetime, new: str, reason: str) -> None:
    old = db.execute("SELECT state FROM study WHERE id=1").fetchone()[0]
    if new not in TRANSITIONS[old]:
        raise SafeguardError(f"invalid lifecycle transition {old} -> {new}")
    db.execute("UPDATE study SET state=?, reason=? WHERE id=1", (new, reason))
    db.execute("INSERT INTO events(at,old_state,new_state,reason) VALUES(?,?,?,?)",
               (_time(now).isoformat(), old, new, reason))


def state(path: Path) -> tuple[str, str]:
    with closing(_db(path)) as db:
        return db.execute("SELECT state,reason FROM study WHERE id=1").fetchone()


def _kill_exists(path: Path) -> bool:
    try:
        path.stat()
    except FileNotFoundError:
        return False
    return True


def begin(path: Path, now: datetime, kill: Path, snapshot: SimulatedSnapshot,
          friday: Bar, reopening: Bar, *, bid: Decimal, ask: Decimal, volume: Decimal,
          risk_budget: Decimal, costs_per_lot: Decimal, constraints: BrokerConstraints,
          magic: int) -> str:
    """Run a single simulated precheck and persist an order intent, never send it."""
    now = _time(now)
    with closing(_db(path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        current, start, expiry, completed, failures = db.execute(
            "SELECT state,started,expires,completed,failures FROM study WHERE id=1").fetchone()
        if current != "IDLE":
            raise SafeguardError("study is not idle")
        reason = ""
        try:
            killed = _kill_exists(kill)
        except OSError as exc:
            _move(db, now, "MANUAL_REVIEW_REQUIRED", "KILL_SWITCH_CHECK_FAILURE")
            db.execute("UPDATE events SET reason=? WHERE id=(SELECT MAX(id) FROM events)",
                       (f"KILL_SWITCH_CHECK_FAILURE: {exc}",))
            return "KILL_SWITCH_CHECK_FAILURE"
        if killed:
            reason = "KILL_SWITCH_TRIGGERED"
        elif completed >= 10:
            reason = "VALIDATION_TRADE_LIMIT"
        elif completed >= 1:
            reason = "ONE_TRADE_COMPLETED"
        elif failures >= 3:
            reason = "SHUTDOWN_FAILURE_LIMIT"
        elif not _time(datetime.fromisoformat(start)) <= now < _time(datetime.fromisoformat(expiry)):
            reason = "VALIDATION_EXPIRED"
        if reason:
            _move(db, now, "SHUTDOWN", reason)
            return reason
        _move(db, now, "PRECHECK", "")
        if (snapshot.demo_verified is not True or snapshot.healthy is not True
                or snapshot.quote_fresh is not True or type(snapshot.positions) is not int
                or type(snapshot.pending_orders) is not int or snapshot.positions < 0
                or snapshot.pending_orders < 0
                or not isinstance(snapshot.daily_net_pnl_r, Decimal)
                or not snapshot.daily_net_pnl_r.is_finite()
                or not isinstance(snapshot.spread_pips, Decimal)
                or not snapshot.spread_pips.is_finite() or snapshot.spread_pips < 0):
            _move(db, now, "MANUAL_REVIEW_REQUIRED", "BROKER_HEALTH_FAILURE")
            return "BROKER_HEALTH_FAILURE"
        if snapshot.positions or snapshot.pending_orders:
            reason = "UNEXPECTED_OPEN_POSITION" if snapshot.positions else "UNEXPECTED_PENDING_ORDER"
            _move(db, now, "MANUAL_REVIEW_REQUIRED", reason)
            return reason
        if snapshot.daily_net_pnl_r <= -1:
            _move(db, now, "SHUTDOWN", "SHUTDOWN_DAILY_LOSS")
            return "SHUTDOWN_DAILY_LOSS"
        try:
            signal = derive_weekend_signal(friday, reopening, observed_at=now)
        except SafeguardError:
            _move(db, now, "MANUAL_REVIEW_REQUIRED", "SIGNAL_DATA_INVALID")
            return "SIGNAL_DATA_INVALID"
        if signal.direction is None:
            _move(db, now, "SHUTDOWN", "NO_SIGNAL")
            return "NO_SIGNAL"
        if not signal.nominal_entry_time <= now <= signal.nominal_entry_time + timedelta(seconds=5):
            _move(db, now, "SHUTDOWN", "SIGNAL_MISSED")
            return "SIGNAL_MISSED"
        _move(db, now, "SIGNAL_DETECTED", "")
        if abs(signal.gap_pips) > 20:
            _move(db, now, "SHUTDOWN", "SIGNAL_SKIPPED_EXTREME_GAP")
            return "SIGNAL_SKIPPED_EXTREME_GAP"
        if snapshot.spread_pips > 3:
            _move(db, now, "SHUTDOWN", "SIGNAL_SKIPPED_HIGH_SPREAD")
            return "SIGNAL_SKIPPED_HIGH_SPREAD"
        if (not isinstance(bid, Decimal) or not isinstance(ask, Decimal)
                or not bid.is_finite() or not ask.is_finite()
                or (ask - bid) / Decimal("0.0001") != snapshot.spread_pips):
            _move(db, now, "MANUAL_REVIEW_REQUIRED", "QUOTE_MISMATCH")
            return "QUOTE_MISMATCH"
        if type(magic) is not int or magic <= 0:
            _move(db, now, "MANUAL_REVIEW_REQUIRED", "INVALID_MAGIC")
            return "INVALID_MAGIC"
        try:
            risk = prepare_risk(signal.direction, bid, ask, volume, risk_budget, costs_per_lot, constraints)
        except SafeguardError:
            _move(db, now, "MANUAL_REVIEW_REQUIRED", "RISK_CHECK_FAILURE")
            return "RISK_CHECK_FAILURE"
        intent = {
            "direction": signal.direction, "friday_close": signal.friday_close,
            "sunday_open": signal.reopening_open, "gap_pips": signal.gap_pips,
            "spread_pips": str(snapshot.spread_pips), "entry": str(risk.entry),
            "stop": str(risk.stop), "target": str(risk.target), "volume": str(volume),
            "risk_budget": str(risk_budget), "magic": magic,
            "signal_time": signal.signal_bar_time.isoformat(), "order_ticket": None,
            "position_id": None,
        }
        db.execute("UPDATE study SET intent=? WHERE id=1", (json.dumps(intent, sort_keys=True),))
        _move(db, now, "ORDER_PENDING", "SIMULATED_INTENT_RECORDED")
    return "ORDER_PENDING"


def submission_result(path: Path, now: datetime, result: str, *,
                      order_ticket: int | None = None, position_id: int | None = None) -> str:
    """Apply a synthetic outcome. There is intentionally no broker submission."""
    with closing(_db(path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        current, raw = db.execute("SELECT state,intent FROM study WHERE id=1").fetchone()
        if current != "ORDER_PENDING":
            raise SafeguardError("no pending simulated intent")
        if result == "rejected":
            db.execute("UPDATE study SET failures=failures+1 WHERE id=1")
            _move(db, now, "SHUTDOWN", "ORDER_REJECTED")
        elif result == "accepted" and type(order_ticket) is int and order_ticket > 0 and type(position_id) is int and position_id > 0:
            intent = json.loads(raw)
            intent.update(order_ticket=order_ticket, position_id=position_id)
            db.execute("UPDATE study SET intent=? WHERE id=1", (json.dumps(intent, sort_keys=True),))
            _move(db, now, "POSITION_OPEN", "SIMULATED_ACCEPTED")
        else:
            db.execute("UPDATE study SET failures=failures+1 WHERE id=1")
            _move(db, now, "MANUAL_REVIEW_REQUIRED", "SUBMISSION_UNKNOWN")
    return state(path)[0]


def supervise(path: Path, now: datetime, kill: Path, snapshot: SimulatedSnapshot,
              position: SimulatedPosition | None, *, require_open_observation: bool = False) -> str:
    with closing(_db(path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        current, raw, expiry = db.execute("SELECT state,intent,expires FROM study WHERE id=1").fetchone()
        if current not in ("POSITION_OPEN", "POSITION_SUPERVISION"):
            raise SafeguardError("no open position to supervise")
        reason = ""
        try:
            killed = _kill_exists(kill)
        except OSError as exc:
            _move(db, now, "MANUAL_REVIEW_REQUIRED", "KILL_SWITCH_CHECK_FAILURE")
            db.execute("UPDATE events SET reason=? WHERE id=(SELECT MAX(id) FROM events)",
                       (f"KILL_SWITCH_CHECK_FAILURE: {exc}",))
            return "KILL_SWITCH_CHECK_FAILURE"
        if killed:
            reason = "KILL_SWITCH_TRIGGERED"
        elif _time(now) >= _time(datetime.fromisoformat(expiry)):
            reason = "VALIDATION_EXPIRED"
        elif (snapshot.demo_verified is not True or snapshot.healthy is not True
              or snapshot.quote_fresh is not True or type(snapshot.positions) is not int
              or type(snapshot.pending_orders) is not int or snapshot.pending_orders != 0
              or not isinstance(snapshot.spread_pips, Decimal) or not snapshot.spread_pips.is_finite()
              or snapshot.spread_pips < 0 or not isinstance(snapshot.daily_net_pnl_r, Decimal)
              or not snapshot.daily_net_pnl_r.is_finite()):
            reason = "BROKER_HEALTH_FAILURE"
        elif snapshot.daily_net_pnl_r <= -1:
            reason = "SHUTDOWN_DAILY_LOSS"
        elif snapshot.spread_pips > 3:
            reason = "HIGH_SPREAD_DURING_POSITION"
        if reason:
            _move(db, now, "MANUAL_REVIEW_REQUIRED", reason)
            return reason
        intent = json.loads(raw)
        if snapshot.positions == 0 and position is None:
            if current == "POSITION_OPEN" and require_open_observation:
                _move(db, now, "MANUAL_REVIEW_REQUIRED", "POSITION_NEVER_OBSERVED")
                return "POSITION_NEVER_OBSERVED"
            if current == "POSITION_OPEN":
                _move(db, now, "POSITION_SUPERVISION", "POSITION_OBSERVED_CLOSED")
            _move(db, now, "POSITION_CLOSED", "HISTORY_REQUIRED")
            return "POSITION_CLOSED"
        if (snapshot.positions != 1 or position is None
                or position.position_id != intent["position_id"] or position.magic != intent["magic"]
                or position.direction != intent["direction"] or position.volume != Decimal(intent["volume"])
                or position.stop != Decimal(intent["stop"]) or position.target != Decimal(intent["target"])):
            _move(db, now, "MANUAL_REVIEW_REQUIRED", "POSITION_OR_PROTECTION_MISMATCH")
            return "POSITION_OR_PROTECTION_MISMATCH"
        if current == "POSITION_OPEN":
            _move(db, now, "POSITION_SUPERVISION", "SIMULATED_PROTECTION_VERIFIED")
    return "POSITION_SUPERVISION"


def _expected(intent: dict) -> ExpectedTrade:
    return ExpectedTrade(intent["order_ticket"], intent["position_id"], intent["magic"],
                         intent["direction"], Decimal(intent["volume"]),
                         Decimal(intent["entry"]), Decimal(intent["risk_budget"]))


def _record_reconciled(db: sqlite3.Connection, now: datetime, intent: dict,
                       trade: ReconciledTrade) -> None:
    record = {**intent, **{k: str(v) for k, v in asdict(trade).items()}}
    db.execute("INSERT INTO trade_log VALUES(1,?)", (json.dumps(record, sort_keys=True),))
    _move(db, now, "RECONCILED", "HISTORY_MATCHED")
    db.execute("UPDATE study SET completed=completed+1 WHERE id=1")
    _move(db, now, "SHUTDOWN", "ONE_TRADE_COMPLETED")


def finish(path: Path, now: datetime, deals: list[Deal], internal_order_ticket: int) -> str:
    with closing(_db(path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        current, raw = db.execute("SELECT state,intent FROM study WHERE id=1").fetchone()
        if current != "POSITION_CLOSED":
            raise SafeguardError("position closure not observed")
        intent = json.loads(raw)
        try:
            trade = reconcile(_expected(intent), deals, position_is_closed=True,
                              internal_order_ticket=internal_order_ticket)
        except SafeguardError:
            db.execute("UPDATE study SET failures=failures+1 WHERE id=1")
            _move(db, now, "MANUAL_REVIEW_REQUIRED", "RECONCILIATION_FAILURE")
            return "RECONCILIATION_FAILURE"
        _record_reconciled(db, now, intent, trade)
    return "SHUTDOWN"


def finish_from_broker(path: Path, now: datetime, module: Any, *, expected_login: int,
                       epoch_is_verified_utc: bool, internal_order_ticket: int) -> str:
    """Reconcile the simulation with read-only broker-like history, never submit.

    The internal order ticket is caller supplied, not an independent log proof.
    Until a real execution journal exists this is not a production lifecycle.
    """
    with closing(_db(path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        current, raw = db.execute("SELECT state,intent FROM study WHERE id=1").fetchone()
        if current != "POSITION_CLOSED":
            raise SafeguardError("position closure not observed")
        intent = json.loads(raw)
        try:
            trade = read_closed_trade(module, _expected(intent), now=now,
                                      expected_login=expected_login,
                                      epoch_is_verified_utc=epoch_is_verified_utc,
                                      internal_order_ticket=internal_order_ticket,
                                      not_before=_time(datetime.fromisoformat(intent["signal_time"]))
                                      + timedelta(minutes=5))
        except Exception as exc:
            db.execute("UPDATE study SET failures=failures+1 WHERE id=1")
            _move(db, now, "MANUAL_REVIEW_REQUIRED", "RECONCILIATION_FAILURE")
            db.execute("UPDATE events SET reason=? WHERE id=(SELECT MAX(id) FROM events)",
                       (f"RECONCILIATION_FAILURE: {type(exc).__name__}: {exc}",))
            return "RECONCILIATION_FAILURE"
        _record_reconciled(db, now, intent, trade)
    return "SHUTDOWN"


def restart(path: Path, now: datetime) -> str:
    with closing(_db(path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        current = db.execute("SELECT state FROM study WHERE id=1").fetchone()[0]
        if current in ("ORDER_PENDING", "POSITION_OPEN", "POSITION_SUPERVISION",
                       "POSITION_CLOSED", "RECONCILED", "PRECHECK", "SIGNAL_DETECTED"):
            _move(db, now, "MANUAL_REVIEW_REQUIRED", "RESTART_REQUIRES_RECONCILIATION")
            return "MANUAL_REVIEW_REQUIRED"
        return current
