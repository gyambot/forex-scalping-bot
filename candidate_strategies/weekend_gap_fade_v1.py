"""Fade the opening price gap after a weekend market closure."""

from datetime import timedelta, timezone

from candidate_strategies.london_breakout_v1 import Signal
from scripts.backtest import PIP_SIZE, Bar


def generate_signals(bars: list[Bar]) -> list[Signal | None]:
    result: list[Signal | None] = [None] * len(bars)
    for i in range(1, len(bars)):
        current = bars[i].timestamp.astimezone(timezone.utc)
        previous = bars[i - 1].timestamp.astimezone(timezone.utc)
        if (previous.weekday() != 4 or current.weekday() not in (6, 0)
                or current - previous < timedelta(hours=36)):
            continue
        gap = bars[i].open - bars[i - 1].close
        if abs(gap) >= 5 * PIP_SIZE:
            result[i] = Signal("short" if gap > 0 else "long", 10 * PIP_SIZE)
    return result
