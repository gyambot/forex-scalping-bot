"""Check V1's 100 eligible completed demo-trade gate."""

from __future__ import annotations

import argparse
from pathlib import Path

from paper_trading.demo_trade_utils import is_gate_eligible, read_trade_log


DEFAULT_LOG = Path(__file__).with_name("DEMO_TRADING_LOG.csv")
GATE_SIZE = 100


def get_gate_status(log_path: Path = DEFAULT_LOG) -> dict[str, object]:
    trades = read_trade_log(log_path)
    eligible_count = sum(is_gate_eligible(trade) for trade in trades)
    return {
        "completed_trades": eligible_count,
        "excluded_noncompliant_trades": len(trades) - eligible_count,
        "required_trades": GATE_SIZE,
        "eligibility": "READY_FOR_V2_REVIEW" if eligible_count >= GATE_SIZE else "BLOCKED",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=DEFAULT_LOG, type=Path, help="demo trade CSV")
    args = parser.parse_args()
    try:
        status = get_gate_status(args.input)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Completed Trades: {status['completed_trades']} / {GATE_SIZE}")
    print(f"Eligibility: {status['eligibility']}")
    if status["excluded_noncompliant_trades"]:
        print(f"Excluded non-compliant completed trades: {status['excluded_noncompliant_trades']}")
    if status["eligibility"] == "READY_FOR_V2_REVIEW":
        print("This status permits a review only; it does not approve or create V2.")


if __name__ == "__main__":
    main()
