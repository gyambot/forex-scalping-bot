"""Reproducible OHLC backtest runner for the frozen Breakout Scalping V1."""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, TextIO

from paper_trading.broker_time import parse_broker_timestamp


TIMEFRAME_MINUTES = 5
LOOKBACK_BARS = 20
STOP_LOSS_PIPS = 10.0
TAKE_PROFIT_R = 2.0
SPREAD_PIPS = 1.0
PIP_SIZE = 0.0001
BAR_DURATION = timedelta(minutes=TIMEFRAME_MINUTES)


@dataclass(frozen=True)
class Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float


@dataclass
class Position:
    direction: str
    signal_time: datetime
    entry_time: datetime
    entry_price: float
    stop_price: float
    target_price: float
    bars_held: int = 0


@dataclass
class Trade:
    direction: str
    signal_time: str
    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    stop_price: float
    target_price: float
    exit_reason: str
    pnl_pips: float
    pnl_r: float
    bars_held: int
    hold_minutes: int


def _parse_timestamp(value: str) -> datetime:
    timestamp = parse_broker_timestamp(value, "timestamp")
    if timestamp.second != 0 or timestamp.microsecond != 0 or timestamp.minute % 5:
        raise ValueError("timestamp is not on an M5 boundary")
    return timestamp


def load_bars(stream: TextIO) -> list[Bar]:
    reader = csv.DictReader(stream)
    required = ["timestamp", "open", "high", "low", "close"]
    if reader.fieldnames != required:
        raise ValueError("CSV header must contain exactly: timestamp,open,high,low,close")

    bars: list[Bar] = []
    previous_timestamp: datetime | None = None
    for line_number, row in enumerate(reader, start=2):
        if None in row:
            raise ValueError(f"line {line_number}: too many CSV fields")
        try:
            timestamp = _parse_timestamp(row["timestamp"])
            prices = [float(row[key]) for key in ("open", "high", "low", "close")]
        except (TypeError, ValueError) as exc:
            raise ValueError(f"line {line_number}: {exc}") from exc
        if not all(math.isfinite(price) and price > 0 for price in prices):
            raise ValueError(f"line {line_number}: prices must be finite and positive")
        open_price, high, low, close = prices
        if low > min(open_price, close) or high < max(open_price, close) or low > high:
            raise ValueError(f"line {line_number}: inconsistent OHLC values")
        if previous_timestamp is not None and timestamp <= previous_timestamp:
            raise ValueError(f"line {line_number}: timestamps must be strictly increasing")
        bars.append(Bar(timestamp, open_price, high, low, close))
        previous_timestamp = timestamp
    if not bars:
        raise ValueError("CSV contains no data bars")
    return bars


def _close_position(
    position: Position,
    bar: Bar,
    exit_price: float,
    reason: str,
    exit_time: datetime,
) -> Trade:
    direction_sign = 1.0 if position.direction == "long" else -1.0
    pnl_pips = direction_sign * (exit_price - position.entry_price) / PIP_SIZE
    bars_held = position.bars_held
    return Trade(
        direction=position.direction,
        signal_time=position.signal_time.isoformat(),
        entry_time=position.entry_time.isoformat(),
        exit_time=exit_time.isoformat(),
        entry_price=position.entry_price,
        exit_price=exit_price,
        stop_price=position.stop_price,
        target_price=position.target_price,
        exit_reason=reason,
        pnl_pips=round(pnl_pips, 4),
        pnl_r=round(pnl_pips / STOP_LOSS_PIPS, 4),
        bars_held=bars_held,
        hold_minutes=bars_held * TIMEFRAME_MINUTES,
    )


def _check_exit(
    position: Position,
    bar: Bar,
    is_entry_bar: bool,
    bar_close_time: datetime,
) -> Trade | None:
    spread = SPREAD_PIPS * PIP_SIZE
    if position.direction == "long":
        if not is_entry_bar:
            if bar.open <= position.stop_price:
                return _close_position(position, bar, bar.open, "stop_loss_gap", bar_close_time)
            if bar.open >= position.target_price:
                return _close_position(position, bar, position.target_price, "take_profit", bar_close_time)
        stop_hit = bar.low <= position.stop_price
        target_hit = bar.high >= position.target_price
        if stop_hit:
            return _close_position(position, bar, position.stop_price, "stop_loss", bar_close_time)
        if target_hit:
            return _close_position(position, bar, position.target_price, "take_profit", bar_close_time)
    else:
        ask_open = bar.open + spread
        ask_high = bar.high + spread
        ask_low = bar.low + spread
        if not is_entry_bar:
            if ask_open >= position.stop_price:
                return _close_position(position, bar, ask_open, "stop_loss_gap", bar_close_time)
            if ask_open <= position.target_price:
                return _close_position(position, bar, position.target_price, "take_profit", bar_close_time)
        stop_hit = ask_high >= position.stop_price
        target_hit = ask_low <= position.target_price
        if stop_hit:
            return _close_position(position, bar, position.stop_price, "stop_loss", bar_close_time)
        if target_hit:
            return _close_position(position, bar, position.target_price, "take_profit", bar_close_time)
    return None


