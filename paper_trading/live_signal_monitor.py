"""Poll MT5 for completed M5 bars and append read-only V1 signal states."""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

from paper_trading import mt5_connector
from paper_trading.live_signal_engine import (
    SIGNAL_CSV_FIELDS,
    LiveSignal,
    evaluate_v1_signal,
)
from paper_trading.mt5_price_feed import get_recent_m5_bars
from scripts.backtest import LOOKBACK_BARS


DEFAULT_LOG = Path(__file__).with_name("LIVE_SIGNAL_LOG.csv")


def _last_logged_timestamp(path: Path) -> str | None:
    if not path.exists() or path.stat().st_size == 0:
        return None
    with path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if tuple(reader.fieldnames or ()) != SIGNAL_CSV_FIELDS:
            raise ValueError(f"signal log header must be: {','.join(SIGNAL_CSV_FIELDS)}")
        last_timestamp = None
        for row in reader:
            if None in row:
                raise ValueError("signal log contains a row with extra fields")
            last_timestamp = row["timestamp"]
        return last_timestamp


def append_signal(path: Path, signal: LiveSignal) -> None:
    """Append one signal state, creating the required CSV header if needed."""
    needs_header = not path.exists() or path.stat().st_size == 0
    if not needs_header:
        with path.open("r", newline="", encoding="utf-8") as existing:
            reader = csv.reader(existing)
            header = tuple(next(reader, ()))
        if header != SIGNAL_CSV_FIELDS:
            raise ValueError(f"signal log header must be: {','.join(SIGNAL_CSV_FIELDS)}")

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=SIGNAL_CSV_FIELDS)
        if needs_header:
            writer.writeheader()
        writer.writerow(signal.to_csv_row())
        file.flush()


def monitor_signals(
    poll_interval_seconds: float = 5.0,
    log_path: Path = DEFAULT_LOG,
    max_polls: int | None = None,
) -> None:
    """Monitor completed bars; each bar state is logged at most once."""
    if poll_interval_seconds <= 0:
        raise ValueError("poll interval must be positive")
    if max_polls is not None and max_polls <= 0:
        raise ValueError("max_polls must be positive when provided")

    mt5_connector.initialize_connection()
    try:
        last_timestamp = _last_logged_timestamp(log_path)
        polls = 0
        while max_polls is None or polls < max_polls:
            bars = get_recent_m5_bars(count=LOOKBACK_BARS + 1)
            signal = evaluate_v1_signal(bars)
            if signal.timestamp != last_timestamp:
                append_signal(log_path, signal)
                print(
                    f"{signal.timestamp} {signal.signal_type} "
                    f"close={signal.current_price:.5f}"
                )
                last_timestamp = signal.timestamp
            polls += 1
            if max_polls is None or polls < max_polls:
                time.sleep(poll_interval_seconds)
    finally:
        mt5_connector.shutdown_connection()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval", type=float, default=5.0, help="poll interval in seconds")
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG, help="signal CSV path")
    args = parser.parse_args()
    if args.interval <= 0:
        parser.error("--interval must be positive")
    try:
        monitor_signals(poll_interval_seconds=args.interval, log_path=args.log)
    except KeyboardInterrupt:
        print("Signal monitoring stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
