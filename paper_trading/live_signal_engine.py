"""Read-only signal evaluation for the frozen Breakout Scalping V1."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Iterable, Mapping, Sequence

from paper_trading.mt5_price_feed import get_recent_m5_bars
from paper_trading.broker_time import parse_broker_timestamp
from scripts.backtest import (
    LOOKBACK_BARS,
    Bar,
    breakout_signal_at,
)


SIGNAL_CSV_FIELDS = (
    "timestamp",
    "signal_type",
    "breakout_level",
    "current_price",
    "stop_price",
    "target_price",
    "notes",
)


@dataclass(frozen=True)
class LiveSignal:
    timestamp: str
    signal_type: str
    breakout_level: float | None
    current_price: float
    stop_price: float | None
    target_price: float | None
    notes: str

    def to_csv_row(self) -> dict[str, Any]:
        row = asdict(self)
        for field in ("breakout_level", "stop_price", "target_price"):
            if row[field] is None:
                row[field] = ""
        return row


def _read_value(bar: Any, name: str) -> Any:
    if isinstance(bar, Mapping):
        return bar[name]
    return getattr(bar, name)


def _normalize_bar(bar: Any) -> Bar:
    value = _read_value(bar, "timestamp")
    if isinstance(value, datetime):
        timestamp = value
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("bar timestamp must include an explicit broker/source offset")
    elif isinstance(value, str):
        timestamp = parse_broker_timestamp(value, "bar timestamp")
    else:
        raise ValueError("bar timestamp must be a datetime or ISO-8601 string")
    if timestamp.second or timestamp.microsecond or timestamp.minute % 5:
        raise ValueError("bar timestamp must be on an M5 boundary")

    prices: dict[str, float] = {}
    for name in ("open", "high", "low", "close"):
        try:
            price = float(_read_value(bar, name))
        except (TypeError, ValueError, KeyError, AttributeError) as exc:
            raise ValueError(f"bar {name} price is missing or invalid") from exc
        if not math.isfinite(price) or price <= 0:
            raise ValueError(f"bar {name} price must be finite and positive")
        prices[name] = price

    if (
        prices["low"] > min(prices["open"], prices["close"])
        or prices["high"] < max(prices["open"], prices["close"])
        or prices["low"] > prices["high"]
    ):
        raise ValueError("bar has inconsistent OHLC prices")

    return Bar(timestamp=timestamp, **prices)


def _normalize_bars(bars: Iterable[Any]) -> list[Bar]:
    normalized = [_normalize_bar(bar) for bar in bars]
    for previous, current in zip(normalized, normalized[1:]):
        if current.timestamp <= previous.timestamp:
            raise ValueError("bars must be strictly chronological and unique")
    return normalized


def evaluate_v1_signal(bars: Sequence[Any]) -> LiveSignal:
    """Evaluate the latest completed bar using V1's strict 20-bar close rule.

    Stop and target prices are left unset because V1 anchors them to the next
    bar's actual entry price, which this read-only engine does not execute.
    """
    normalized = _normalize_bars(bars)
    if not normalized:
        raise ValueError("at least one completed bar is required")

    latest = normalized[-1]
    timestamp = latest.timestamp.isoformat()
    if len(normalized) <= LOOKBACK_BARS:
        return LiveSignal(
            timestamp=timestamp,
            signal_type="NO SIGNAL",
            breakout_level=None,
            current_price=latest.close,
            stop_price=None,
            target_price=None,
            notes=f"Need {LOOKBACK_BARS} prior completed bars.",
        )

    direction, level = breakout_signal_at(normalized, len(normalized) - 1)
    if direction is None:
        return LiveSignal(
            timestamp=timestamp,
            signal_type="NO SIGNAL",
            breakout_level=None,
            current_price=latest.close,
            stop_price=None,
            target_price=None,
            notes="Close is not strictly beyond the prior 20-bar channel.",
        )

    return LiveSignal(
        timestamp=timestamp,
        signal_type="LONG" if direction == "long" else "SHORT",
        breakout_level=level,
        current_price=latest.close,
        stop_price=None,
        target_price=None,
        notes=(
            "Raw V1 breakout candidate. Entry is next M5 bar open; stop/target "
            "levels are unknown until entry. Active-position eligibility is "
            "not evaluated by this read-only engine."
        ),
    )


def generate_v1_signals(bars: Iterable[Any]) -> list[LiveSignal]:
    """Return every raw LONG/SHORT breakout candidate in chronological data."""
    normalized = _normalize_bars(bars)
    signals: list[LiveSignal] = []
    for index in range(LOOKBACK_BARS, len(normalized)):
        direction, level = breakout_signal_at(normalized, index)
        if direction is None:
            continue
        bar = normalized[index]
        signals.append(
            LiveSignal(
                timestamp=bar.timestamp.isoformat(),
                signal_type="LONG" if direction == "long" else "SHORT",
                breakout_level=level,
                current_price=bar.close,
                stop_price=None,
                target_price=None,
                notes=(
                    "Raw V1 breakout candidate; active-position eligibility "
                    "is not evaluated."
                ),
            )
        )
    return signals


def get_live_v1_signal() -> LiveSignal:
    """Read the latest 21 completed MT5 M5 bars and evaluate the newest bar."""
    bars = get_recent_m5_bars(count=LOOKBACK_BARS + 1)
    return evaluate_v1_signal(bars)
