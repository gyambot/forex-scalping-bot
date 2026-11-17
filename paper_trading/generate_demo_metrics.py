"""Generate validated metrics from the completed V1 demo-trade log."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from paper_trading.demo_trade_utils import (
    STRATEGY_VERSION,
    is_gate_eligible,
    parse_broker_time,
    read_trade_log,
)


DEFAULT_LOG = Path(__file__).with_name("DEMO_TRADING_LOG.csv")
DEFAULT_OUTPUT = Path(__file__).with_name("DEMO_METRICS.json")


def _rounded(value: float | None, digits: int = 4) -> float | None:
    return None if value is None else round(value, digits)


def calculate_demo_metrics(trades: list[dict[str, str]]) -> dict[str, object]:
    """Calculate the specification's metrics from gate-eligible completed trades."""
    eligible = [trade for trade in trades if is_gate_eligible(trade)]
    ordered = sorted(
        eligible,
        key=lambda trade: (
            parse_broker_time(trade["exit_time_broker"], "exit_time_broker"),
            trade["trade_id"],
        ),
    )
    pnl_values = [float(trade["pnl_pips"]) for trade in ordered]
    wins = [value for value in pnl_values if value > 0]
    losses = [value for value in pnl_values if value < 0]
    net_profit = sum(pnl_values)
    cumulative = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for pnl in pnl_values:
        cumulative += pnl
        peak = max(peak, cumulative)
        max_drawdown = max(max_drawdown, peak - cumulative)

    count = len(ordered)
    entry_spreads = [
        float(trade["entry_spread_pips"])
        for trade in ordered
        if not trade["entry_spread_pips"].lower().startswith("unavailable:")
    ]
    exit_spreads = [
        float(trade["exit_spread_pips"])
        for trade in ordered
        if not trade["exit_spread_pips"].lower().startswith("unavailable:")
    ]
    metrics: dict[str, float | int | None] = {
        "trade_count": count,
        "win_rate": _rounded(100 * len(wins) / count, 2) if count else None,
        "profit_factor": (
            _rounded(sum(wins) / abs(sum(losses))) if losses else None
        ),
        "expectancy": _rounded(statistics.mean(pnl_values)) if count else None,
        "net_profit": _rounded(net_profit),
        "max_drawdown": _rounded(max_drawdown),
        "average_winner": _rounded(statistics.mean(wins)) if wins else None,
        "average_loser": _rounded(statistics.mean(losses)) if losses else None,
        "average_hold_time": _rounded(
            statistics.mean(float(trade["hold_minutes"]) for trade in ordered)
        )
        if count
        else None,
        "expectancy_r": (
            _rounded(statistics.mean(float(trade["pnl_r"]) for trade in ordered))
            if count
            else None
        ),
    }
    return {
        "strategy_version": STRATEGY_VERSION,
        "account_type": "DEMO",
        "account_aliases": sorted({trade["account_alias"] for trade in eligible}),
        "eligible_trade_count": count,
        "excluded_noncompliant_trade_count": len(trades) - count,
        "reporting_period_broker_time": (
            {
                "first_exit": ordered[0]["exit_time_broker"],
                "last_exit": ordered[-1]["exit_time_broker"],
            }
            if ordered
            else None
        ),
        "metrics": metrics,
        "average_spread_pips": {
            "entry": _rounded(statistics.mean(entry_spreads)) if entry_spreads else None,
            "entry_observations": len(entry_spreads),
            "exit": _rounded(statistics.mean(exit_spreads)) if exit_spreads else None,
            "exit_observations": len(exit_spreads),
            "missing_observations": 2 * count - len(entry_spreads) - len(exit_spreads),
        },
        "metric_units": {
            "trade_count": "trades",
            "win_rate": "percent",
            "profit_factor": "ratio",
            "expectancy": "pips per trade",
            "net_profit": "pips",
            "max_drawdown": "pips (closed-trade)",
            "average_winner": "pips",
            "average_loser": "pips",
            "average_hold_time": "minutes",
            "expectancy_r": "R per trade",
        },
        "drawdown_method": (
            "Peak-to-trough drawdown of cumulative net realized P&L in exit-time order, "
            "starting at zero; closed trades only, excludes intratrade equity drawdown."
        ),
        "pnl_scope": "Net pips after recorded costs; account-currency metrics are not included.",
        "profit_factor_note": "null means there were no losing trades or no eligible trades",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=DEFAULT_LOG, type=Path, help="demo trade CSV")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, type=Path, help="JSON output path")
    args = parser.parse_args()
    try:
        trades = read_trade_log(args.input)
        result = calculate_demo_metrics(trades)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8"
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Demo metrics written: {args.output}")


if __name__ == "__main__":
    main()
