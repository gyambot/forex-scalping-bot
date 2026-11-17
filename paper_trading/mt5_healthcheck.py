"""Write a read-only MT5 demo connectivity and account health report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from paper_trading import mt5_connector
from paper_trading.broker_time import now_broker_time, parse_broker_timezone
from paper_trading.mt5_connector import (
    EXPECTED_SERVER,
    MT5ConnectorError,
    load_config,
)


DEFAULT_OUTPUT = Path(__file__).with_name("MT5_HEALTHCHECK.json")


def _account_demo_or_live(account: Any, module: Any) -> str:
    mode = getattr(account, "trade_mode", None)
    if mode == getattr(module, "ACCOUNT_TRADE_MODE_DEMO", 0):
        return "demo"
    if mode == getattr(module, "ACCOUNT_TRADE_MODE_REAL", 2):
        return "live"
    return "unknown"


def run_healthcheck() -> dict[str, Any]:
    """Collect account, terminal, permission, and EURUSD quote status."""
    result: dict[str, Any] = {
        "connected": False,
        "login": None,
        "server": EXPECTED_SERVER,
        "account_name": None,
        "currency": None,
        "leverage": None,
        "balance": None,
        "equity": None,
        "trade_allowed": False,
        "terminal_build": None,
        "eurusd_available": False,
        "demo_or_live": "unknown",
        "market_open": False,
        "quote_available": False,
        "checked_at_broker_time": None,
        "errors": [],
        "warnings": [],
    }

    try:
        config = load_config()
        result["server"] = config.server
        result["checked_at_broker_time"] = now_broker_time(
            parse_broker_timezone(config.broker_utc_offset)
        ).isoformat()
        mt5_connector.initialize_connection()
        module, _ = mt5_connector._require_connection()

        terminal = module.terminal_info()
        account = module.account_info()
        if terminal is None:
            raise MT5ConnectorError("MT5 terminal status is unavailable")
        if account is None:
            raise MT5ConnectorError("MT5 account information is unavailable")

        result["connected"] = bool(getattr(terminal, "connected", False))
        result["login"] = int(account.login) if getattr(account, "login", None) is not None else None
        result["server"] = getattr(account, "server", config.server)
        result["account_name"] = getattr(account, "name", None)
        result["currency"] = getattr(account, "currency", None)
        result["leverage"] = int(account.leverage) if getattr(account, "leverage", None) is not None else None
        result["balance"] = float(account.balance) if getattr(account, "balance", None) is not None else None
        result["equity"] = float(account.equity) if getattr(account, "equity", None) is not None else None
        result["demo_or_live"] = _account_demo_or_live(account, module)
        result["terminal_build"] = getattr(terminal, "build", None)

        permissions = mt5_connector.verify_trade_permissions()
        result["trade_allowed"] = permissions["permitted"]
        result["trade_permissions"] = permissions

        try:
            status = mt5_connector.verify_market_status("EURUSD")
            result["eurusd_available"] = status["quote_available"]
            result["market_open"] = status["market_open"]
            result["quote_available"] = status["quote_available"]
            result["quote_fresh_vs_broker_clock"] = status["quote_fresh"]
            result["quote_broker_clock_skew_seconds"] = round(
                -status["quote_age_seconds"], 3
            ) if status["quote_age_seconds"] is not None else None
            result["eurusd"] = {
                "bid": status["bid"],
                "ask": status["ask"],
                "tick_time_broker": status["tick_time_broker"],
                "trade_mode": status["trade_mode"],
            }
        except MT5ConnectorError as exc:
            result["errors"].append(str(exc))

        if not result["connected"]:
            result["errors"].append("MT5 terminal is not connected")
        if (
            result["server"] != EXPECTED_SERVER
            or result["login"] != config.login
            or result["demo_or_live"] != "demo"
        ):
            result["errors"].append(
                f"Account verification failed; expected demo server {EXPECTED_SERVER!r}"
            )
        if not result["trade_allowed"]:
            result["warnings"].append(
                "MT5 trade permissions are not fully enabled; this read-only connector will not enable them"
            )
        if not result.get("quote_fresh_vs_broker_clock", False):
            result["warnings"].append(
                "MT5 quote timestamp is outside the configured broker-time clock tolerance; "
                "verify the MT5_BROKER_UTC_OFFSET setting."
            )
        if not result["eurusd_available"]:
            result["errors"].append("EURUSD is not available with a valid current quote")
    except (MT5ConnectorError, OSError) as exc:
        result["errors"].append(str(exc))
    finally:
        try:
            mt5_connector.shutdown_connection()
        except MT5ConnectorError as exc:
            result["errors"].append(str(exc))

    result["success"] = not result["errors"]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=DEFAULT_OUTPUT, type=Path, help="healthcheck JSON output")
    args = parser.parse_args()
    report = run_healthcheck()
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        parser.error(f"Unable to write healthcheck report: {exc}")

    print(f"MT5 healthcheck written: {args.output}")
    print(f"Connected: {report['connected']}; demo account: {report['demo_or_live']}")
    print(f"EURUSD available: {report['eurusd_available']}; success: {report['success']}")
    for error in report["errors"]:
        print(f"ERROR: {error}")
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
