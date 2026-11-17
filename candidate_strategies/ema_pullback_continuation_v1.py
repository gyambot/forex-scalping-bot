"""Causal EMA pullback and ATR research signals on completed M5 bars."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from scripts.backtest import Bar


@dataclass(frozen=True)
class Signal:
    direction: str
    atr: float


def generate_signals(bars: list[Bar]) -> list[Signal | None]:
    """Use only the current and prior bars to calculate each signal."""
    signals: list[Signal | None] = [None] * len(bars)
    ema50: float | None = None
    ema200: float | None = None
    true_ranges: deque[float] = deque(maxlen=14)
    for i, bar in enumerate(bars):
        ema50 = bar.close if ema50 is None else ema50 + (2 / 51) * (bar.close - ema50)
        ema200 = bar.close if ema200 is None else ema200 + (2 / 201) * (bar.close - ema200)
        previous_close = bars[i - 1].close if i else bar.close
        true_ranges.append(max(bar.high - bar.low, abs(bar.high - previous_close),
                               abs(bar.low - previous_close)))
        if i < 199 or len(true_ranges) != 14:
            continue
        atr = sum(true_ranges) / 14
        if atr <= 0:
            continue
        if ema50 > ema200 and bar.low < ema50 and bar.close > ema50 and bar.close > bar.open:
            signals[i] = Signal("long", atr)
        elif ema50 < ema200 and bar.high > ema50 and bar.close < ema50 and bar.close < bar.open:
            signals[i] = Signal("short", atr)
    return signals
