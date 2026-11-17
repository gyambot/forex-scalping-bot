"""Convert a HistData generic EURUSD M1 ZIP archive into strict M5 bid OHLC CSV."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import zipfile
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import TextIO


SOURCE_TZ = timezone(timedelta(hours=-5), name="EST")
UTC = timezone.utc


def _read_minutes(
    stream: TextIO,
) -> tuple[dict[datetime, tuple[float, float, float, float]], int, set[date], int]:
    minutes: dict[datetime, tuple[float, float, float, float]] = {}
    ambiguous_dates: set[datetime.date] = set()
    source_rows = 0
    previous_timestamp: datetime | None = None
    for line_number, row in enumerate(csv.reader(stream, delimiter=";"), start=1):
        source_rows += 1
        if len(row) != 6:
            raise ValueError(f"source line {line_number}: expected 6 semicolon-separated fields")
        try:
            timestamp = datetime.strptime(row[0], "%Y%m%d %H%M%S")
            prices = tuple(float(value) for value in row[1:5])
        except ValueError as exc:
            raise ValueError(f"source line {line_number}: invalid timestamp or price") from exc
        if timestamp.second != 0 or timestamp.microsecond != 0:
            raise ValueError(f"source line {line_number}: expected minute-aligned timestamp")
        if previous_timestamp is not None and timestamp < previous_timestamp:
            ambiguous_dates.add(timestamp.date())
        if not all(math.isfinite(price) and price > 0 for price in prices):
            raise ValueError(f"source line {line_number}: prices must be finite and positive")
        open_price, high, low, close = prices
        if low > min(open_price, close) or high < max(open_price, close) or low > high:
            raise ValueError(f"source line {line_number}: inconsistent OHLC values")

        existing = minutes.get(timestamp)
        if existing is None:
            minutes[timestamp] = prices
        else:
            minutes[timestamp] = (
                existing[0],
                max(existing[1], high),
                min(existing[2], low),
                close,
            )
        previous_timestamp = timestamp
    if not minutes:
        raise ValueError("source archive contains no M1 rows")
    raw_unique_minutes = len(minutes)
    if ambiguous_dates:
        minutes = {
            timestamp: values
            for timestamp, values in minutes.items()
            if timestamp.date() not in ambiguous_dates
        }
    if not minutes:
        raise ValueError("all source dates contain out-of-order timestamps")
    return minutes, source_rows, ambiguous_dates, raw_unique_minutes


def convert_archive(input_path: Path, output_path: Path) -> dict[str, object]:
    with zipfile.ZipFile(input_path) as archive:
        csv_members = [
            name for name in archive.namelist()
            if name.lower().endswith(".csv") and "eurusd" in name.lower()
        ]
        if len(csv_members) != 1:
            raise ValueError("archive must contain exactly one EURUSD CSV member")
        with archive.open(csv_members[0]) as source:
            text = io.TextIOWrapper(source, encoding="ascii", newline="")
            minutes, source_rows, ambiguous_dates, raw_unique_minutes = _read_minutes(text)

    buckets: dict[datetime, list[datetime]] = defaultdict(list)
    for timestamp in minutes:
        bucket_start = timestamp.replace(
            minute=timestamp.minute - timestamp.minute % 5,
            second=0,
            microsecond=0,
        )
        buckets[bucket_start].append(timestamp)

    complete_bars: list[tuple[datetime, float, float, float, float]] = []
    for bucket_start in sorted(buckets):
        expected = [bucket_start + timedelta(minutes=offset) for offset in range(5)]
        observed = sorted(buckets[bucket_start])
        if observed != expected:
            continue
        minute_prices = [minutes[timestamp] for timestamp in expected]
        complete_bars.append(
            (
                bucket_start,
                minute_prices[0][0],
                max(prices[1] for prices in minute_prices),
                min(prices[2] for prices in minute_prices),
                minute_prices[-1][3],
            )
        )
    if not complete_bars:
        raise ValueError("no complete five-minute buckets found in source archive")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(["timestamp", "open", "high", "low", "close"])
        for timestamp, open_price, high, low, close in complete_bars:
            utc_timestamp = timestamp.replace(tzinfo=SOURCE_TZ).astimezone(UTC)
            writer.writerow(
                [
                    utc_timestamp.isoformat().replace("+00:00", "Z"),
                    f"{open_price:.6f}",
                    f"{high:.6f}",
                    f"{low:.6f}",
                    f"{close:.6f}",
                ]
            )

    gaps = sum(
        current[0] - previous[0] > timedelta(minutes=5)
        for previous, current in zip(complete_bars, complete_bars[1:])
    )
    duplicate_rows_merged = source_rows - raw_unique_minutes
    summary: dict[str, object] = {
        "source_archive": input_path.name,
        "source_member": csv_members[0],
        "source_timezone": "EST (UTC-05:00 fixed; no DST adjustment)",
        "source_rows": source_rows,
        "unique_source_minutes_before_exclusions": raw_unique_minutes,
        "unique_source_minutes": len(minutes),
        "duplicate_rows_merged": duplicate_rows_merged,
        "out_of_order_source_dates_excluded": [
            date.isoformat() for date in sorted(ambiguous_dates)
        ],
        "source_minutes_excluded_for_ordering": raw_unique_minutes - len(minutes),
        "complete_m5_bars": len(complete_bars),
        "incomplete_m5_buckets_excluded": len(buckets) - len(complete_bars),
        "gaps_between_output_bars_over_5m": gaps,
        "first_bar_utc": complete_bars[0][0].replace(tzinfo=SOURCE_TZ).astimezone(UTC)
        .isoformat()
        .replace("+00:00", "Z"),
        "last_bar_utc": complete_bars[-1][0].replace(tzinfo=SOURCE_TZ).astimezone(UTC)
        .isoformat()
        .replace("+00:00", "Z"),
        "source_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
        "output_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="HistData EURUSD M1 ZIP archive")
    parser.add_argument("--output", required=True, type=Path, help="destination EURUSD M5 CSV")
    args = parser.parse_args()
    try:
        summary = convert_archive(args.input, args.output)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        parser.error(str(exc))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
