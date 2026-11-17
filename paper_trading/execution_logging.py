"""Append-only event logging for demo-only execution attempts."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from paper_trading.broker_time import configured_broker_timezone, now_broker_time


EXECUTION_FIELDS = (
    "timestamp_broker",
    "event",
    "signal_time_broker",
    "planned_entry_time_broker",
    "submission_time_broker",
    "fill_time_broker",
    "fill_delay_ms",
    "direction",
    "order_ticket",
    "deal_ticket",
    "position_id",
    "volume",
    "price",
    "stop_loss",
    "take_profit",
    "details",
)

DEFAULT_EXECUTION_LOG = Path(__file__).with_name("EXECUTION_LOG.csv")


class ExecutionLogError(RuntimeError):
    """Raised when execution events cannot be persisted safely."""


class ExecutionLogger:
    def __init__(self, path: Path = DEFAULT_EXECUTION_LOG):
        self.path = path

    def append(self, event: str, **values: Any) -> None:
        row = {field: "" for field in EXECUTION_FIELDS}
        row.update(values)
        row["event"] = event
        if not row["timestamp_broker"]:
            row["timestamp_broker"] = now_broker_time(
                configured_broker_timezone()
            ).isoformat()
        try:
            needs_header = not self.path.exists() or self.path.stat().st_size == 0
            if not needs_header:
                with self.path.open("r", newline="", encoding="utf-8") as existing:
                    header = tuple(next(csv.reader(existing), ()))
                if header != EXECUTION_FIELDS:
                    raise ExecutionLogError(
                        f"execution log schema must exactly match: "
                        f"{','.join(EXECUTION_FIELDS)}"
                    )
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", newline="", encoding="utf-8") as output:
                writer = csv.DictWriter(
                    output, fieldnames=EXECUTION_FIELDS, extrasaction="raise"
                )
                if needs_header:
                    writer.writeheader()
                writer.writerow(row)
                output.flush()
        except OSError as exc:
            raise ExecutionLogError(f"cannot persist execution event: {exc}") from exc


def read_events(path: Path = DEFAULT_EXECUTION_LOG) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open("r", newline="", encoding="utf-8") as source:
            reader = csv.DictReader(source)
            if tuple(reader.fieldnames or ()) != EXECUTION_FIELDS:
                raise ExecutionLogError(
                    f"execution log schema must exactly match: "
                    f"{','.join(EXECUTION_FIELDS)}"
                )
            rows = list(reader)
    except OSError as exc:
        raise ExecutionLogError(f"cannot read execution log: {exc}") from exc
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ExecutionLogError("execution log contains malformed rows")
    return rows
