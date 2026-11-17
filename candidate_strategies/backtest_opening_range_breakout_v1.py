"""Run opening-range research using the existing isolated execution model."""

import argparse
import csv
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from candidate_strategies.backtest_london_breakout_v1 import _with_actual_risk
from candidate_strategies.london_breakout_v1 import Signal
from candidate_strategies.opening_range_breakout_v1 import generate_signals
from scripts.backtest import (
    BAR_DURATION, PIP_SIZE, SPREAD_PIPS, Bar, Position, Trade,
    _check_exit, _close_position, calculate_metrics, load_bars,
)


def run_signals(bars: list[Bar], signals: list[Signal | None]) -> list[Trade]:
    if len(bars) != len(signals):
        raise ValueError("signals must match bars")
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
            distance = risk if signal.direction == "long" else -risk
            if price - distance <= 0 or price + 2 * distance <= 0:
                raise ValueError("stop or target is not a positive price")
            position = Position(signal.direction, bars[signal_index].timestamp, bar.timestamp,
                                price, price - distance, price + 2 * distance)
            pending = None
            entered = True
        if position is not None:
            position.bars_held += 1
            close_time = bars[i + 1].timestamp if i + 1 < len(bars) else bar.timestamp + BAR_DURATION
            trade = _check_exit(position, bar, entered, close_time)
            if trade is not None:
                trades.append(_with_actual_risk(trade, risk))
                position = None
        if position is None and signals[i] is not None:
            pending = (signals[i], i)
    if position is not None:
        final = bars[-1]
        price = final.close if position.direction == "long" else final.close + SPREAD_PIPS * PIP_SIZE
        trades.append(_with_actual_risk(
            _close_position(position, final, price, "end_of_data", final.timestamp + BAR_DURATION), risk
        ))
    return trades


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    with args.input.open(encoding="utf-8", newline="") as stream:
        bars = load_bars(stream)
    signals = generate_signals(bars)
    trades = run_signals(bars, signals)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / "trades.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=Trade.__dataclass_fields__)
        writer.writeheader()
        writer.writerows(asdict(trade) for trade in trades)
    result = {
        "strategy": "Opening Range Breakout V1",
        "input": str(args.input),
        "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "bars": len(bars),
        "first_bar": bars[0].timestamp.isoformat(),
        "last_bar": bars[-1].timestamp.isoformat(),
        "performance": calculate_metrics(trades, bars),
        "by_direction": {direction: calculate_metrics(
            [t for t in trades if t.direction == direction], bars
        ) for direction in ("long", "short")},
    }
    text = json.dumps(result, indent=2, allow_nan=False)
    (args.output_dir / "metrics.json").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
