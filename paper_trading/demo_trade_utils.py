"""Shared validation and CSV helpers for the V1 demo-trading tools."""

from __future__ import annotations

import csv
import math
import re
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Mapping

from paper_trading.broker_time import parse_broker_timestamp


STRATEGY_VERSION = "Breakout Scalping V1"
PIP_SIZE = Decimal("0.0001")
STOP_LOSS_PIPS = Decimal("10")
TAKE_PROFIT_PIPS = Decimal("20")

TRADE_FIELDS = (
    "trade_id",
    "strategy_version",
    "account_type",
    "account_alias",
    "broker",
    "symbol",
    "timeframe",
    "signal_bar_open_time_broker",
    "signal_time_broker",
    "entry_time_broker",
    "exit_time_broker",
    "direction",
    "signal_close",
    "prior_20_high",
    "prior_20_low",
    "intended_entry",
    "actual_entry",
    "stop_price",
    "target_price",
    "actual_exit",
    "entry_spread_pips",
    "exit_spread_pips",
    "gross_pnl_pips",
    "commission_pips",
    "financing_pips",
    "slippage_pips",
    "pnl_pips",
    "pnl_r",
    "hold_minutes",
    "exit_reason",
    "order_reference",
    "completed",
    "rule_compliant",
    "notes",
)

TIMESTAMP_FIELDS = (
    "signal_bar_open_time_broker",
    "signal_time_broker",
    "entry_time_broker",
    "exit_time_broker",
)
PRICE_FIELDS = (
    "signal_close",
    "prior_20_high",
    "prior_20_low",
    "intended_entry",
    "actual_entry",
    "stop_price",
    "target_price",
    "actual_exit",
)
NUMERIC_FIELDS = (
    "gross_pnl_pips",
    "commission_pips",
    "financing_pips",
    "slippage_pips",
    "pnl_pips",
    "pnl_r",
    "hold_minutes",
)
SPREAD_FIELDS = ("entry_spread_pips", "exit_spread_pips")
def parse_broker_time(value: str, field: str) -> datetime:
    """Parse an ISO-8601 timestamp carrying its explicit source offset."""
    return parse_broker_timestamp(value, field)


def parse_decimal(value: str, field: str) -> Decimal:
    text = value.strip()
    if not text:
        raise ValueError(f"{field} is missing")
    try:
        parsed = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"{field} must be numeric: {value!r}") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field} must be finite")
    return parsed


def _as_text(value: object, field: str) -> str:
    if value is None:
        raise ValueError(f"{field} is missing")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field} is missing")
    return text


def validate_trade(values: Mapping[str, object]) -> dict[str, str]:
    """Validate and normalize one fully closed V1 demo-position record."""
    missing_columns = [field for field in TRADE_FIELDS if field not in values]
    if missing_columns:
        raise ValueError(f"trade is missing required fields: {', '.join(missing_columns)}")

    trade = {
        field: (
            ""
            if field == "notes"
            and (values[field] is None or not str(values[field]).strip())
            else _as_text(values[field], field)
        )
        for field in TRADE_FIELDS
    }
    if trade["strategy_version"] != STRATEGY_VERSION:
        raise ValueError(f"strategy_version must be {STRATEGY_VERSION!r}")
    if trade["account_type"].upper() != "DEMO":
        raise ValueError("account_type must be DEMO; live-account records are not accepted")
    trade["account_type"] = "DEMO"
    if trade["timeframe"].upper() != "M5":
        raise ValueError("timeframe must be M5")

    direction = trade["direction"].lower()
    if direction not in {"long", "short"}:
        raise ValueError("direction must be long or short")
    trade["direction"] = direction

    completed = trade["completed"].lower()
    if completed != "true":
        raise ValueError("incomplete trades cannot be recorded; completed must be true")
    trade["completed"] = "true"

    compliant = trade["rule_compliant"].lower()
    if compliant not in {"true", "false"}:
        raise ValueError("rule_compliant must be true or false")
    trade["rule_compliant"] = compliant

    timestamps = {
        field: parse_broker_time(trade[field], field) for field in TIMESTAMP_FIELDS
    }
    bar_open = timestamps["signal_bar_open_time_broker"]
    signal_time = timestamps["signal_time_broker"]
    entry_time = timestamps["entry_time_broker"]
    exit_time = timestamps["exit_time_broker"]
    if bar_open.minute % 5 or bar_open.second or bar_open.microsecond:
        raise ValueError("signal_bar_open_time_broker must be on an M5 boundary")
    if signal_time != bar_open + timedelta(minutes=5):
        raise ValueError("signal_time_broker must be the close time of the M5 signal bar")
    if signal_time.minute % 5 or signal_time.second or signal_time.microsecond:
        raise ValueError("signal_time_broker must be on an M5 boundary")
    if entry_time < signal_time:
        raise ValueError("entry_time_broker cannot precede signal_time_broker")
    if exit_time <= entry_time:
        raise ValueError("exit_time_broker must follow entry_time_broker")

    numbers: dict[str, Decimal] = {}
    for field in PRICE_FIELDS:
        value = parse_decimal(trade[field], field)
        if value <= 0:
            raise ValueError(f"{field} must be a positive price")
        numbers[field] = value
    for field in NUMERIC_FIELDS:
        numbers[field] = parse_decimal(trade[field], field)
    if numbers["hold_minutes"] < 0:
        raise ValueError("hold_minutes must be nonnegative")
    actual_hold = Decimal(str((exit_time - entry_time).total_seconds() / 60))
    if not math.isclose(
        float(numbers["hold_minutes"]), float(actual_hold), rel_tol=0, abs_tol=0.0001
    ):
        raise ValueError("hold_minutes must match the entry and exit timestamps")

    for field in SPREAD_FIELDS:
        value = trade[field]
        if value.lower().startswith("unavailable:"):
            if not value.partition(":")[2].strip():
                raise ValueError(f"{field} unavailable value must include a reason")
        else:
            spread = parse_decimal(value, field)
            if spread < 0:
                raise ValueError(f"{field} must be nonnegative")

    if numbers["prior_20_high"] < numbers["prior_20_low"]:
        raise ValueError("prior_20_high cannot be below prior_20_low")
    if direction == "long":
        if numbers["signal_close"] <= numbers["prior_20_high"]:
            raise ValueError("long signal_close must be above prior_20_high")
        expected_stop = numbers["actual_entry"] - STOP_LOSS_PIPS * PIP_SIZE
        expected_target = numbers["actual_entry"] + TAKE_PROFIT_PIPS * PIP_SIZE
    else:
        if numbers["signal_close"] >= numbers["prior_20_low"]:
            raise ValueError("short signal_close must be below prior_20_low")
        expected_stop = numbers["actual_entry"] + STOP_LOSS_PIPS * PIP_SIZE
        expected_target = numbers["actual_entry"] - TAKE_PROFIT_PIPS * PIP_SIZE
    if numbers["stop_price"] != expected_stop or numbers["target_price"] != expected_target:
        raise ValueError("stop_price and target_price must match frozen V1 distances")
    if not math.isclose(
        float(numbers["pnl_r"]),
        float(numbers["pnl_pips"] / STOP_LOSS_PIPS),
        rel_tol=0,
        abs_tol=0.0001,
    ):
        raise ValueError("pnl_r must equal pnl_pips divided by the frozen 10-pip risk")

    return trade


