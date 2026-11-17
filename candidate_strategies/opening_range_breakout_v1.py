"""London opening-range breakout signals for isolated research."""

from datetime import time, timezone

from candidate_strategies.london_breakout_v1 import LONDON, Signal
from scripts.backtest import BAR_DURATION, PIP_SIZE, Bar


def generate_signals(bars: list[Bar]) -> list[Signal | None]:
    result: list[Signal | None] = [None] * len(bars)
    date = None
    opening: list[Bar] = []
    attempted = False
    for i, bar in enumerate(bars):
        local = bar.timestamp.astimezone(timezone.utc).astimezone(LONDON)
        if local.date() != date:
            date = local.date()
            opening = []
            attempted = False
        if time(7) <= local.time() < time(8):
            opening.append(bar)
            continue
        if attempted or not (time(8) <= local.time() < time(11)):
            continue
        if len(opening) != 12 or any(
            (b.timestamp - a.timestamp) != BAR_DURATION
            for a, b in zip(opening, opening[1:])
        ):
            continue
        if opening[0].timestamp.astimezone(LONDON).time() != time(7):
            continue
        high = max(item.high for item in opening)
        low = min(item.low for item in opening)
        direction = "long" if bar.close > high else "short" if bar.close < low else None
        if direction is not None:
            result[i] = Signal(direction, 10 * PIP_SIZE)
            attempted = True
    return result
