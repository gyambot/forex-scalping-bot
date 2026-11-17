"""Re-run the weekend gap fade under fixed spread and slippage scenarios."""

import argparse
import csv
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

from candidate_strategies.london_breakout_v1 import Signal
from candidate_strategies.weekend_gap_fade_v1 import generate_signals
from scripts.backtest import (
    BAR_DURATION, PIP_SIZE, SPREAD_PIPS, Bar, Position, Trade,
    _check_exit, _close_position, calculate_metrics, load_bars,
)


@dataclass(frozen=True)
class Scenario:
    spread_pips: float
    entry_slippage_pips: float


SCENARIOS = {
    "A": Scenario(1, 0),
    "B": Scenario(2, 0),
    "C": Scenario(3, 0),
    "D": Scenario(5, 0),
    "E": Scenario(2, 1),
    "F": Scenario(3, 1),
}


def run_stress(bars: list[Bar], signals: list[Signal | None], scenario: Scenario) -> list[Trade]:
    if len(signals) != len(bars):
        raise ValueError("signals must match bars")
    if (not math.isfinite(scenario.spread_pips) or scenario.spread_pips < 0
            or not math.isfinite(scenario.entry_slippage_pips) or scenario.entry_slippage_pips < 0):
        raise ValueError("spread and slippage must be finite and nonnegative")
    position: Position | None = None
    pending: tuple[Signal, int] | None = None
    trades: list[Trade] = []
    for i, bar in enumerate(bars):
        entered = False
        if position is None and pending is not None:
            signal, signal_index = pending
            if signal.direction not in ("long", "short") or signal.atr <= 0 or not math.isfinite(signal.atr):
                raise ValueError("invalid signal direction or risk")
            sign = 1 if signal.direction == "long" else -1
            price = bar.open + (scenario.spread_pips * PIP_SIZE if sign == 1 else 0)
            price += sign * scenario.entry_slippage_pips * PIP_SIZE
            stop, target = price - sign * signal.atr, price + sign * 2 * signal.atr
            if min(price, stop, target) <= 0:
                raise ValueError("entry, stop and target must be positive")
            position = Position(signal.direction, bars[signal_index].timestamp, bar.timestamp,
                                price, stop, target)
            pending = None
            entered = True
        if position is not None:
            position.bars_held += 1
            close_time = bars[i + 1].timestamp if i + 1 < len(bars) else bar.timestamp + BAR_DURATION
            exit_bar = bar
            if position.direction == "short" and scenario.spread_pips != SPREAD_PIPS:
                # The shared helper adds its own fixed spread; shift bid OHLC so its ask matches this scenario.
                shift = (scenario.spread_pips - SPREAD_PIPS) * PIP_SIZE
                exit_bar = Bar(bar.timestamp, bar.open + shift, bar.high + shift,
                               bar.low + shift, bar.close + shift)
            trade = _check_exit(position, exit_bar, entered, close_time)
            if trade is not None:
                trades.append(trade)
                position = None
        if position is None and signals[i] is not None:
            pending = (signals[i], i)
    if position is not None:
        final = bars[-1]
        price = final.close if position.direction == "long" else final.close + scenario.spread_pips * PIP_SIZE
        trades.append(_close_position(position, final, price, "end_of_data", final.timestamp + BAR_DURATION))
    return trades


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-2025", type=Path, required=True)
    parser.add_argument("--input-2026", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    inputs = {"2025": args.input_2025, "2026": args.input_2026}
    datasets: dict[str, list[Bar]] = {}
    signals: dict[str, list[Signal | None]] = {}
    for name, path in inputs.items():
        with path.open(encoding="utf-8", newline="") as stream:
            datasets[name] = load_bars(stream)
        signals[name] = generate_signals(datasets[name])
    if datasets["2025"][-1].timestamp >= datasets["2026"][0].timestamp:
        raise ValueError("input periods must be ordered and non-overlapping")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "inputs": {name: {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                          "first_bar": datasets[name][0].timestamp.isoformat(),
                          "last_bar": datasets[name][-1].timestamp.isoformat()}
                   for name, path in inputs.items()},
        "scenarios": {},
    }
    for label, scenario in SCENARIOS.items():
        all_trades: list[Trade] = []
        periods = {}
        for name in inputs:
            trades = run_stress(datasets[name], signals[name], scenario)
            all_trades.extend(trades)
            periods[name] = calculate_metrics(trades, datasets[name])
            with (args.output_dir / f"{label}_{name}_trades.csv").open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=Trade.__dataclass_fields__)
                writer.writeheader()
                writer.writerows(asdict(trade) for trade in trades)
        periods["combined"] = calculate_metrics(all_trades, datasets["2025"] + datasets["2026"])
        result["scenarios"][label] = {"assumptions": asdict(scenario), "performance": periods}
    text = json.dumps(result, indent=2, allow_nan=False)
    (args.output_dir / "metrics.json").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
