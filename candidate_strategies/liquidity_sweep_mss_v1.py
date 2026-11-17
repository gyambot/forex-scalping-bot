"""Causal EURUSD M5 liquidity-sweep and structure-shift research signals."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from scripts.backtest import Bar, PIP_SIZE


SWEEP_DISTANCE = Decimal(str(PIP_SIZE))
SETUP_EXPIRY_BARS = 12


@dataclass(frozen=True)
class Signal:
    direction: str
    sweep_index: int
    pivot_index: int
    pivot_price: float
    structure_index: int
    structure_price: float


def generate_signals(bars: list[Bar]) -> list[Signal | None]:
    """Evaluate completed bars; pivots must have been confirmed before a sweep."""
    signals: list[Signal | None] = [None] * len(bars)
    last_high: tuple[int, float] | None = None
    last_low: tuple[int, float] | None = None
    long_setup: Signal | None = None
    short_setup: Signal | None = None

    for i, bar in enumerate(bars):
        if long_setup and i - long_setup.sweep_index > SETUP_EXPIRY_BARS:
            long_setup = None
        if short_setup and i - short_setup.sweep_index > SETUP_EXPIRY_BARS:
            short_setup = None

        long_break = bool(long_setup and i > long_setup.sweep_index and bar.close > long_setup.structure_price)
        short_break = bool(short_setup and i > short_setup.sweep_index and bar.close < short_setup.structure_price)
        if long_break and short_break:
            long_setup = short_setup = None
        elif long_break:
            signals[i] = long_setup
            long_setup = None
        elif short_break:
            signals[i] = short_setup
            short_setup = None

        if last_high is not None and last_low is not None:
            sweep_low = Decimal(str(bar.low)) <= Decimal(str(last_low[1])) - SWEEP_DISTANCE and bar.close > last_low[1]
            sweep_high = Decimal(str(bar.high)) >= Decimal(str(last_high[1])) + SWEEP_DISTANCE and bar.close < last_high[1]
            if sweep_low and sweep_high:
                long_setup = short_setup = None
            elif sweep_low:
                long_setup = Signal("long", i, *last_low, *last_high)
            elif sweep_high:
                short_setup = Signal("short", i, *last_high, *last_low)

        if i >= 4:
            p = i - 2
            pivot = bars[p]
            neighbors = (bars[p - 2], bars[p - 1], bars[p + 1], bars[p + 2])
            if all(pivot.high > item.high for item in neighbors):
                last_high = (p, pivot.high)
            if all(pivot.low < item.low for item in neighbors):
                last_low = (p, pivot.low)
    return signals
