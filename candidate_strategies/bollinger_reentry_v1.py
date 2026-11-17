"""Causal Bollinger re-entry mean-reversion signals."""

import math

from candidate_strategies.london_breakout_v1 import Signal
from scripts.backtest import PIP_SIZE, Bar


def generate_signals(bars: list[Bar]) -> list[Signal | None]:
    result: list[Signal | None] = [None] * len(bars)
    previous_side = 0
    for i in range(19, len(bars)):
        closes = [bar.close for bar in bars[i - 19:i + 1]]
        mean = sum(closes) / 20
        deviation = math.sqrt(sum((value - mean) ** 2 for value in closes) / 20)
        side = -1 if bars[i].close < mean - 2 * deviation else (
            1 if bars[i].close > mean + 2 * deviation else 0
        )
        if side == 0 and previous_side:
            result[i] = Signal("long" if previous_side == -1 else "short", 10 * PIP_SIZE)
        previous_side = side
    return result