def read_trade_log(path: Path) -> list[dict[str, str]]:
    """Read and validate the complete operational CSV, including unique IDs."""
    try:
        file = path.open("r", newline="", encoding="utf-8-sig")
    except OSError as exc:
        raise ValueError(f"cannot read trade log {path}: {exc}") from exc
    with file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            raise ValueError(f"trade log {path} has no CSV header")
        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError(f"trade log {path} has duplicate CSV columns")
        missing = [field for field in TRADE_FIELDS if field not in reader.fieldnames]
        if missing:
            raise ValueError(
                f"trade log {path} is missing required columns: {', '.join(missing)}"
            )
        trades: list[dict[str, str]] = []
        seen_ids: set[str] = set()
        for line_number, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(f"trade log line {line_number} has extra CSV fields")
            try:
                trade = validate_trade(row)
            except ValueError as exc:
                raise ValueError(f"trade log line {line_number}: {exc}") from exc
            trade_id = trade["trade_id"]
            if trade_id in seen_ids:
                raise ValueError(f"trade log line {line_number}: duplicate trade_id {trade_id!r}")
            seen_ids.add(trade_id)
            trades.append(trade)
    return trades


def write_trade_log_header(path: Path) -> None:
    """Create a new operational CSV with the exact documented schema."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", newline="", encoding="utf-8") as file:
            csv.writer(file).writerow(TRADE_FIELDS)
    except FileExistsError:
        return


def ensure_no_cross_log_conflict(trade: Mapping[str, str], other_log: Path) -> None:
    """Reject records already classified in the other operational log."""
    if not other_log.exists():
        return
    references = dict(re.findall(r"(?:^|;)\s*(order|position)=(\d+)(?=;|$)", trade["order_reference"]))
    for existing in read_trade_log(other_log):
        if existing["trade_id"] == trade["trade_id"]:
            raise ValueError("trade ID already exists in the other classification log")
        if existing["account_alias"] != trade["account_alias"]:
            continue
        other_refs = dict(re.findall(r"(?:^|;)\s*(order|position)=(\d+)(?=;|$)", existing["order_reference"]))
        if not {"order", "position"} <= references.keys() or not {"order", "position"} <= other_refs.keys():
            raise ValueError("cross-log broker references are not structured; manual reconciliation required")
        if any(value != "0" and other_refs.get(key) == value for key, value in references.items()):
            raise ValueError("broker reference already exists in the other classification log")


def check_operational_log_classification(trade: Mapping[str, str], destination: Path) -> None:
    """Guard the two standard operational logs against cross-classification."""
    counterparts = {
        "demo_trading_log.csv": "VALIDATION_TRADING_LOG.csv",
        "validation_trading_log.csv": "DEMO_TRADING_LOG.csv",
    }
    other = counterparts.get(destination.name.lower())
    if other is not None:
        ensure_no_cross_log_conflict(trade, destination.with_name(other))


def is_gate_eligible(trade: Mapping[str, str]) -> bool:
    """Return whether a validated record may advance the 100-trade gate."""
    return (
        trade["strategy_version"] == STRATEGY_VERSION
        and trade["account_type"] == "DEMO"
        and trade["completed"] == "true"
        and trade["rule_compliant"] == "true"
    )
