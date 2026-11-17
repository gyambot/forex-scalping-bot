"""Non-executing candidate 9 safeguard model. No broker or order interface."""

from __future__ import annotations

import math
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


class SafeguardError(RuntimeError):
    """State is absent, invalid, or cannot be used safely."""


@dataclass(frozen=True)
class Snapshot:
    connected: bool
    demo_account_verified: bool
    account_available: bool
    symbol_available: bool
    trade_permissions: bool
    quote_fresh: bool
    open_positions: int
    pending_orders: int
    daily_net_pnl_r: float
    spread_pips: float
    gap_pips: float


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise SafeguardError("time must have an explicit offset")
    return value.astimezone(timezone.utc)


def initialize_model(path: Path, started: datetime, duration: timedelta = timedelta(days=90)) -> None:
    """Create isolated test/model state once; never reset existing state."""
    started = _utc(started)
    if duration <= timedelta(0) or duration > timedelta(days=90):
        raise SafeguardError("duration must be positive and no longer than 90 days")
    if not path.parent.is_dir():
        raise SafeguardError("state directory does not exist")
    with path.open("xb"):
        pass
    with closing(sqlite3.connect(path)) as db, db:
        db.executescript("""
            CREATE TABLE state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                started TEXT NOT NULL, expires TEXT NOT NULL,
                completed INTEGER NOT NULL CHECK (completed >= 0),
                failures INTEGER NOT NULL CHECK (failures >= 0),
                shutdown TEXT NOT NULL
            );
            CREATE TABLE events (
                id INTEGER PRIMARY KEY, at TEXT NOT NULL, event TEXT NOT NULL
            );
        """)
        db.execute("INSERT INTO state VALUES (1, ?, ?, 0, 0, '')",
                   (started.isoformat(), (started + duration).isoformat()))


def _open_existing(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise SafeguardError("safeguard state missing")
    db = sqlite3.connect(path)
    try:
        row = db.execute("SELECT started, expires, completed, failures, shutdown FROM state WHERE id=1").fetchone()
        if row is None or db.execute("SELECT count(*) FROM state").fetchone()[0] != 1:
            raise SafeguardError("safeguard state invalid")
        start, end = _utc(datetime.fromisoformat(row[0])), _utc(datetime.fromisoformat(row[1]))
        if (end <= start or end - start > timedelta(days=90)
                or not isinstance(row[2], int) or row[2] < 0
                or not isinstance(row[3], int) or row[3] < 0
                or not isinstance(row[4], str)):
            raise SafeguardError("safeguard state invalid")
        db.execute("SELECT id, at, event FROM events LIMIT 1").fetchone()
    except (sqlite3.Error, ValueError, TypeError, SafeguardError) as exc:
        db.close()
        raise SafeguardError("safeguard state unreadable or invalid") from exc
    return db


def record_outcome(path: Path, now: datetime, outcome: str) -> str:
    """Record a simulated lifecycle outcome; no order is submitted."""
    now = _utc(now)
    if outcome not in {"completed", "rejected", "reconciliation_failure", "execution_exception"}:
        raise SafeguardError("unsupported outcome")
    with closing(_open_existing(path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        completed, failures, shutdown = db.execute(
            "SELECT completed, failures, shutdown FROM state WHERE id=1"
        ).fetchone()
        if shutdown:
            raise SafeguardError("model is already shut down")
        if outcome == "completed":
            completed += 1
            shutdown = "ONE_TRADE_COMPLETED"
        else:
            failures += 1
            if outcome == "rejected":
                shutdown = "ORDER_REJECTED"
            elif outcome == "reconciliation_failure":
                shutdown = "RECONCILIATION_FAILURE"
            elif failures >= 3:
                shutdown = "SHUTDOWN_FAILURE_LIMIT"
        db.execute("UPDATE state SET completed=?, failures=?, shutdown=? WHERE id=1",
                   (completed, failures, shutdown))
        db.execute("INSERT INTO events(at, event) VALUES (?, ?)", (now.isoformat(), outcome))
        if shutdown:
            db.execute("INSERT INTO events(at, event) VALUES (?, ?)", (now.isoformat(), shutdown))
    return shutdown


def check_model(path: Path, kill_switch: Path, now: datetime, snapshot: Snapshot,
                max_spread_pips: float = 3.0, max_gap_pips: float = 20.0) -> str:
    """Return a model outcome, not permission to submit an order."""
    now = _utc(now)
    if (not math.isfinite(max_spread_pips) or max_spread_pips < 0
            or not math.isfinite(max_gap_pips) or max_gap_pips <= 0):
        raise SafeguardError("invalid configured limits")
    with closing(_open_existing(path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        start, expiry, completed, failures, shutdown = db.execute(
            "SELECT started, expires, completed, failures, shutdown FROM state WHERE id=1"
        ).fetchone()
        reason = shutdown
        if not reason:
            try:
                kill_switch.stat()
                killed = True
            except FileNotFoundError:
                killed = False
            if killed:
                reason = "KILL_SWITCH_TRIGGERED"
            elif completed >= 10:
                reason = "VALIDATION_TRADE_LIMIT"
            elif completed >= 1:
                reason = "ONE_TRADE_COMPLETED"
            elif failures >= 3:
                reason = "SHUTDOWN_FAILURE_LIMIT"
            elif now < _utc(datetime.fromisoformat(start)) or now >= _utc(datetime.fromisoformat(expiry)):
                reason = "VALIDATION_EXPIRED"
            elif any(value is not True for value in (
                    snapshot.connected, snapshot.demo_account_verified, snapshot.account_available,
                    snapshot.symbol_available, snapshot.trade_permissions, snapshot.quote_fresh)):
                reason = "BROKER_HEALTH_FAILURE"
            elif (type(snapshot.open_positions) is not int or snapshot.open_positions < 0
                  or type(snapshot.pending_orders) is not int or snapshot.pending_orders < 0):
                reason = "BROKER_HEALTH_FAILURE"
            elif snapshot.open_positions:
                reason = "UNEXPECTED_OPEN_POSITION"
            elif snapshot.pending_orders:
                reason = "UNEXPECTED_PENDING_ORDER"
            elif not math.isfinite(snapshot.daily_net_pnl_r):
                reason = "BROKER_HEALTH_FAILURE"
            elif snapshot.daily_net_pnl_r <= -1:
                reason = "SHUTDOWN_DAILY_LOSS"
            elif (not math.isfinite(snapshot.spread_pips) or snapshot.spread_pips < 0
                  or not math.isfinite(snapshot.gap_pips)):
                reason = "BROKER_HEALTH_FAILURE"
            elif abs(snapshot.gap_pips) > max_gap_pips:
                reason = "SIGNAL_SKIPPED_EXTREME_GAP"
            elif snapshot.spread_pips > max_spread_pips:
                reason = "SIGNAL_SKIPPED_HIGH_SPREAD"
            else:
                reason = "MODEL_CHECKS_PASSED_NO_EXECUTION"
            db.execute("INSERT INTO events(at, event) VALUES (?, ?)", (now.isoformat(), reason))
            if reason not in {"MODEL_CHECKS_PASSED_NO_EXECUTION", "SIGNAL_SKIPPED_HIGH_SPREAD",
                              "SIGNAL_SKIPPED_EXTREME_GAP"}:
                db.execute("UPDATE state SET shutdown=? WHERE id=1", (reason,))
    return reason
