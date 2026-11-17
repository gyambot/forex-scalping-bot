"""Run isolated liquidity-sweep research using V1 OHLC execution helpers."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from candidate_strategies.liquidity_sweep_mss_v1 import Signal, generate_signals
from scripts.backtest import (
    BAR_DURATION, PIP_SIZE, SPREAD_PIPS, STOP_LOSS_PIPS, TAKE_PROFIT_R,
    Bar, Position, Trade, _check_exit, _close_position, calculate_metrics, load_bars,
)


def run_candidate(bars: list[Bar]) -> tuple[list[Trade], list[Signal]]:
    signals = generate_signals(bars)
    trades: list[Trade] = []
    evidence: list[Signal] = []
    position: Position | None = None
    pending: tuple[Signal, int] | None = None
    active_signal: Signal | None = None
    for i, bar in enumerate(bars):
        entered = False
        if position is None and pending is not None:
            active_signal, signal_index = pending
            direction = active_signal.direction
            price = bar.open + SPREAD_PIPS * PIP_SIZE if direction == "long" else bar.open
            distance = STOP_LOSS_PIPS * PIP_SIZE * (1 if direction == "long" else -1)
            position = Position(direction, bars[signal_index].timestamp, bar.timestamp,
                                price, price - distance, price + TAKE_PROFIT_R * distance)
            pending = None
            entered = True
        if position is not None:
            position.bars_held += 1
            close_time = bars[i + 1].timestamp if i + 1 < len(bars) else bar.timestamp + BAR_DURATION
            trade = _check_exit(position, bar, entered, close_time)
            if trade is not None:
                assert active_signal is not None
                trades.append(trade)
                evidence.append(active_signal)
                position = None
        if position is None and signals[i] is not None:
            pending = (signals[i], i)
    if position is not None:
        assert active_signal is not None
        final = bars[-1]
        price = final.close if position.direction == "long" else final.close + SPREAD_PIPS * PIP_SIZE
        trades.append(_close_position(position, final, price, "end_of_data", final.timestamp + BAR_DURATION))
        evidence.append(active_signal)
    return trades, evidence


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    with args.input.open(encoding="utf-8", newline="") as file:
        bars = load_bars(file)
    trades, evidence = run_candidate(bars)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    fields = [*Trade.__dataclass_fields__, "sweep_time", "pivot_time",
              "pivot_price", "structure_time", "structure_price"]
    with (args.output_dir / "trades.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for trade, signal in zip(trades, evidence):
            writer.writerow({
                **asdict(trade), "sweep_time": bars[signal.sweep_index].timestamp.isoformat(),
                "pivot_time": bars[signal.pivot_index].timestamp.isoformat(),
                "pivot_price": signal.pivot_price,
                "structure_time": bars[signal.structure_index].timestamp.isoformat(),
                "structure_price": signal.structure_price,
            })
    result = {
        "strategy": "Liquidity Sweep MSS V1 research candidate",
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