def breakout_signal_at(bars: list[Bar], index: int) -> tuple[str | None, float | None]:
    """Return the raw V1 breakout direction and prior-channel level for one bar."""
    if index < LOOKBACK_BARS:
        return None, None
    prior_bars = bars[index - LOOKBACK_BARS : index]
    prior_high = max(item.high for item in prior_bars)
    prior_low = min(item.low for item in prior_bars)
    if bars[index].close > prior_high:
        return "long", prior_high
    if bars[index].close < prior_low:
        return "short", prior_low
    return None, None


def run_backtest(bars: list[Bar]) -> list[Trade]:
    trades: list[Trade] = []
    position: Position | None = None
    pending: tuple[str, datetime] | None = None

    for index, bar in enumerate(bars):
        entered_this_bar = False
        if position is None and pending is not None:
            direction, signal_time = pending
            spread = SPREAD_PIPS * PIP_SIZE
            entry_price = bar.open + spread if direction == "long" else bar.open
            stop_distance = STOP_LOSS_PIPS * PIP_SIZE
            signed_distance = stop_distance if direction == "long" else -stop_distance
            position = Position(
                direction=direction,
                signal_time=signal_time,
                entry_time=bar.timestamp,
                entry_price=entry_price,
                stop_price=entry_price - signed_distance,
                target_price=entry_price + signed_distance * TAKE_PROFIT_R,
            )
            pending = None
            entered_this_bar = True

        if position is not None:
            position.bars_held += 1
            bar_close_time = (
                bars[index + 1].timestamp
                if index + 1 < len(bars)
                else bar.timestamp + BAR_DURATION
            )
            trade = _check_exit(position, bar, entered_this_bar, bar_close_time)
            if trade is not None:
                trades.append(trade)
                position = None

        if position is None:
            direction, _ = breakout_signal_at(bars, index)
            if direction is not None:
                pending = (direction, bar.timestamp)

    if position is not None:
        final_bar = bars[-1]
        exit_price = (
            final_bar.close
            if position.direction == "long"
            else final_bar.close + SPREAD_PIPS * PIP_SIZE
        )
        trades.append(
            _close_position(
                position,
                final_bar,
                exit_price,
                "end_of_data",
                final_bar.timestamp + BAR_DURATION,
            )
        )
    return trades


def calculate_metrics(trades: Iterable[Trade], bars: list[Bar]) -> dict[str, object]:
    trade_list = list(trades)
    pnls = [trade.pnl_pips for trade in trade_list]
    wins = [pnl for pnl in pnls if pnl > 0]
    losses = [pnl for pnl in pnls if pnl < 0]
    cumulative = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for pnl in pnls:
        cumulative += pnl
        peak = max(peak, cumulative)
        max_drawdown = max(max_drawdown, peak - cumulative)
    active_days = len({bar.timestamp.date() for bar in bars})
    count = len(trade_list)
    return {
        "net_profit_pips": round(sum(pnls), 4),
        "profit_factor": round(sum(wins) / abs(sum(losses)), 4) if losses else None,
        "expectancy_pips": round(sum(pnls) / count, 4) if count else None,
        "expectancy_r": round(
            sum(trade.pnl_r for trade in trade_list) / count, 4
        )
        if count
        else None,
        "win_rate_pct": round(len(wins) / count * 100, 4) if count else None,
        "max_drawdown_pips": round(max_drawdown, 4),
        "avg_trade_pips": round(sum(pnls) / count, 4) if count else None,
        "avg_hold_minutes": round(
            sum(trade.hold_minutes for trade in trade_list) / count, 4
        )
        if count
        else None,
        "trades_per_day": round(count / active_days, 4) if active_days else None,
        "trade_count": count,
        "active_data_days": active_days,
    }


def write_results(
    trades: list[Trade], bars: list[Bar], output_dir: Path
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    trade_rows = [asdict(trade) for trade in trades]
    with (output_dir / "trades.csv").open("w", newline="", encoding="utf-8") as file:
        fieldnames = list(Trade.__dataclass_fields__)
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(trade_rows)

    metrics: dict[str, object] = {
        "strategy": "Breakout Scalping V1",
        "instrument": "EURUSD",
        "timeframe": "M5",
        "parameters": {
            "lookback_bars": LOOKBACK_BARS,
            "stop_loss_pips": STOP_LOSS_PIPS,
            "take_profit_r": TAKE_PROFIT_R,
            "spread_pips": SPREAD_PIPS,
            "pip_size": PIP_SIZE,
        },
        "data": {
            "first_bar_time": bars[0].timestamp.isoformat(),
            "last_bar_time": bars[-1].timestamp.isoformat(),
            "bar_count": len(bars),
        },
        "performance": calculate_metrics(trades, bars),
    }
    with (output_dir / "metrics.json").open("w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=2)
        file.write("\n")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="EURUSD M5 bid OHLC CSV")
    parser.add_argument("--output-dir", required=True, type=Path, help="directory for run outputs")
    args = parser.parse_args()
    try:
        with args.input.open("r", newline="", encoding="utf-8-sig") as file:
            bars = load_bars(file)
        trades = run_backtest(bars)
        metrics = write_results(trades, bars, args.output_dir)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(metrics["performance"], indent=2))


if __name__ == "__main__":
    main()
