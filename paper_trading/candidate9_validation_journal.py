"""Isolated durable journal for candidate 9; contains no order-submission code."""

from __future__ import annotations

import json
import math
import sqlite3
from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from paper_trading.candidate9_reconciliation import ReconciledTrade
from paper_trading.candidate9_safeguard_model import SafeguardError


@dataclass(frozen=True)
class EntryIntent:
    signal_id: str
    direction: str
    friday_close: float
    sunday_open: float
    gap_pips: float
    spread_pips: float
    intended_price: float
    created_at: datetime


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise SafeguardError("explicit-offset timestamp required")
    return value.astimezone(timezone.utc)


def create_journal(path: Path, started: datetime, expires: datetime) -> None:
    start, end = _utc(started), _utc(expires)
    if not start < end or (end - start).total_seconds() > 90 * 86400:
        raise SafeguardError("expiry must be within 90 days")
    if not path.parent.is_dir():
        raise SafeguardError("journal directory does not exist")
    with path.open("xb"):
        pass
    with closing(sqlite3.connect(path)) as db, db:
        db.executescript("""
            CREATE TABLE study (
                id INTEGER PRIMARY KEY CHECK(id=1), started TEXT NOT NULL,
                expires TEXT NOT NULL, state TEXT NOT NULL, reason TEXT NOT NULL
            );
            CREATE TABLE events (
                id INTEGER PRIMARY KEY, at TEXT NOT NULL,
                kind TEXT NOT NULL, payload TEXT NOT NULL
            );
            CREATE TABLE trade (
                id INTEGER PRIMARY KEY CHECK(id=1), signal_id TEXT NOT NULL UNIQUE,
                intent TEXT NOT NULL, result TEXT NOT NULL
            );
        """)
        db.execute("INSERT INTO study VALUES (1, ?, ?, 'idle', '')", (start.isoformat(), end.isoformat()))


def _connect(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise SafeguardError("journal is missing")
    db = sqlite3.connect(path)
    try:
        row = db.execute("SELECT started, expires, state, reason FROM study WHERE id=1").fetchone()
        if row is None or db.execute("SELECT COUNT(*) FROM study").fetchone()[0] != 1:
            raise SafeguardError("invalid study state")
        start, end = _utc(datetime.fromisoformat(row[0])), _utc(datetime.fromisoformat(row[1]))
        if end <= start or (end - start).total_seconds() > 90 * 86400:
            raise SafeguardError("invalid study expiry")
        if row[2] not in ("idle", "intent", "shutdown") or not isinstance(row[3], str):
            raise SafeguardError("invalid study phase")
        count = db.execute("SELECT COUNT(*) FROM trade").fetchone()[0]
        if count not in (0, 1) or (row[2] == "intent" and count != 1):
            raise SafeguardError("inconsistent trade state")
        db.execute("SELECT id, at, kind, payload FROM events LIMIT 1").fetchone()
    except (sqlite3.Error, TypeError, ValueError, SafeguardError) as exc:
        db.close()
        raise SafeguardError("journal is invalid or unreadable") from exc
    return db


def _event(db: sqlite3.Connection, now: datetime, kind: str, payload: dict) -> None:
    db.execute("INSERT INTO events(at,kind,payload) VALUES(?,?,?)",
               (_utc(now).isoformat(), kind, json.dumps(payload, sort_keys=True, allow_nan=False)))


def record_intent(path: Path, intent: EntryIntent) -> None:
    """Persist exactly one simulated intent. This operation never sends an order."""
    now = _utc(intent.created_at)
    if (not intent.signal_id or intent.direction not in ("long", "short")
            or any(not math.isfinite(x) for x in (
                intent.friday_close, intent.sunday_open, intent.gap_pips,
                intent.spread_pips, intent.intended_price))
            or min(intent.friday_close, intent.sunday_open, intent.intended_price) <= 0
            or intent.spread_pips < 0):
        raise SafeguardError("invalid trade intent")
    data = asdict(intent)
    data["created_at"] = now.isoformat()
    expired = False
    with closing(_connect(path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        started, expires, state = db.execute("SELECT started,expires,state FROM study WHERE id=1").fetchone()
        if state != "idle" or db.execute("SELECT COUNT(*) FROM trade").fetchone()[0]:
            raise SafeguardError("study already attempted or shut down")
        if not _utc(datetime.fromisoformat(started)) <= now < _utc(datetime.fromisoformat(expires)):
            db.execute("UPDATE study SET state='shutdown', reason='VALIDATION_EXPIRED'")
            _event(db, now, "VALIDATION_EXPIRED", {})
            expired = True
        else:
            payload = json.dumps(data, sort_keys=True, allow_nan=False)
            db.execute("INSERT INTO trade VALUES(1,?,?, '')", (intent.signal_id, payload))
            db.execute("UPDATE study SET state='intent' WHERE id=1")
            _event(db, now, "INTENT_RECORDED", data)
    if expired:
        raise SafeguardError("VALIDATION_EXPIRED")


def shutdown(path: Path, now: datetime, reason: str) -> None:
    if reason not in ("ORDER_REJECTED", "RECONCILIATION_FAILURE", "EXECUTION_UNCERTAIN",
                      "KILL_SWITCH_TRIGGERED", "BROKER_HEALTH_FAILURE",
                      "UNEXPECTED_OPEN_POSITION", "UNEXPECTED_PENDING_ORDER",
                      "VALIDATION_EXPIRED", "VALIDATION_TRADE_LIMIT", "ONE_TRADE_COMPLETED",
                      "SHUTDOWN_FAILURE_LIMIT", "SHUTDOWN_DAILY_LOSS", "RISK_CHECK_FAILURE",
                      "PROTECTION_FAILURE", "HIGH_SPREAD_DURING_POSITION"):
        raise SafeguardError("unsupported shutdown reason")
    with closing(_connect(path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        state = db.execute("SELECT state FROM study WHERE id=1").fetchone()[0]
        if state == "shutdown":
            raise SafeguardError("study is already shut down")
        db.execute("UPDATE study SET state='shutdown', reason=?", (reason,))
        _event(db, now, reason, {})


def record_completion(path: Path, now: datetime, trade: ReconciledTrade) -> None:
    """Save already reconciled evidence and permanently latch the study."""
    if not isinstance(trade, ReconciledTrade):
        raise SafeguardError("reconciled trade required")
    data = asdict(trade)
    for key, value in data.items():
        if isinstance(value, Decimal):
            if not value.is_finite():
                raise SafeguardError("invalid reconciled value")
            data[key] = str(value)
        elif isinstance(value, datetime):
            data[key] = _utc(value).isoformat()
    with closing(_connect(path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        state = db.execute("SELECT state FROM study WHERE id=1").fetchone()[0]
        if state != "intent":
            raise SafeguardError("completion requires exactly one pending intent")
        db.execute("UPDATE trade SET result=? WHERE id=1", (json.dumps(data, sort_keys=True),))
        db.execute("UPDATE study SET state='shutdown', reason='ONE_TRADE_COMPLETED'")
        _event(db, now, "ONE_TRADE_COMPLETED", data)


def recover(path: Path, now: datetime) -> str:
    """An unresolved intent is ambiguous after restart and must never be retried."""
    with closing(_connect(path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        state, reason = db.execute("SELECT state,reason FROM study WHERE id=1").fetchone()
        if state == "intent":
            reason = "EXECUTION_UNCERTAIN"
            db.execute("UPDATE study SET state='shutdown', reason=?", (reason,))
            _event(db, now, reason, {})
        return reason or "IDLE_NO_EXECUTION"
