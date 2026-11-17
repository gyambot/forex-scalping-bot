"""Backtest the EMA pullback candidate using existing V1 OHLC conventions."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from dataclasses import asdict, replace
from pathlib import Path

from candidate_strategies.ema_pullback_continuation_v1 import Signal, generate_signals
from scripts.backtest import (
    BAR_DURATION, PIP_SIZE, SPREAD_PIPS, Bar, Position, Trade,
    _check_exit, _close_position, calculate_metrics, load_bars,
)


def _candidate_trade(trade: Trade, risk: float) -> Trade:
    signed_move = trade.exit_price - trade.entry_price
    if trade.direction == "short":
        signed_move = -signed_move
    return replace(trade, pnl_r=round(signed_move / risk, 4))


def run_candidate(bars: list[Bar]) -> list[Trade]:
    signals = generate_signals(bars)
    trades: list[Trade] = []
    position: Position | None = None
    pending: tuple[Signal, int] | None = None
    risk = 0.0
    for i, bar in enumerate(bars):
        entered = False
        if position is None and pending is not None:
            signal, signal_index = pending
            price = bar.open + SPREAD_PIPS * PIP_SIZE if signal.direction == "long" else bar.open
            risk = signal.atr
            signed_risk = risk if signal.direction == "long" else -risk
            if price - signed_risk <= 0 or price + 2 * signed_risk <= 0:
                raise ValueError("ATR stop or target is not a positive price")
            position = Position(signal.direction, bars[signal_index].timestamp, bar.timestamp,
                                price, price - signed_risk, price + 2 * signed_risk)
            pending = None
            entered = True
        if position is not None:
            position.bars_held += 1
            close_time = bars[i + 1].timestamp if i + 1 < len(bars) else bar.timestamp + BAR_DURATION
            trade = _check_exit(position, bar, entered, close_time)
            if trade is not None:
                trades.append(_candidate_trade(trade, risk))
                position = None
        if position is None and signals[i] is not None:
            pending = (signals[i], i)
    if position is not None:
        final = bars[-1]
        price = final.close if position.direction == "long" else final.close + SPREAD_PIPS * PIP_SIZE
        trade = _close_position(position, final, price, "end_of_data", final.timestamp + BAR_DURATION)
        trades.append(_candidate_trade(trade, risk))
    return trades


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    with args.input.open(encoding="utf-8", newline="") as file:
        bars = load_bars(file)
    trades = run_candidate(bars)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / "trades.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=Trade.__dataclass_fields__)
        writer.writeheader()
        writer.writerows(asdict(trade) for trade in trades)
    result = {
        "strategy": "EMA Pullback Continuation V1 research candidate",
        "input": str(args.input),
        "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "bars": len(bars),
        "first_bar": bars[0].timestamp.isoformat(),
        "last_bar": bars[-1].timestamp.isoformat(),
        "direction_counts": dict(Counter(trade.direction for trade in trades)),
        "performance": calculate_metrics(trades, bars),
    }
    (args.output_dir / "metrics.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
