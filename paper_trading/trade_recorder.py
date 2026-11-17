"""Validate and append completed V1 demo positions to the operational CSV."""

from __future__ import annotations

import argparse
import csv
import json
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


def record_trade(values: Mapping[str, object], log_path: Path = DEFAULT_LOG) -> dict[str, str]:
    """Validate a trade and append it, refusing duplicate IDs or incomplete rows."""
    trade = validate_trade(values)
    check_operational_log_classification(trade, log_path)
    if log_path.exists():
        existing = read_trade_log(log_path)
        if any(row["trade_id"] == trade["trade_id"] for row in existing):
            raise ValueError(f"trade_id {trade['trade_id']!r} already exists")
    else:
        write_trade_log_header(log_path)
    with log_path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=TRADE_FIELDS, extrasaction="raise")
        writer.writerow(trade)
    return trade


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trade-json", required=True, type=Path, help="JSON object for one closed trade")
    parser.add_argument(
        "--log",
        default=DEFAULT_LOG,
        type=Path,
        help=f"operational demo CSV (default: {DEFAULT_LOG})",
    )
    args = parser.parse_args()
    try:
        with args.trade_json.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        if not isinstance(payload, dict):
            raise ValueError("trade JSON must contain one object")
        trade = record_trade(payload, args.log)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Recorded completed demo trade: {trade['trade_id']}")


if __name__ == "__main__":
    main()
