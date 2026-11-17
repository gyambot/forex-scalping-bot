"""Timestamp helpers for explicit-offset broker-time records."""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone, tzinfo


DEFAULT_BROKER_UTC_OFFSET = "+02:00"
_OFFSET_PATTERN = re.compile(r"^([+-])(\d{2}):(\d{2})$")


def parse_broker_timezone(offset: str = DEFAULT_BROKER_UTC_OFFSET) -> timezone:
    """Create the configured fixed broker offset without changing clock fields."""
    match = _OFFSET_PATTERN.fullmatch(offset.strip())
    if match is None:
        raise ValueError("broker UTC offset must use the explicit +HH:MM or -HH:MM form")
    sign = 1 if match.group(1) == "+" else -1
    hours, minutes = int(match.group(2)), int(match.group(3))
    if hours > 14 or minutes > 59 or (hours == 14 and minutes != 0):
        raise ValueError("broker UTC offset is outside the supported range")
    delta = sign * timedelta(hours=hours, minutes=minutes)
    return timezone(delta, f"ICMarketsSC-Demo{offset}")


def configured_broker_timezone(offset: str | None = None) -> timezone:
    """Return the broker offset configured for this process."""
    return parse_broker_timezone(
        offset or os.environ.get("MT5_BROKER_UTC_OFFSET", DEFAULT_BROKER_UTC_OFFSET)
    )


def epoch_to_broker_time(epoch: int, offset: str) -> datetime:
    """Interpret MT5's epoch-rendered clock fields as broker wall time.

    The MT5 values observed in this project match the broker chart clock, but
    render about two hours ahead of the Windows UTC clock. Preserve those
    numeric clock fields and attach the configured broker offset; do not shift
    the displayed time as though the value were a UTC instant.
    """
    wall_time = datetime.fromtimestamp(epoch, timezone.utc).replace(tzinfo=None)
    return wall_time.replace(tzinfo=parse_broker_timezone(offset))


def now_broker_time(tz: tzinfo | None = None) -> datetime:
    """Return the current clock reading tagged with the configured broker offset."""
    return datetime.now(tz or configured_broker_timezone())


def parse_broker_timestamp(value: str, field: str) -> datetime:
    """Parse an ISO-8601 timestamp that carries an explicit source offset."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is missing")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include an explicit broker/source offset")
    return parsed
