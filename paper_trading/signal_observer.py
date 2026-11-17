"""Observe completed MT5 M5 bars and log frozen V1 signal states only."""

from __future__ import annotations

import argparse
import csv
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from paper_trading import mt5_connector
from paper_trading.live_signal_engine import evaluate_v1_signal
from paper_trading.mt5_price_feed import get_recent_m5_bars
from paper_trading.broker_time import now_broker_time, parse_broker_timestamp, parse_broker_timezone
from scripts.backtest import LOOKBACK_BARS


SYMBOL = "EURUSD"
BAR_DURATION = timedelta(minutes=5)
CLOCK_TOLERANCE_SECONDS = 120
DEFAULT_LOG = Path(__file__).with_name("SIGNAL_OBSERVATION_LOG.csv")
DEFAULT_REPORT = Path(__file__).with_name("SIGNAL_OBSERVATION_REPORT.md")
OBSERVATION_FIELDS = (
    "timestamp",
    "signal_type",
    "symbol",
    "bar_timestamp",
    "breakout_level",
    "close_price",
    "raw_signal_status",
)


def _broker_now() -> str:
    offset = mt5_connector.get_broker_utc_offset()
    return now_broker_time(parse_broker_timezone(offset)).isoformat()


def _parse_broker_time(value: str, field: str) -> datetime:
    return parse_broker_timestamp(value, field)


