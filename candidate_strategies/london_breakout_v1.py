"""Causal London-session breakout signals for research."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

from scripts.backtest import BAR_DURATION, Bar


LONDON = ZoneInfo("Europe/London")


@dataclass(frozen=True)
class Signal:
    direction: str
    atr: float


def london_session_at_close(bar_open: datetime) -> bool:
    """Evaluate the completed bar's close as an instant in London."""
    if bar_open.tzinfo is None or bar_open.utcoffset() is None:
        raise ValueError("bar timestamp must have an explicit offset")
    close = bar_open.astimezone(timezone.utc) + BAR_DURATION
    local = close.astimezone(LONDON).time()
    return time(7) <= local < time(11)


def generate_signals(bars: list[Bar]) -> list[Signal | None]:
    signals: list[Signal | None] = [None] * len(bars)
    ema50: float | None = None
    ema200: float | None = None
    ranges: deque[float] = deque(maxlen=14)
    for i, bar in enumerate(bars):
        ema50 = bar.close if ema50 is None else ema50 + (2 / 51) * (bar.close - ema50)
        ema200 = bar.close if ema200 is None else ema200 + (2 / 201) * (bar.close - ema200)
        previous_close = bars[i - 1].close if i else bar.close
        ranges.append(max(bar.high - bar.low, abs(bar.high - previous_close),
                          abs(bar.low - previous_close)))
        if i < 199 or len(ranges) < 14 or not london_session_at_close(bar.timestamp):
            continue
        atr = sum(ranges) / 14
        if atr <= 0:
            continue
        prior = bars[i - 12:i]
        if ema50 > ema200 and bar.close > max(item.high for item in prior):
            signals[i] = Signal("long", atr)
        elif ema50 < ema200 and bar.close < min(item.low for item in prior):
            signals[i] = Signal("short", atr)
    return signals
