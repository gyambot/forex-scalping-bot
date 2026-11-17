"""Generate descriptive weekly reviews from V1 M5 bars and a trade CSV."""

from __future__ import annotations

import argparse
import csv
import math
import statistics
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

from scripts.backtest import Bar, PIP_SIZE, SPREAD_PIPS, load_bars
from paper_trading.broker_time import parse_broker_timestamp


def _parse_broker_time(value: str) -> datetime:
    return parse_broker_timestamp(value, "trade timestamp")


def _session(timestamp: datetime) -> str:
    hour = timestamp.hour
    if hour < 7:
        return "Broker time (00-06)"
    if hour < 12:
        return "Broker time (07-11)"
    if hour < 21:
        return "Broker time (12-20)"
    return "Broker time (21-23)"


def _week_key(timestamp: datetime) -> tuple[int, int]:
    week = timestamp.isocalendar()
    return week.year, week.week


def _week_start(key: tuple[int, int]) -> date:
    return date.fromisocalendar(key[0], key[1], 1)


def _fmt(value: float | None, suffix: str = "") -> str:
    return "n/a" if value is None else f"{value:,.2f}{suffix}"


def _read_trades(path: Path) -> list[dict[str, object]]:
    required = {
        "direction",
        "exit_reason",
        "pnl_pips",
        "pnl_r",
        "hold_minutes",
    }
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if (
            reader.fieldnames is None
            or not required.issubset(reader.fieldnames)
            or not ({"entry_time", "entry_time_broker"} & set(reader.fieldnames))
            or not ({"exit_time", "exit_time_broker"} & set(reader.fieldnames))
            or not ({"entry_price", "actual_entry"} & set(reader.fieldnames))
            or not ({"exit_price", "actual_exit"} & set(reader.fieldnames))
        ):
            raise ValueError("trade CSV is missing required V1 or demo trade columns")
        trades = []
        for line_number, row in enumerate(reader, start=2):
            if "completed" in reader.fieldnames and row.get("completed", "").strip().lower() not in {
                "true",
                "yes",
                "1",
            }:
                continue
            try:
                entry_time = row.get("entry_time") or row.get("entry_time_broker", "")
                exit_time = row.get("exit_time") or row.get("exit_time_broker", "")
                entry_price = row.get("entry_price") or row.get("actual_entry", "")
                exit_price = row.get("exit_price") or row.get("actual_exit", "")
                pnl_pips = float(row["pnl_pips"])
                pnl_r = float(row["pnl_r"])
                hold_minutes = float(row["hold_minutes"])
                entry_spread = (
                    float(row["entry_spread_pips"])
                    if (row.get("entry_spread_pips") or "").strip()
                    else None
                )
                exit_spread = (
                    float(row["exit_spread_pips"])
                    if (row.get("exit_spread_pips") or "").strip()
                    else None
                )
                parsed_entry_time = _parse_broker_time(entry_time)
                parsed_exit_time = _parse_broker_time(exit_time)
                parsed_entry_price = float(entry_price)
                parsed_exit_price = float(exit_price)
                numeric_values = [
                    parsed_entry_price,
                    parsed_exit_price,
                    pnl_pips,
                    pnl_r,
                    hold_minutes,
                    *([entry_spread] if entry_spread is not None else []),
                    *([exit_spread] if exit_spread is not None else []),
                ]
                if not all(math.isfinite(value) for value in numeric_values):
                    raise ValueError("trade metrics and prices must be finite")
                if parsed_entry_price <= 0 or parsed_exit_price <= 0 or hold_minutes < 0:
                    raise ValueError("prices must be positive and hold time nonnegative")
                if entry_spread is not None and entry_spread < 0:
                    raise ValueError("entry spread must be nonnegative")
                if exit_spread is not None and exit_spread < 0:
                    raise ValueError("exit spread must be nonnegative")
                direction = row["direction"].strip().lower()
                if direction not in {"long", "short"}:
                    raise ValueError("direction must be long or short")
                if parsed_exit_time <= parsed_entry_time:
                    raise ValueError("exit time must follow entry time")
                trades.append(
                    {
                        "direction": direction,
                        "entry_time": parsed_entry_time,
                        "exit_time": parsed_exit_time,
                        "entry_price": parsed_entry_price,
                        "exit_price": parsed_exit_price,
                        "exit_reason": row["exit_reason"],
                        "pnl_pips": pnl_pips,
                        "pnl_r": pnl_r,
                        "hold_minutes": hold_minutes,
                        "entry_spread_pips": entry_spread,
                        "exit_spread_pips": exit_spread,
                    }
                )
            except (TypeError, ValueError) as exc:
                raise ValueError(f"trade CSV line {line_number}: {exc}") from exc
    return trades


