"""Causal, research-only trendline/stochastic signal generator."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from scripts.backtest import Bar


@dataclass(frozen=True)
class Signal:
    direction: str
    setup: str


def classify_signal(
    bar: Bar, previous_close: float, ema: float, zone: float,
    support: tuple[float, float] | None, resistance: tuple[float, float] | None,
    k: float, d: float, previous_k: float, previous_d: float,
) -> Signal | None:
    bullish_cross = previous_k <= previous_d and k > d
    bearish_cross = previous_k >= previous_d and k < d
    if bar.close > ema and resistance is not None and resistance[1] < 0 and previous_close <= resistance[0] - resistance[1] + zone and bar.close > resistance[0] + zone and k > d:
        return Signal("long", "breakout")
    if bar.close < ema and support is not None and support[1] > 0 and previous_close >= support[0] - support[1] - zone and bar.close < support[0] - zone and k < d:
        return Signal("short", "breakout")
    if bar.close > ema and support is not None and support[1] > 0 and support[0] - zone <= bar.low <= support[0] + zone and bar.close > support[0] + zone and bullish_cross and k < 20:
        return Signal("long", "bounce")
    if bar.close < ema and resistance is not None and resistance[1] < 0 and resistance[0] - zone <= bar.high <= resistance[0] + zone and bar.close < resistance[0] - zone and bearish_cross and k > 80:
        return Signal("short", "bounce")
    return None


def generate_signals(bars: list[Bar]) -> list[Signal | None]:
    """Return one close-of-bar signal per input bar without future data."""
    signals: list[Signal | None] = [None] * len(bars)
    highs: deque[tuple[int, float]] = deque(maxlen=2)
    lows: deque[tuple[int, float]] = deque(maxlen=2)
    true_ranges: deque[float] = deque(maxlen=14)
    raw_ks: deque[float] = deque(maxlen=3)
    slow_ks: deque[float] = deque(maxlen=3)
    previous_k: float | None = None
    previous_d: float | None = None
    ema: float | None = None
    alpha = 2 / 201

    for i, bar in enumerate(bars):
        ema = bar.close if ema is None else alpha * bar.close + (1 - alpha) * ema
        previous_close = bars[i - 1].close if i else bar.close
        true_ranges.append(max(bar.high - bar.low, abs(bar.high - previous_close), abs(bar.low - previous_close)))
        if i >= 4:
            p = i - 2
            pivot = bars[p]
            neighbors = (bars[p - 2], bars[p - 1], bars[p + 1], bars[p + 2])
            if all(pivot.high > item.high for item in neighbors):
                highs.append((p, pivot.high))
            if all(pivot.low < item.low for item in neighbors):
                lows.append((p, pivot.low))

        k = d = None
        if i >= 13:
            window = bars[i - 13 : i + 1]
            high = max(item.high for item in window)
            low = min(item.low for item in window)
            if high > low:
                raw_ks.append(100 * (bar.close - low) / (high - low))
            else:
                raw_ks.clear()
                slow_ks.clear()
            if len(raw_ks) == 3:
                k = sum(raw_ks) / 3
                slow_ks.append(k)
                if len(slow_ks) == 3:
                    d = sum(slow_ks) / 3

        if i >= 199 and len(true_ranges) == 14 and k is not None and d is not None and previous_k is not None and previous_d is not None:
            zone = 0.25 * sum(true_ranges) / 14
            if zone > 0:
                def line(points: deque[tuple[int, float]]) -> tuple[float, float] | None:
                    if len(points) != 2:
                        return None
                    (x1, y1), (x2, y2) = points
                    slope = (y2 - y1) / (x2 - x1)
                    return y2 + slope * (i - x2), slope

                support = line(lows)
                resistance = line(highs)
                signals[i] = classify_signal(
                    bar, bars[i - 1].close, ema, zone, support, resistance,
                    k, d, previous_k, previous_d,
                )

        previous_k, previous_d = k, d
    return signals
