"""Backtest a registered isolated research signal generator."""

import argparse
import csv
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from candidate_strategies import bollinger_reentry_v1, daily_momentum_v1, weekend_gap_fade_v1
from candidate_strategies.backtest_opening_range_breakout_v1 import run_signals
from scripts.backtest import Trade, calculate_metrics, load_bars


GENERATORS = {
    "bollinger_reentry_v1": bollinger_reentry_v1.generate_signals,
    "daily_momentum_v1": daily_momentum_v1.generate_signals,
    "weekend_gap_fade_v1": weekend_gap_fade_v1.generate_signals,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strategy", choices=GENERATORS, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    with args.input.open(encoding="utf-8", newline="") as stream:
        bars = load_bars(stream)
    trades = run_signals(bars, GENERATORS[args.strategy](bars))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / "trades.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=Trade.__dataclass_fields__)
        writer.writeheader()
        writer.writerows(asdict(trade) for trade in trades)
    result = {
        "strategy": args.strategy,
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
