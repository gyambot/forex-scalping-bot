"""Generate a descriptive weekly review of validated V1 demo records."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path

from paper_trading.demo_trade_utils import (
    is_gate_eligible,
    parse_broker_time,
    read_trade_log,
)
from paper_trading.generate_demo_metrics import calculate_demo_metrics


DEFAULT_LOG = Path(__file__).with_name("DEMO_TRADING_LOG.csv")
DEFAULT_OUTPUT = Path(__file__).with_name("DEMO_WEEKLY_REVIEW.md")


def _week_key(timestamp: datetime) -> tuple[int, int]:
    iso = timestamp.isocalendar()
    return iso.year, iso.week


def _week_label(key: tuple[int, int]) -> str:
    monday = datetime.fromisocalendar(key[0], key[1], 1).date()
    sunday = monday + timedelta(days=6)
    return f"{monday.isoformat()} through {sunday.isoformat()} (broker time)"


def _fmt(value: object, suffix: str = "") -> str:
    return "n/a" if value is None else f"{float(value):,.2f}{suffix}"


def _weekly_summary(trades: list[dict[str, str]]) -> dict[str, float | int | None]:
    result = calculate_demo_metrics(trades)["metrics"]
    assert isinstance(result, dict)
    return result


def _drawdown_events(trades: list[dict[str, str]]) -> list[tuple[str, str, float, str | None]]:
    ordered = sorted(
        trades,
        key=lambda trade: (
            parse_broker_time(trade["exit_time_broker"], "exit_time_broker"),
            trade["trade_id"],
        ),
    )
    cumulative = 0.0
    peak = 0.0
    active_peak_id: str | None = None
    trough_id: str | None = None
    trough_drawdown = 0.0
    events: list[tuple[str, str, float, str | None]] = []
    for trade in ordered:
        cumulative += float(trade["pnl_pips"])
        if cumulative >= peak and trough_id is not None:
            events.append((active_peak_id or "start of sample", trough_id, trough_drawdown, trade["trade_id"]))
            trough_id = None
            trough_drawdown = 0.0
        if cumulative > peak:
            peak = cumulative
            active_peak_id = trade["trade_id"]
        else:
            drawdown = peak - cumulative
            if drawdown > 0 and drawdown >= trough_drawdown:
                trough_id = trade["trade_id"]
                trough_drawdown = drawdown
    if trough_id is not None:
        events.append((active_peak_id or "start of sample", trough_id, trough_drawdown, None))
    return events


def _metric_change(current: object, previous: object, suffix: str = "") -> str:
    if current is None or previous is None:
        return "n/a (one week has no defined value)"
    delta = float(current) - float(previous)
    sign = "+" if delta > 0 else ""
    return f"{sign}{delta:,.2f}{suffix}"


def build_report(all_trades: list[dict[str, str]]) -> str:
    eligible = [trade for trade in all_trades if is_gate_eligible(trade)]
    eligible.sort(
        key=lambda trade: (
            parse_broker_time(trade["exit_time_broker"], "exit_time_broker"),
            trade["trade_id"],
        )
    )
    lines = [
        "# Weekly Demo Review — Breakout Scalping V1",
        "",
        "> Descriptive demo-trade summary only. This report does not recommend",
        "> strategy changes, authorize V2, or replace broker reconciliation.",
        "",
        f"- Validated completed records in source log: {len(all_trades)}",
        f"- Eligible rule-compliant demo trades in source log: {len(eligible)}",
        f"- Excluded non-compliant completed trades: {len(all_trades) - len(eligible)}",
    ]
    if not eligible:
        lines.extend(
            [
                "- Review week: no eligible demo trades available.",
                "",
                "## Trade summary",
                "",
                "- Trade count: 0",
                "- Net profit: 0.00 pips",
                "- Win rate: n/a",
                "- Profit factor: n/a",
                "- Expectancy: n/a",
                "- Expectancy R: n/a",
                "- Maximum drawdown: 0.00 pips",
                "- Average winner: n/a",
                "- Average loser: n/a",
                "- Average hold time: n/a",
                "",
                "## Best trades",
                "",
                "- None recorded.",
                "",
                "## Worst trades",
                "",
                "- None recorded.",
                "",
                "## Drawdown events",
                "",
                "- None recorded.",
                "",
                "## Metric changes",
                "",
                "- No current or prior eligible trade week is available for comparison.",
                "",
                "## Lessons observed",
                "",
                "- No eligible completed demo trades are present in the log.",
                "",
            ]
        )
        return "\n".join(lines)

    latest_key = _week_key(parse_broker_time(
        eligible[-1]["exit_time_broker"], "exit_time_broker"
    ))
    previous_week_anchor = datetime.fromisocalendar(
        latest_key[0], latest_key[1], 1
    ) - timedelta(days=7)
    previous_key = _week_key(previous_week_anchor)
    current = [
        trade
        for trade in eligible
        if _week_key(parse_broker_time(trade["exit_time_broker"], "exit_time_broker"))
        == latest_key
    ]
    previous = [
        trade
        for trade in eligible
        if _week_key(parse_broker_time(trade["exit_time_broker"], "exit_time_broker"))
        == previous_key
    ]
    summary = _weekly_summary(current)
    prior_summary = _weekly_summary(previous)

    lines.extend(["", f"- Review week: {_week_label(latest_key)}", "", "## Trade summary", ""])
    lines.extend(
        [
            f"- Trade count: {summary['trade_count']}",
            f"- Net profit: {_fmt(summary['net_profit'], ' pips')}",
            f"- Win rate: {_fmt(summary['win_rate'], '%')}",
            f"- Profit factor: {_fmt(summary['profit_factor'])}",
            f"- Expectancy: {_fmt(summary['expectancy'], ' pips/trade')}",
            f"- Expectancy R: {_fmt(summary['expectancy_r'], ' R/trade')}",
            f"- Maximum drawdown: {_fmt(summary['max_drawdown'], ' pips')}",
            f"- Average winner: {_fmt(summary['average_winner'], ' pips')}; "
            f"average loser: {_fmt(summary['average_loser'], ' pips')}",
            f"- Average hold time: {_fmt(summary['average_hold_time'], ' minutes')}",
            "",
            "## Best trades",
            "",
        ]
    )
    for trade in sorted(current, key=lambda row: float(row["pnl_pips"]), reverse=True)[:5]:
        lines.append(
            f"- `{trade['trade_id']}` — {float(trade['pnl_pips']):,.2f} pips, "
            f"{trade['direction']}, exited {trade['exit_time_broker']}."
        )
    lines.extend(["", "## Worst trades", ""])
    for trade in sorted(current, key=lambda row: float(row["pnl_pips"]))[:5]:
        lines.append(
            f"- `{trade['trade_id']}` — {float(trade['pnl_pips']):,.2f} pips, "
            f"{trade['direction']}, exited {trade['exit_time_broker']}."
        )

    lines.extend(["", "## Drawdown events", ""])
    events = _drawdown_events(current)
    if events:
        for peak_id, trough_id, depth, recovered_id in events:
            recovery = f"; recovered at `{recovered_id}`" if recovered_id else "; not recovered by week end"
            lines.append(
                f"- {_fmt(depth, ' pips')} from `{peak_id}` to `{trough_id}`{recovery}."
            )
    else:
        lines.append("- No closed-trade drawdown events in the review week.")

    lines.extend(["", "## Metric changes", ""])
    lines.extend(
        [
            f"- Trade count: {_metric_change(summary['trade_count'], prior_summary['trade_count'])}",
            f"- Net profit: {_metric_change(summary['net_profit'], prior_summary['net_profit'], ' pips')}",
            f"- Win rate: {_metric_change(summary['win_rate'], prior_summary['win_rate'], ' percentage points')}",
            f"- Profit factor: {_metric_change(summary['profit_factor'], prior_summary['profit_factor'])}",
            f"- Expectancy: {_metric_change(summary['expectancy'], prior_summary['expectancy'], ' pips/trade')}",
            f"- Expectancy R: {_metric_change(summary['expectancy_r'], prior_summary['expectancy_r'], ' R/trade')}",
            f"- Maximum drawdown: {_metric_change(summary['max_drawdown'], prior_summary['max_drawdown'], ' pips')}",
            f"- Average winner: {_metric_change(summary['average_winner'], prior_summary['average_winner'], ' pips')}",
            f"- Average loser: {_metric_change(summary['average_loser'], prior_summary['average_loser'], ' pips')}",
            f"- Average hold time: {_metric_change(summary['average_hold_time'], prior_summary['average_hold_time'], ' minutes')}",
            f"- Comparison week: {_week_label(previous_key)} ({prior_summary['trade_count']} eligible trades).",
        ]
    )

    winners = sum(float(trade["pnl_pips"]) > 0 for trade in current)
    losers = sum(float(trade["pnl_pips"]) < 0 for trade in current)
    breakeven = len(current) - winners - losers
    pnl_values = [float(trade["pnl_pips"]) for trade in current]
    lines.extend(
        [
            "",
            "## Lessons observed",
            "",
            f"- The review week contains {len(current)} eligible trades: {winners} winners, "
            f"{losers} losers, and {breakeven} breakeven; net result "
            f"{_fmt(summary['net_profit'], ' pips')}.",
        ]
    )
    if pnl_values:
        lines.append(
            f"- Observed trade outcomes ranged from {min(pnl_values):,.2f} to "
            f"{max(pnl_values):,.2f} pips; these are descriptive sample statistics."
        )
    lines.append("- No strategy recommendation is made.")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=DEFAULT_LOG, type=Path, help="demo trade CSV")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, type=Path, help="Markdown output path")
    args = parser.parse_args()
    try:
        trades = read_trade_log(args.input)
        report = build_report(trades)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Demo weekly review written: {args.output}")


if __name__ == "__main__":
    main()