def build_report(bars: list[Bar], trades: list[dict[str, object]]) -> str:
    bars_by_week: dict[tuple[int, int], list[Bar]] = defaultdict(list)
    for bar in bars:
        bars_by_week[_week_key(bar.timestamp)].append(bar)

    trades_by_week: dict[tuple[int, int], list[dict[str, object]]] = defaultdict(list)
    for trade in trades:
        trades_by_week[_week_key(trade["exit_time"])].append(trade)

    weekly_ranges = {
        week: statistics.mean((bar.high - bar.low) / PIP_SIZE for bar in week_bars)
        for week, week_bars in bars_by_week.items()
    }
    median_weekly_range = statistics.median(weekly_ranges.values()) if weekly_ranges else None

    ordered_trades = sorted(trades, key=lambda trade: trade["exit_time"])
    cumulative = 0.0
    peak = 0.0
    peak_time: datetime | None = None
    drawdown_by_week: dict[tuple[int, int], tuple[float, datetime | None, datetime | None]] = {}
    for trade in ordered_trades:
        cumulative += float(trade["pnl_pips"])
        if cumulative > peak:
            peak = cumulative
            peak_time = trade["exit_time"]
        drawdown = peak - cumulative
        week = _week_key(trade["exit_time"])
        previous = drawdown_by_week.get(week)
        if previous is None or drawdown > previous[0]:
            drawdown_by_week[week] = (drawdown, peak_time, trade["exit_time"])

    all_bars = [bar.timestamp for bar in bars]
    period = (
        f"{min(all_bars).date().isoformat()} to {max(all_bars).date().isoformat()}"
        if all_bars
        else "no bar data"
    )
    lines = [
        "# Weekly Review — Breakout Scalping V1",
        "",
        "> Historical backtest breakdown, not live or demo performance. Fixed source-clock",
        "> buckets and OHLC volatility are descriptive only; they do not authorize a",
        "> strategy change. Actual variable spread is unavailable in bid-bar data.",
        "",
        f"- Data period: {period}",
        f"- Completed trades reviewed: {len(trades)}",
        "- Time bands use each input timestamp's displayed clock hour; they are descriptive only.",
        f"- Spread: V1 models a constant {SPREAD_PIPS:.1f} pip; this report cannot measure historical or demo spread variation.",
        "- Volatility proxy: mean M5 high-low range in pips per ISO week; not a strategy filter.",
        "- Drawdown: trade-close cumulative P&L drawdown from the prior cumulative peak, in pips.",
        "",
        "## Weekly reviews",
        "",
    ]

    weeks = sorted(set(bars_by_week) | set(trades_by_week))
    for week in weeks:
        week_start = _week_start(week)
        week_end = date.fromordinal(week_start.toordinal() + 6)
        week_trades = sorted(
            trades_by_week.get(week, []), key=lambda trade: trade["exit_time"]
        )
        week_bars = bars_by_week.get(week, [])
        range_mean = weekly_ranges.get(week)
        total_pnl = sum(float(trade["pnl_pips"]) for trade in week_trades)
        count = len(week_trades)
        wins = [float(trade["pnl_pips"]) for trade in week_trades if float(trade["pnl_pips"]) > 0]
        losses = [float(trade["pnl_pips"]) for trade in week_trades if float(trade["pnl_pips"]) < 0]
        expectancy_r = (
            statistics.mean(float(trade["pnl_r"]) for trade in week_trades)
            if week_trades
            else None
        )

        lines.extend(
            [
                f"### {week_start.isoformat()} to {week_end.isoformat()} (ISO {week[0]}-W{week[1]:02d})",
                "",
                f"- Completed trades: {count}; net P&L: {_fmt(total_pnl, ' pips')}; expectancy: {_fmt(total_pnl / count if count else None, ' pips')} / {_fmt(expectancy_r, ' R')}.",
            ]
        )
        if count:
            profit_factor = sum(wins) / abs(sum(losses)) if losses else None
            win_rate = len(wins) / count * 100
            avg_hold = statistics.mean(float(trade["hold_minutes"]) for trade in week_trades)
            session_results: dict[str, list[float]] = defaultdict(list)
            for trade in week_trades:
                session_results[_session(trade["entry_time"])].append(float(trade["pnl_pips"]))
            ranked_sessions = sorted(
                session_results.items(), key=lambda item: sum(item[1]), reverse=True
            )
            best_session = ranked_sessions[0]
            worst_session = ranked_sessions[-1]
            top_winners = sorted(week_trades, key=lambda trade: float(trade["pnl_pips"]), reverse=True)[:3]
            top_losers = sorted(week_trades, key=lambda trade: float(trade["pnl_pips"]))[:3]
            dd, dd_peak_time, dd_trough_time = drawdown_by_week.get(week, (0.0, None, None))
            trading_days = len({bar.timestamp.date() for bar in week_bars})
            lines.extend(
                [
                    f"- Required metrics: profit factor {_fmt(profit_factor)}; win rate {_fmt(win_rate, '%')}; average trade {_fmt(total_pnl / count, ' pips')}; average hold {_fmt(avg_hold, ' min')}; trades/day {_fmt(count / trading_days if trading_days else None)}; maximum trade-close drawdown this week {_fmt(dd, ' pips')}.",
                    f"- Best session by net P&L: {best_session[0]}, {_fmt(sum(best_session[1]), ' pips')} across {len(best_session[1])} trades.",
                    f"- Worst session by net P&L: {worst_session[0]}, {_fmt(sum(worst_session[1]), ' pips')} across {len(worst_session[1])} trades.",
                    "- Largest winners: " + "; ".join(
                        f"{trade['direction']} {_fmt(float(trade['pnl_pips']), ' pips')} (entry {trade['entry_time'].isoformat()})"
                        for trade in top_winners
                    ),
                    "- Largest losers: " + "; ".join(
                        f"{trade['direction']} {_fmt(float(trade['pnl_pips']), ' pips')} (entry {trade['entry_time'].isoformat()})"
                        for trade in top_losers
                    ),
                    (
                        f"- Drawdown event: {_fmt(dd, ' pips')} from running peak "
                        f"{dd_peak_time.isoformat() if dd_peak_time else 'before sample'} "
                        f"to trough {dd_trough_time.isoformat() if dd_trough_time else 'n/a'}."
                    ),
                ]
            )
        else:
            lines.extend(
                [
                    "- Best/worst sessions, largest winners/losers, and trade drawdown events: no completed trades this week.",
                ]
            )
        if range_mean is None:
            lines.append("- Volatility analysis: no M5 bars available.")
        else:
            comparison = (
                "at the weekly median"
                if range_mean == median_weekly_range
                else "above the weekly median"
                if range_mean > median_weekly_range
                else "below the weekly median"
            )
            lines.append(
                f"- Volatility analysis: average M5 range {_fmt(range_mean, ' pips')}, "
                f"{comparison} of {_fmt(median_weekly_range, ' pips')} across data weeks."
            )
        entry_spreads = [
            float(trade["entry_spread_pips"])
            for trade in week_trades
            if trade.get("entry_spread_pips") is not None
        ]
        exit_spreads = [
            float(trade["exit_spread_pips"])
            for trade in week_trades
            if trade.get("exit_spread_pips") is not None
        ]
        if entry_spreads or exit_spreads:
            spread_summary = (
                f"observed entry spread avg {_fmt(statistics.mean(entry_spreads), ' pips')}"
                if entry_spreads
                else "entry spread unavailable"
            )
            if exit_spreads:
                spread_summary += f"; exit spread avg {_fmt(statistics.mean(exit_spreads), ' pips')}"
            lines.append(f"- Spread analysis: {spread_summary}.")
        else:
            lines.append(
                f"- Spread analysis: modeled at a flat {SPREAD_PIPS:.1f} pip per V1; no actual bid/ask spread observations are available."
            )
        lines.extend(
            [
                "- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bars", required=True, type=Path, help="M5 bid OHLC CSV with explicit source offsets")
    parser.add_argument("--trades", required=True, type=Path, help="V1 trades CSV")
    parser.add_argument("--output", required=True, type=Path, help="Markdown review destination")
    args = parser.parse_args()
    try:
        with args.bars.open("r", newline="", encoding="utf-8-sig") as file:
            bars = load_bars(file)
        trades = _read_trades(args.trades)
        report = build_report(bars, trades)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Weekly review written: {args.output}")


if __name__ == "__main__":
    main()
