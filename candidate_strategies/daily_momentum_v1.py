"""Once-daily intraday time-series momentum research signal."""

from datetime import time, timedelta, timezone

from candidate_strategies.london_breakout_v1 import LONDON, Signal
from scripts.backtest import PIP_SIZE, Bar


def generate_signals(bars: list[Bar]) -> list[Signal | None]:
    result: list[Signal | None] = [None] * len(bars)
    closes = {}
    for i, bar in enumerate(bars):
        instant = bar.timestamp.astimezone(timezone.utc)
        local = instant.astimezone(LONDON)
        prior = closes.get(instant - timedelta(hours=24))
        if local.time() == time(7, 55) and prior is not None and bar.close != prior:
            result[i] = Signal("long" if bar.close > prior else "short", 10 * PIP_SIZE)
        closes[instant] = bar.close
    return result