def _read_observations(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if tuple(reader.fieldnames or ()) != OBSERVATION_FIELDS:
            raise ValueError(
                f"observation log header must be: {','.join(OBSERVATION_FIELDS)}"
            )
        rows: list[dict[str, str]] = []
        for line_number, row in enumerate(reader, start=2):
            if None in row or any(row.get(field) is None for field in OBSERVATION_FIELDS):
                raise ValueError(f"observation log line {line_number} has invalid fields")
            rows.append(row)
    return rows


def _append_row(path: Path, row: dict[str, Any]) -> None:
    needs_header = not path.exists() or path.stat().st_size == 0
    if not needs_header:
        with path.open("r", newline="", encoding="utf-8") as existing:
            header = tuple(next(csv.reader(existing), ()))
        if header != OBSERVATION_FIELDS:
            raise ValueError(
                f"observation log header must be: {','.join(OBSERVATION_FIELDS)}"
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=OBSERVATION_FIELDS)
        if needs_header:
            writer.writeheader()
        writer.writerow(row)
        file.flush()


def observe_latest_bar(log_path: Path = DEFAULT_LOG) -> dict[str, Any] | None:
    """Evaluate the latest completed M5 bar and append it only once.

    Returns the appended row, or None when this bar timestamp is already logged.
    """
    rows = _read_observations(log_path)
    seen_bar_timestamps = {row["bar_timestamp"] for row in rows}

    bars = get_recent_m5_bars(count=LOOKBACK_BARS + 1, symbol=SYMBOL)
    signal = evaluate_v1_signal(bars)
    if signal.timestamp in seen_bar_timestamps:
        return None

    row: dict[str, Any] = {
        "timestamp": _broker_now(),
        "signal_type": signal.signal_type,
        "symbol": SYMBOL,
        "bar_timestamp": signal.timestamp,
        "breakout_level": (
            "" if signal.breakout_level is None else signal.breakout_level
        ),
        "close_price": signal.current_price,
        "raw_signal_status": (
            "BREAKOUT" if signal.signal_type in {"LONG", "SHORT"} else "NO_BREAKOUT"
        ),
    }
    _append_row(log_path, row)
    return row


def _timestamp_anomalies(rows: list[dict[str, str]]) -> list[str]:
    anomalies: list[str] = []
    previous_bar_time: datetime | None = None
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        observation_time = _parse_broker_time(row["timestamp"], f"row {index} timestamp")
        bar_time = _parse_broker_time(row["bar_timestamp"], f"row {index} bar_timestamp")
        if row["symbol"] != SYMBOL:
            anomalies.append(f"row {index}: unexpected symbol {row['symbol']!r}")
        if row["signal_type"] not in {"LONG", "SHORT", "NO SIGNAL"}:
            anomalies.append(f"row {index}: invalid signal type {row['signal_type']!r}")
        if row["raw_signal_status"] not in {"BREAKOUT", "NO_BREAKOUT"}:
            anomalies.append(f"row {index}: invalid raw signal status")
        if row["bar_timestamp"] in seen:
            anomalies.append(f"row {index}: duplicate completed-bar timestamp")
        seen.add(row["bar_timestamp"])
        if previous_bar_time is not None and bar_time <= previous_bar_time:
            anomalies.append(f"row {index}: completed-bar timestamps are not increasing")
        previous_bar_time = bar_time

        expected_close_time = bar_time + BAR_DURATION
        skew = (expected_close_time - observation_time).total_seconds()
        if abs(skew) > CLOCK_TOLERANCE_SECONDS:
            anomalies.append(
                f"row {index}: bar close time differs from observation clock by "
                f"{skew:.0f} seconds under the configured broker-time contract"
            )
        expected_status = (
            "BREAKOUT" if row["signal_type"] in {"LONG", "SHORT"} else "NO_BREAKOUT"
        )
        if row["raw_signal_status"] != expected_status:
            anomalies.append(f"row {index}: signal type and raw signal status disagree")
    return anomalies


def _no_signal_periods(rows: list[dict[str, str]]) -> list[tuple[str, str, int]]:
    periods: list[tuple[str, str, int]] = []
    start: str | None = None
    previous: datetime | None = None
    count = 0

    def finish() -> None:
        nonlocal start, previous, count
        if start is not None and previous is not None:
            periods.append(
                (
                    start,
                    previous.isoformat(),
                    count,
                )
            )
        start = None
        previous = None
        count = 0

    for row in rows:
        bar_time = _parse_broker_time(row["bar_timestamp"], "bar_timestamp")
        no_signal = row["signal_type"] == "NO SIGNAL"
        contiguous = previous is not None and bar_time - previous == BAR_DURATION
        if not no_signal:
            finish()
        elif start is None or not contiguous:
            finish()
            start = bar_time.isoformat().replace("+00:00", "Z")
            previous = bar_time
            count = 1
        else:
            previous = bar_time
            count += 1
    finish()
    return periods


def generate_report(
    log_path: Path = DEFAULT_LOG,
    report_path: Path = DEFAULT_REPORT,
) -> str:
    """Write a descriptive observation summary with no trade-performance metrics."""
    rows = _read_observations(log_path)
    anomalies = _timestamp_anomalies(rows)
    longs = sum(row["signal_type"] == "LONG" for row in rows)
    shorts = sum(row["signal_type"] == "SHORT" for row in rows)
    no_signals = sum(row["signal_type"] == "NO SIGNAL" for row in rows)
    signals = longs + shorts
    frequency = signals / len(rows) * 100 if rows else 0.0
    periods = _no_signal_periods(rows)

    if rows:
        first_observed = rows[0]["timestamp"]
        last_observed = rows[-1]["timestamp"]
        first_bar = rows[0]["bar_timestamp"]
        last_bar = rows[-1]["bar_timestamp"]
    else:
        first_observed = last_observed = first_bar = last_bar = "none"

    lines = [
        "# Live V1 Signal Observation Report",
        "",
        f"- Observations logged: {len(rows)} completed bars",
        f"- Observation window (broker clock): {first_observed} to {last_observed}",
        f"- MT5-reported bar timestamp range: {first_bar} to {last_bar}",
        f"- Observed LONG signals: {longs}",
        f"- Observed SHORT signals: {shorts}",
        f"- LONG:SHORT ratio: {f'{longs}:{shorts}' if signals else 'n/a (no signals)'}",
        f"- Signal frequency: {signals}/{len(rows)} observed bars ({frequency:.2f}%)",
        f"- Bars without a signal: {no_signals}",
        "",
        "## Periods without signals",
        "",
    ]
    if periods:
        lines.append(
            "Each period below is a contiguous run of logged M5 bars. Gaps in "
            "observation are not treated as no-signal periods."
        )
        lines.append("")
        for start, end, count in periods:
            lines.append(f"- {start} to {end}: {count} completed bars")
    else:
        lines.append("- None observed.")

    lines.extend(["", "## Logging anomalies", ""])
    if anomalies:
        lines.extend(f"- {anomaly}" for anomaly in anomalies)
    else:
        lines.append("- None detected in the recorded rows.")

    lines.extend(
        [
            "",
            "## Interpretation limits",
            "",
            "- This is signal observation only, not trade-performance analysis.",
            "- The sample is too small to assess signal frequency as stable or "
            "representative."
            if len(rows) < 100
            else "- Frequency is descriptive for this observation window only.",
            "- MT5 bars are requested at position 1 or older, so the forming "
            "bar is excluded. API wall-clock fields are retained and tagged "
            "with the configured broker offset. Differences over 120 seconds "
            "from the expected bar close are reported as anomalies.",
            "- Signal observations do not count toward the completed-demo-trade "
            "gate. Demo trades remain 0 / 100 and V2 remains blocked.",
            "",
        ]
    )
    report = "\n".join(lines)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    return report


def observe(
    poll_interval_seconds: float = 5.0,
    log_path: Path = DEFAULT_LOG,
    report_path: Path = DEFAULT_REPORT,
    max_polls: int | None = None,
) -> None:
    """Poll, log one state per newly completed bar, and report on shutdown."""
    if poll_interval_seconds <= 0:
        raise ValueError("poll interval must be positive")
    if max_polls is not None and max_polls <= 0:
        raise ValueError("max_polls must be positive when provided")

    mt5_connector.initialize_connection()
    try:
        polls = 0
        while max_polls is None or polls < max_polls:
            row = observe_latest_bar(log_path)
            if row is not None:
                print(
                    f"{row['bar_timestamp']} {row['signal_type']} "
                    f"status={row['raw_signal_status']}"
                )
            polls += 1
            if max_polls is None or polls < max_polls:
                time.sleep(poll_interval_seconds)
    finally:
        mt5_connector.shutdown_connection()
        generate_report(log_path, report_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval", type=float, default=5.0, help="poll interval in seconds")
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG, help="observation CSV path")
    parser.add_argument(
        "--report", type=Path, default=DEFAULT_REPORT, help="observation report path"
    )
    parser.add_argument(
        "--max-polls",
        type=int,
        help="stop after this many polls (useful for bounded observation sessions)",
    )
    args = parser.parse_args()
    if args.interval <= 0:
        parser.error("--interval must be positive")
    if args.max_polls is not None and args.max_polls <= 0:
        parser.error("--max-polls must be positive")
    try:
        observe(
            poll_interval_seconds=args.interval,
            log_path=args.log,
            report_path=args.report,
            max_polls=args.max_polls,
        )
    except KeyboardInterrupt:
        print("Signal observation stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
