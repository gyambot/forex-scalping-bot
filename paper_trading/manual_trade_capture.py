"""Validate and append one human-reconciled, completed MT5 demo position."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Mapping

from paper_trading.demo_trade_utils import (
    TRADE_FIELDS,
    check_operational_log_classification,
    read_trade_log,
    validate_trade,
    write_trade_log_header,
)


DEFAULT_LOG = Path(__file__).with_name("DEMO_TRADING_LOG.csv")


def read_trade_import(import_path: Path) -> dict[str, str]:
    """Read exactly one trade from a CSV using the operational schema."""
    try:
        with import_path.open("r", newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            if tuple(reader.fieldnames or ()) != TRADE_FIELDS:
                raise ValueError(
                    f"trade import schema must exactly match: {','.join(TRADE_FIELDS)}"
                )
            rows = list(reader)
    except OSError as exc:
        raise ValueError(f"cannot read trade import {import_path}: {exc}") from exc

    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError("trade import contains a row with missing or extra CSV fields")
    if len(rows) != 1:
        raise ValueError("trade import CSV must contain exactly one completed trade row")
    return rows[0]


def append_completed_trade(
    values: Mapping[str, object],
    log_path: Path = DEFAULT_LOG,
) -> dict[str, str]:
    """Validate schema and completed status, reject duplicate IDs, then append."""
    trade = validate_trade(values)
    check_operational_log_classification(trade, log_path)
    if log_path.exists():
        with log_path.open("r", newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            if tuple(reader.fieldnames or ()) != TRADE_FIELDS:
                raise ValueError(
                    f"trade log schema must exactly match: {','.join(TRADE_FIELDS)}"
                )
        existing = read_trade_log(log_path)
        if any(row["trade_id"] == trade["trade_id"] for row in existing):
            raise ValueError(f"trade_id {trade['trade_id']!r} already exists")
    else:
        write_trade_log_header(log_path)

    with log_path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=TRADE_FIELDS, extrasaction="raise")
        writer.writerow(trade)
    return trade


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--trade-csv",
        required=True,
        type=Path,
        help="one-row CSV manually transcribed and reconciled from MT5 demo history",
    )
    parser.add_argument(
        "--log",
        default=DEFAULT_LOG,
        type=Path,
        help=f"operational demo CSV (default: {DEFAULT_LOG})",
    )
    args = parser.parse_args()
    try:
        payload = read_trade_import(args.trade_csv)
        trade = append_completed_trade(payload, args.log)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Recorded completed manual demo trade: {trade['trade_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
