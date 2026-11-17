"""Fail-closed, demo-only executor for frozen Breakout Scalping V1."""

from __future__ import annotations

import argparse
import json
import math
import msvcrt
import os
import re
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Mapping

from paper_trading import mt5_connector
from paper_trading.broker_time import (
    epoch_to_broker_time,
    now_broker_time,
    parse_broker_timezone,
)
from paper_trading.demo_trade_utils import read_trade_log
from paper_trading.check_gate import get_gate_status
from paper_trading.execution_logging import ExecutionLogger, read_events
from paper_trading.execution_reconciliation import (
    ReconciliationError,
    build_trade_record,
)
from paper_trading.generate_demo_metrics import calculate_demo_metrics
from paper_trading.live_signal_engine import evaluate_v1_signal
from paper_trading.manual_trade_capture import append_completed_trade
from paper_trading.mt5_price_feed import _field
from paper_trading.mt5_connector import (
    EXPECTED_SERVER,
    MT5ConnectorError,
)
from scripts.backtest import LOOKBACK_BARS


SYMBOL = "EURUSD"
PIP_SIZE = Decimal("0.0001")
STOP_PIPS = Decimal("10")
TARGET_PIPS = Decimal("20")
POLL_INTERVAL_SECONDS = 0.1
MAGIC_NUMBER = 26111601
DEFAULT_EXECUTION_LOG = Path(__file__).with_name("EXECUTION_LOG.csv")
DEFAULT_STATE_FILE = Path(__file__).with_name("EXECUTOR_STATE.json")
DEFAULT_TRADE_LOG = Path(__file__).with_name("DEMO_TRADING_LOG.csv")
DEFAULT_METRICS_FILE = Path(__file__).with_name("DEMO_METRICS.json")
DEFAULT_GATE_FILE = Path(__file__).with_name("DEMO_GATE_STATUS.md")
DEFAULT_INTEGRATION_RESULT = Path(__file__).with_name(
    "DEMO_EXECUTOR_INTEGRATION_RESULT.md"
)
DEFAULT_SINGLE_RESULT = Path(__file__).with_name("SINGLE_TRADE_VALIDATION_RESULT.md")
VALIDATION_CLASS = "engineering_validation"


class ExecutorError(RuntimeError):
    """Raised when an execution state is unsafe or cannot be reconciled."""


def validate_demo_account(module: Any, expected_login: int | None = None) -> Any:
    """Require a connected terminal, exact demo server, and known demo mode."""
    terminal = module.terminal_info()
    account = module.account_info()
    if terminal is None or account is None:
        raise ExecutorError("cannot determine terminal connection or account state")
    if not bool(getattr(terminal, "connected", False)):
        raise ExecutorError("MT5 terminal is disconnected; execution stopped")
    if str(getattr(account, "server", "")) != EXPECTED_SERVER:
        raise ExecutorError(
            f"server mismatch; expected {EXPECTED_SERVER!r}, execution stopped"
        )
    demo_mode = getattr(module, "ACCOUNT_TRADE_MODE_DEMO", None)
    trade_mode = getattr(account, "trade_mode", None)
    if demo_mode is None or trade_mode is None:
        raise ExecutorError("account type is unknown; execution stopped")
    if trade_mode != demo_mode:
        raise ExecutorError("account is not demo; execution stopped")
    try:
        login = int(getattr(account, "login", 0))
    except (TypeError, ValueError) as exc:
        raise ExecutorError("account login is unknown; execution stopped") from exc
    if login <= 0:
        raise ExecutorError("account login is unknown; execution stopped")
    if expected_login is not None and login != expected_login:
        raise ExecutorError("connected login mismatch; execution stopped")
    if not mt5_connector.verify_trade_permissions()["permitted"]:
        raise ExecutorError("MT5 trade permissions are unavailable; execution stopped")
    return account


def _read_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"processed_signal_times": [], "active_position": None}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExecutorError(f"executor state is unreadable: {exc}") from exc
    if not isinstance(state, dict) or not isinstance(
        state.get("processed_signal_times"), list
    ):
        raise ExecutorError("executor state has an invalid schema")
    if "active_position" not in state:
        raise ExecutorError("executor state is missing active_position")
    if "single_trade_validation" in state and not isinstance(state["single_trade_validation"], dict):
        raise ExecutorError("single-trade validation state is invalid")
    return state


def _write_state(path: Path, state: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        temporary.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
    except OSError as exc:
        raise ExecutorError(f"cannot persist executor state: {exc}") from exc


def _configured_volume(module: Any, symbol_info: Any) -> float:
    raw = os.environ.get("MT5_DEMO_VOLUME", "").strip()
    if not raw:
        values = mt5_connector._read_env_file(mt5_connector.DEFAULT_ENV_FILE)
        raw = values.get("MT5_DEMO_VOLUME", "").strip()
    if not raw:
        raise ExecutorError(
            "MT5_DEMO_VOLUME must be explicitly configured; no broker lot size is inferred"
        )
    try:
        volume = Decimal(raw)
        minimum = Decimal(str(getattr(symbol_info, "volume_min")))
        maximum = Decimal(str(getattr(symbol_info, "volume_max")))
        step = Decimal(str(getattr(symbol_info, "volume_step")))
    except (ValueError, TypeError, ArithmeticError, AttributeError) as exc:
        raise ExecutorError("demo volume or broker volume limits are invalid") from exc
    if not volume.is_finite() or minimum <= 0 or step <= 0:
        raise ExecutorError("demo volume and broker volume step must be positive")
    if volume < minimum or volume > maximum or (volume - minimum) % step:
        raise ExecutorError("MT5_DEMO_VOLUME is outside broker limits or volume step")
    return float(volume)


def _filling_type(module: Any, symbol_info: Any) -> int:
    modes = int(getattr(symbol_info, "filling_mode", 0))
    if modes & int(getattr(module, "SYMBOL_FILLING_FOK", 1)):
        return int(module.ORDER_FILLING_FOK)
    if modes & int(getattr(module, "SYMBOL_FILLING_IOC", 2)):
        return int(module.ORDER_FILLING_IOC)
    raise ExecutorError("EURUSD has no supported FOK/IOC market filling mode")


def _current_bar(module: Any, broker_offset: str) -> dict[str, Any]:
    rates = module.copy_rates_from_pos(SYMBOL, module.TIMEFRAME_M5, 0, 1)
    if rates is None or len(rates) != 1:
        raise ExecutorError("cannot read the current M5 bar; execution stopped")
    rate = rates[0]
    timestamp = int(_field(rate, "time"))
    if timestamp <= 0:
        raise ExecutorError("current M5 bar has no timestamp")
    open_price = float(_field(rate, "open"))
    if open_price <= 0:
        raise ExecutorError("current M5 bar has an invalid open price")
    return {
        "timestamp": epoch_to_broker_time(timestamp, broker_offset).isoformat(),
        "open": open_price,
    }


def _position_list(module: Any) -> list[Any]:
    positions = module.positions_get()
    if positions is None:
        raise ExecutorError("cannot determine open-position state; execution stopped")
    return list(positions)


def _probe_writable_parent(parent: Path) -> None:
    if not parent.is_dir():
        raise ExecutorError(f"required output directory does not exist: {parent}")
    try:
        with NamedTemporaryFile(
            mode="wb", prefix=".demo-executor-verify-", dir=parent, delete=True
        ) as probe:
            probe.write(b"read-only integration preflight\n")
            probe.flush()
    except OSError as exc:
        raise ExecutorError(f"output directory is not writable: {parent}") from exc


@contextmanager
def _exclusive_instance_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        lock_file = path.open("a+b")
    except OSError as exc:
        raise ExecutorError(f"cannot open executor instance lock: {exc}") from exc
    with lock_file:
        lock_file.seek(0, os.SEEK_END)
        if lock_file.tell() == 0:
            lock_file.write(b"\0")
            lock_file.flush()
        lock_file.seek(0)
        try:
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            raise ExecutorError(
                "another executor instance holds the lock; execution stopped"
            ) from exc
        try:
            yield
        finally:
            lock_file.seek(0)
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)


def _deal_by_ticket(module: Any, ticket: int) -> Any:
    deals = module.history_deals_get(ticket=ticket)
    if deals is None or len(deals) != 1:
        raise ExecutorError(
            "order result cannot be confirmed in deal history; execution stopped for reconciliation"
        )
    return deals[0]


class DemoExecutor:
    def __init__(
        self,
        *,
        execution_log: Path = DEFAULT_EXECUTION_LOG,
        state_file: Path = DEFAULT_STATE_FILE,
        trade_log: Path = DEFAULT_TRADE_LOG,
        metrics_file: Path = DEFAULT_METRICS_FILE,
        gate_file: Path = DEFAULT_GATE_FILE,
        lock_file: Path | None = None,
        logger: ExecutionLogger | None = None,
    ):
        self.execution_log = execution_log
        self.state_file = state_file
        self.trade_log = trade_log
        self.metrics_file = metrics_file
        self.gate_file = gate_file
        self.lock_file = lock_file or state_file.with_suffix(".lock")
        self.logger = logger or ExecutionLogger(execution_log)

    def verify_only(
        self,
        *,
        approved_volume: Decimal,
        report_path: Path = DEFAULT_INTEGRATION_RESULT,
    ) -> bool:
        """Run read-only startup checks; never place or modify a broker order."""
        checks: list[tuple[str, str, str]] = []
        account_info: Any | None = None
        server = "unavailable"
        offset = "unavailable"
        module: Any | None = None

        def record(name: str, action) -> Any | None:
            try:
                result = action()
                if (
                    isinstance(result, tuple)
                    and len(result) == 2
                    and isinstance(result[1], str)
                ):
                    result, details = result
                else:
                    details = str(result)
            except Exception as exc:
                checks.append((name, "FAIL", str(exc)))
                return None
            checks.append((name, "PASS", details))
            return result

        def connect() -> str:
            if not mt5_connector.initialize_connection():
                raise ExecutorError("MT5 initialization returned false")
            return "MT5 initialization succeeded."

        connected = record(
            "MT5 startup connection",
            connect,
        )
        try:
            if connected:
                module, config = mt5_connector._require_connection()
                server = config.server
                offset = config.broker_utc_offset
                account_info = record(
                    "Demo account and server",
                    lambda: (
                        validate_demo_account(module, config.login),
                        f"Account mode=DEMO; connected server={module.account_info().server}.",
                    ),
                )
            else:
                checks.extend(
                    (
                        (name, "SKIP", "MT5 connection did not pass.")
                        for name in (
                            "Demo account and server",
                            "EURUSD symbol",
                            "Trade permissions",
                            "Broker-time configuration",
                            "Broker-time feed",
                            "Position and reconciliation readiness",
                        )
                    )
                )

            if module is not None:
                symbol_info = record(
                    "EURUSD symbol",
                    lambda: (
                        (info := self._verify_symbol_read_only(module)),
                        (
                            f"EURUSD visible={bool(getattr(info, 'visible', False))}; "
                            f"trade mode={getattr(info, 'trade_mode', 'unknown')}; "
                            f"tick size={getattr(info, 'trade_tick_size', 'unknown')}."
                        ),
                    ),
                )
                record(
                    "Trade permissions",
                    lambda: self._verify_permissions_read_only(),
                )
                offset_source = self._explicit_broker_offset()
                if offset_source is None:
                    offset = (
                        f"UNSET (active MT5 default is {config.broker_utc_offset})"
                    )
                    checks.append(
                        (
                            "Broker-time configuration",
                            "FAIL",
                            "MT5_BROKER_UTC_OFFSET is not explicitly set in the process environment or paper_trading/.env.",
                        )
                    )
                else:
                    try:
                        parse_broker_timezone(offset_source)
                        if offset_source != offset:
                            raise ExecutorError(
                                "configured broker offset differs from the active MT5 configuration"
                            )
                    except (ValueError, ExecutorError) as exc:
                        checks.append(
                            ("Broker-time configuration", "FAIL", str(exc))
                        )
                    else:
                        checks.append(
                            (
                                "Broker-time configuration",
                                "PASS",
                                f"Explicit configured broker offset={offset_source}.",
                            )
                        )
                if symbol_info is not None:
                    record(
                        "Approved demo volume",
                        lambda: self._verify_approved_volume(
                            symbol_info, approved_volume
                        ),
                    )
                else:
                    checks.append(
                        ("Approved demo volume", "SKIP", "EURUSD symbol check did not pass.")
                    )

                if offset_source and symbol_info:
                    record(
                        "Broker-time feed",
                        lambda: self._verify_broker_feed(
                            module, offset_source
                        ),
                    )
                else:
                    checks.append(
                        (
                            "Broker-time feed",
                            "SKIP",
                            "Requires a valid explicit broker-time offset and available EURUSD symbol.",
                        )
                    )
                self._record_local_check(
                    checks,
                    "Execution logging",
                    lambda: self._verify_log_path(),
                )
                position_result = record(
                    "Position and reconciliation readiness",
                    lambda: self._verify_reconciliation_startup(module),
                )
            else:
                self._record_local_check(
                    checks,
                    "Execution logging",
                    lambda: self._verify_log_path(),
                )

            self._record_local_check(
                checks,
                "Metrics startup",
                self._verify_metrics_startup,
            )
            self._record_local_check(
                checks,
                "Gate startup",
                self._verify_gate_startup,
            )
            all_passed = bool(checks) and all(status == "PASS" for _, status, _ in checks)
            self._write_integration_report(
                report_path,
                checks,
                conclusion="READY_FOR_DEMO_TRADE_1" if all_passed else "EXECUTOR_BLOCKED",
                server=server,
                offset=offset,
                approved_volume=approved_volume,
            )
            return all_passed
        finally:
            if connected:
                mt5_connector.shutdown_connection()

    def _record_local_check(
        self, checks: list[tuple[str, str, str]], name: str, action
    ) -> None:
        try:
            details = str(action())
        except Exception as exc:
            checks.append((name, "FAIL", str(exc)))
        else:
            checks.append((name, "PASS", details))

    @staticmethod
    def _explicit_broker_offset() -> str | None:
        configured = os.environ.get("MT5_BROKER_UTC_OFFSET", "").strip()
        if configured:
            return configured
        values = mt5_connector._read_env_file(mt5_connector.DEFAULT_ENV_FILE)
        configured = values.get("MT5_BROKER_UTC_OFFSET", "").strip()
        return configured or None

    @staticmethod
    def _verify_symbol_read_only(module: Any) -> Any:
        info = module.symbol_info(SYMBOL)
        if info is None:
            raise ExecutorError("EURUSD symbol information is unavailable")
        if not bool(getattr(info, "visible", False)):
            raise ExecutorError(
                "EURUSD is not visible in Market Watch; read-only verification will not select symbols"
            )
        trade_mode = int(getattr(info, "trade_mode", -1))
        if trade_mode in {
            int(getattr(module, "SYMBOL_TRADE_MODE_DISABLED", 0)),
            int(getattr(module, "SYMBOL_TRADE_MODE_CLOSEONLY", 3)),
        }:
            raise ExecutorError("EURUSD is disabled or close-only")
        if Decimal(str(getattr(info, "trade_tick_size", 0))) <= 0:
            raise ExecutorError("EURUSD tick size is unavailable")
        if Decimal(str(getattr(info, "trade_tick_value", 0))) <= 0:
            raise ExecutorError("EURUSD tick value is unavailable")
        return info

    @staticmethod
    def _verify_permissions_read_only() -> str:
        permissions = mt5_connector.verify_trade_permissions()
        if not permissions["permitted"]:
            raise ExecutorError(
                "terminal/account trade permissions are not fully enabled; no permission settings were changed"
            )
        return "Terminal, API, account, and expert permissions are enabled."

    @staticmethod
    def _verify_approved_volume(
        symbol_info: Any, approved_volume: Decimal
    ) -> str:
        minimum = Decimal(str(getattr(symbol_info, "volume_min", 0)))
        maximum = Decimal(str(getattr(symbol_info, "volume_max", 0)))
        step = Decimal(str(getattr(symbol_info, "volume_step", 0)))
        if not approved_volume.is_finite() or minimum <= 0 or step <= 0:
            raise ExecutorError("approved volume or broker limits are invalid")
        configured = os.environ.get("MT5_DEMO_VOLUME", "").strip()
        if not configured:
            configured = mt5_connector._read_env_file(
                mt5_connector.DEFAULT_ENV_FILE
            ).get("MT5_DEMO_VOLUME", "").strip()
        try:
            configured_volume = Decimal(configured) if configured else None
        except Exception as exc:
            raise ExecutorError("MT5_DEMO_VOLUME is not a valid decimal") from exc
        if configured_volume != approved_volume:
            raise ExecutorError(
                "MT5_DEMO_VOLUME is not configured to the approved demo size"
            )
        if not minimum <= approved_volume <= maximum or (
            approved_volume - minimum
        ) % step:
            raise ExecutorError(
                "approved volume violates EURUSD broker min/max/step limits"
            )
        return (
            f"MT5_DEMO_VOLUME={approved_volume}; broker limits "
            f"{minimum}..{maximum}, step {step}."
        )

    @staticmethod
    def _verify_broker_feed(module: Any, offset: str) -> str:
        parse_broker_timezone(offset)
        tick = module.symbol_info_tick(SYMBOL)
        if tick is None:
            raise ExecutorError("EURUSD quote is unavailable")
        bid, ask = float(getattr(tick, "bid", 0)), float(getattr(tick, "ask", 0))
        tick_epoch = int(getattr(tick, "time", 0))
        if not math.isfinite(bid) or not math.isfinite(ask) or bid <= 0 or ask < bid or tick_epoch <= 0:
            raise ExecutorError("EURUSD quote or broker timestamp is invalid")
        tick_time = epoch_to_broker_time(tick_epoch, offset)
        bar = _current_bar(module, offset)
        bar_time = datetime.fromisoformat(bar["timestamp"])
        if tick_time < bar_time:
            raise ExecutorError(
                "EURUSD quote timestamp precedes the current M5 bar timestamp"
            )
        seconds_into_bar = (tick_time - bar_time).total_seconds()
        if seconds_into_bar >= 5 * 60:
            raise ExecutorError(
                "EURUSD quote timestamp is not within the current M5 bar"
            )
        if bar_time.minute % 5 or bar_time.second or bar_time.microsecond:
            raise ExecutorError("current M5 bar timestamp is not on an M5 boundary")
        return (
            f"Offset={offset}; quote is {seconds_into_bar:.1f}s after the current M5 bar open; "
            f"current M5 bar={bar['timestamp']}."
        )

    def _verify_log_path(self) -> str:
        events = read_events(self.execution_log)
        _probe_writable_parent(self.execution_log.parent)
        return (
            f"Execution log path and schema are writable/readable; "
            f"{len(events)} existing events; no execution event was appended."
        )

    def _verify_reconciliation_startup(self, module: Any) -> str:
        state = _read_state(self.state_file)
        if state.get("active_position") is not None:
            raise ExecutorError(
                "executor state contains an active or unresolved position"
            )
        if not callable(getattr(module, "history_deals_get", None)):
            raise ExecutorError("MT5 deal-history API is unavailable")
        positions = _position_list(module)
        if positions:
            raise ExecutorError(
                f"account has {len(positions)} open position(s); startup requires a flat account"
            )
        trades = read_trade_log(self.trade_log)
        return (
            f"Trade schema validated; {len(trades)} existing trade records; "
            "executor state is idle; account is flat; deal-history API is available."
        )

    def _verify_metrics_startup(self) -> str:
        trades = read_trade_log(self.trade_log)
        current_metrics = calculate_demo_metrics(trades)
        saved = json.loads(self.metrics_file.read_text(encoding="utf-8"))
        if saved != current_metrics:
            raise ExecutorError(
                "saved demo metrics do not match a fresh in-memory calculation"
            )
        _probe_writable_parent(self.metrics_file.parent)
        return (
            f"Saved metrics match an in-memory calculation; "
            f"eligible trades={current_metrics['eligible_trade_count']}; no file was changed."
        )

    def _verify_gate_startup(self) -> str:
        gate_text = self.gate_file.read_text(encoding="utf-8")
        counts = re.findall(
            r"(?m)^- \*\*Demo Trades Completed:\*\* \*\*(\d+) / 100\*\*$",
            gate_text,
        )
        if len(counts) != 1:
            raise ExecutorError("gate file has an unrecognized trade-count schema")
        metrics = calculate_demo_metrics(read_trade_log(self.trade_log))
        count = int(metrics["eligible_trade_count"])
        if int(counts[0]) != count:
            raise ExecutorError(
                f"gate count {counts[0]} does not match eligible trade count {count}"
            )
        eligibility = re.findall(r"(?m)^- \*\*V2 Eligibility:\*\* \*\*(BLOCKED|READY_FOR_V2_REVIEW)\*\*$", gate_text)
        expected = "READY_FOR_V2_REVIEW" if count >= 100 else "BLOCKED"
        if eligibility != [expected]:
            raise ExecutorError("gate eligibility is missing or inconsistent with the trade count")
        if len(re.findall(r"(?m)^- \*\*Reason:\*\* \*\*.+\*\*$", gate_text)) != 1:
            raise ExecutorError("gate reason schema is invalid")
        _probe_writable_parent(self.gate_file.parent)
        return f"Gate schema is valid and count matches {count} eligible trade(s); no file was changed."

    @staticmethod
    def _write_integration_report(
        path: Path,
        checks: list[tuple[str, str, str]],
        *,
        conclusion: str,
        server: str,
        offset: str,
        approved_volume: Decimal,
    ) -> None:
        rows = "\n".join(
            f"| {name} | {status} | {details.replace('|', '/')} |"
            for name, status, details in checks
        )
        report = (
            "# Demo Executor Integration Result\n\n"
            f"- Run time: {datetime.now().astimezone().isoformat()}\n"
            f"- MT5 configured server: {server}\n"
            f"- Broker offset setting: {offset}\n"
            f"- Approved demo volume: {approved_volume}\n"
            "- Mode: read-only verification; no order/position/pending-order modification attempted.\n"
            "- No trade record was created by this verification run.\n\n"
            "The MT5 connection shutdown path was executed after verification.\n\n"
            "| Check | Result | Evidence |\n|---|---|---|\n"
            f"{rows}\n\n"
            "This startup verification does not test broker order acceptance, "
            "protective-order attachment, actual fill behavior, or live deal-cost "
            "conversion because order submission is prohibited in this phase.\n\n"
            f"**{conclusion}**\n"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report, encoding="utf-8")

    def _time(self, offset: str) -> datetime:
        return now_broker_time(parse_broker_timezone(offset))

    def _log(self, event: str, offset: str, **values: Any) -> None:
        values.setdefault("timestamp_broker", self._time(offset).isoformat())
        self.logger.append(event, **values)

    def _signal_values(self, bars: list[dict[str, Any]], signal: Any) -> dict[str, Any]:
        previous = bars[-LOOKBACK_BARS - 1 : -1]
        direction = signal.signal_type.lower()
        return {
            "trade_id": "V1-DEMO-" + signal.timestamp.replace("-", "").replace(":", "").replace("+", "_").replace(".", ""),
            "symbol": SYMBOL,
            "direction": direction,
            "signal_bar_open_time_broker": signal.timestamp,
            "signal_close": signal.current_price,
            "prior_20_high": max(float(bar["high"]) for bar in previous),
            "prior_20_low": min(float(bar["low"]) for bar in previous),
        }

    def _validation_paths(self) -> dict[str, Path]:
        directory = self.trade_log.parent
        paths = {
            "trade_log": directory / "VALIDATION_TRADING_LOG.csv",
            "metrics": directory / "VALIDATION_METRICS.json",
            "gate": directory / "VALIDATION_GATE_SIMULATION.json",
        }
        protected = (self.trade_log, self.metrics_file, self.gate_file,
                     self.state_file, self.execution_log, self.lock_file)
        resolved = [path.resolve() for path in (*paths.values(), *protected)]
        if len(set(resolved)) != len(resolved):
            raise ExecutorError("validation and study or safety paths must not alias")
        for path in paths.values():
            if path.exists():
                for other in (*protected, *paths.values()):
                    if other != path and other.exists() and os.path.samefile(path, other):
                        raise ExecutorError("validation and study or safety paths must not alias")
        return paths

    def _validation_descriptor(self) -> dict[str, Any]:
        paths = self._validation_paths()
        return {
            "classification": VALIDATION_CLASS,
            "destinations": {name: str(path.resolve()) for name, path in paths.items()},
        }

    def _check_validation_descriptor(self, validation: Any) -> dict[str, Path]:
        if not isinstance(validation, dict):
            raise ExecutorError("validation classification is missing or invalid")
        descriptor = self._validation_descriptor()
        if any(validation.get(key) != value for key, value in descriptor.items()):
            raise ExecutorError("validation classification or destinations are invalid")
        return self._validation_paths()

    def _verify_validation_startup(self, module: Any, config: Any) -> None:
        state = _read_state(self.state_file)
        if "single_trade_validation" in state:
            raise ExecutorError("prior single-trade validation exists; manual reconciliation required")
        pending = module.orders_get()
        if pending is None or pending:
            raise ExecutorError("pending orders are present or unavailable")
        offset = self._explicit_broker_offset()
        if not offset or offset != config.broker_utc_offset:
            raise ExecutorError("explicit broker offset is missing or differs from active configuration")
        self._verify_broker_feed(module, offset)
        tick = module.symbol_info_tick(SYMBOL)
        if tick is None or int(getattr(tick, "time", 0)) <= 0:
            raise ExecutorError("EURUSD quote timestamp is unavailable")
        age = (self._time(offset) - epoch_to_broker_time(int(tick.time), offset)).total_seconds()
        if not 0 <= age <= mt5_connector.MAX_TICK_AGE_SECONDS:
            raise ExecutorError("EURUSD quote is stale or in the future")
        self._verify_log_path()
        self._verify_reconciliation_startup(module)
        self._verify_metrics_startup()
        self._verify_gate_startup()
        paths = self._validation_paths()
        for path in paths.values():
            _probe_writable_parent(path.parent)
            if path.exists() and not path.is_file():
                raise ExecutorError(f"validation output is not a file: {path}")
            if path.exists():
                with path.open("r+", encoding="utf-8"):
                    pass
        if paths["trade_log"].exists():
            import csv
            from paper_trading.demo_trade_utils import TRADE_FIELDS
            with paths["trade_log"].open("r", newline="", encoding="utf-8-sig") as source:
                if tuple(next(csv.reader(source), ())) != TRADE_FIELDS:
                    raise ExecutorError("validation trade log schema is invalid")
            read_trade_log(paths["trade_log"])
        for key, required, label in (
            ("metrics", "eligible_trade_count", "engineering validation only; not study performance"),
            ("gate", "completed_trades", "simulation only; not study gate progress"),
        ):
            if paths[key].exists():
                try:
                    saved = json.loads(paths[key].read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    raise ExecutorError(f"validation {key} output is unreadable") from exc
                if not isinstance(saved, dict) or required not in saved or saved.get("scope") != label:
                    raise ExecutorError(f"validation {key} output schema is invalid")

    def verify_validation_only(self) -> None:
        """Check validation startup without placing or modifying broker orders."""
        mt5_connector.initialize_connection()
        try:
            with _exclusive_instance_lock(self.lock_file):
                module, config = mt5_connector._require_connection()
                validate_demo_account(module, config.login)
                self._verify_approved_volume(self._verify_symbol_read_only(module), Decimal("0.01"))
                self._verify_validation_startup(module, config)
        finally:
            mt5_connector.shutdown_connection()

    def _refresh_validation_reports(self, paths: dict[str, Path]) -> None:
        trades = read_trade_log(paths["trade_log"])
        metrics = calculate_demo_metrics(trades)
        metrics["scope"] = "engineering validation only; not study performance"
        gate = get_gate_status(paths["trade_log"])
        gate["scope"] = "simulation only; not study gate progress"
        paths["metrics"].write_text(json.dumps(metrics, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        paths["gate"].write_text(json.dumps(gate, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    def process_once(self) -> None:
        with _exclusive_instance_lock(self.lock_file):
            self._process_once()

    def _process_once(self, *, validation_run: bool = False) -> None:
        module, config = mt5_connector._require_connection()
        validate_demo_account(module, config.login)
        symbol_info = mt5_connector.verify_symbol(SYMBOL)
        if not bool(getattr(symbol_info, "visible", False)):
            raise ExecutorError("EURUSD is not available in Market Watch")
        disabled_mode = int(getattr(module, "SYMBOL_TRADE_MODE_DISABLED", 0))
        close_only_mode = int(getattr(module, "SYMBOL_TRADE_MODE_CLOSEONLY", 3))
        if int(getattr(symbol_info, "trade_mode", disabled_mode)) in {
            disabled_mode,
            close_only_mode,
        }:
            raise ExecutorError("EURUSD is not available for new market orders")
        state = _read_state(self.state_file)
        active = state["active_position"]
        validation = state.get("single_trade_validation")
        if validation is not None:
            if not validation_run:
                raise ExecutorError("single-trade validation state requires reconciliation; execution stopped")
            self._check_validation_descriptor(validation)
            phase = validation.get("phase")
            if phase == "monitoring" and active and active.get("phase") == "open":
                self._monitor_position(module, config, symbol_info, state, _position_list(module))
                return
            if phase != "armed":
                raise ExecutorError("single-trade validation is disarmed; no new entry permitted")
            if active is not None:
                raise ExecutorError("validation has an unexpected active position")
            pending = module.orders_get()
            if pending is None or len(pending):
                raise ExecutorError("pending orders are present or unavailable")
        elif validation_run:
            raise ExecutorError("single-trade validation state is missing")
        if active and active.get("phase") == "submitting":
            raise ExecutorError(
                "previous order submission is ambiguous; execution stopped for reconciliation"
            )

        positions = _position_list(module)
        if active and active.get("phase") == "open":
            self._monitor_position(module, config, symbol_info, state, positions)
            return
        if validation_run and positions:
            raise ExecutorError("unexpected open position during single-trade validation")

        from paper_trading.mt5_price_feed import get_recent_m5_bars

        recent = get_recent_m5_bars(count=LOOKBACK_BARS + 1, symbol=SYMBOL)
        signal = evaluate_v1_signal(recent)
        if signal.signal_type not in {"LONG", "SHORT"}:
            return
        signal_values = self._signal_values(recent, signal)
        signal_time = signal_values["signal_bar_open_time_broker"]
        processed = set(state["processed_signal_times"])
        if signal_time in processed:
            return

        offset = config.broker_utc_offset
        planned = datetime.fromisoformat(signal_time) + timedelta(minutes=5)
        current_time = self._time(offset)
        signal_already_logged = any(
            event["event"] == "signal_detected"
            and event["signal_time_broker"] == signal_time
            for event in read_events(self.execution_log)
        )
        if not signal_already_logged:
            self._log(
                "signal_detected",
                offset,
                signal_time_broker=signal_time,
                planned_entry_time_broker=planned.isoformat(),
                direction=signal_values["direction"],
                price=signal.current_price,
                details=signal_values["trade_id"],
            )

        if positions:
            state["processed_signal_times"].append(signal_time)
            _write_state(self.state_file, state)
            self._log(
                "signal_ignored_position_open",
                offset,
                signal_time_broker=signal_time,
                planned_entry_time_broker=planned.isoformat(),
                direction=signal_values["direction"],
                details="one-position rule",
            )
            return

        if current_time < planned:
            return
        if current_time >= planned + timedelta(minutes=5):
            state["processed_signal_times"].append(signal_time)
            _write_state(self.state_file, state)
            self._log(
                "signal_missed",
                offset,
                signal_time_broker=signal_time,
                planned_entry_time_broker=planned.isoformat(),
                direction=signal_values["direction"],
                details="next M5 entry bar has elapsed; no late order submitted",
            )
            return

        current_bar = _current_bar(module, offset)
        if datetime.fromisoformat(current_bar["timestamp"]) != planned:
            state["processed_signal_times"].append(signal_time)
            _write_state(self.state_file, state)
            self._log(
                "signal_missed",
                offset,
                signal_time_broker=signal_time,
                planned_entry_time_broker=planned.isoformat(),
                direction=signal_values["direction"],
                details="MT5 current bar is not the planned next M5 bar",
            )
            return

        volume = _configured_volume(module, symbol_info)
        if validation_run and Decimal(str(volume)) != Decimal("0.01"):
            raise ExecutorError("single-trade validation requires exactly 0.01 lots")
        tick = module.symbol_info_tick(SYMBOL)
        if tick is None:
            raise ExecutorError("EURUSD quote unavailable; execution stopped")
        if validation_run:
            tick_epoch = int(getattr(tick, "time", 0))
            if tick_epoch <= 0:
                raise ExecutorError("EURUSD quote timestamp is unavailable")
            age = (self._time(offset) - epoch_to_broker_time(tick_epoch, offset)).total_seconds()
            if not 0 <= age <= mt5_connector.MAX_TICK_AGE_SECONDS:
                raise ExecutorError("EURUSD quote is stale or in the future")
        bid, ask = float(getattr(tick, "bid", 0)), float(getattr(tick, "ask", 0))
        if not math.isfinite(bid) or not math.isfinite(ask) or bid <= 0 or ask < bid:
            raise ExecutorError("EURUSD quote is invalid; execution stopped")
        buy = signal_values["direction"] == "long"
        order_type = int(module.ORDER_TYPE_BUY if buy else module.ORDER_TYPE_SELL)
        requested_price = ask if buy else bid
        intended_entry = (
            current_bar["open"] + float(PIP_SIZE)
            if buy
            else current_bar["open"]
        )
        stop = requested_price - float(STOP_PIPS * PIP_SIZE) if buy else requested_price + float(STOP_PIPS * PIP_SIZE)
        target = requested_price + float(TARGET_PIPS * PIP_SIZE) if buy else requested_price - float(TARGET_PIPS * PIP_SIZE)
        request = {
            "action": int(module.TRADE_ACTION_DEAL),
            "symbol": SYMBOL,
            "volume": volume,
            "type": order_type,
            "price": requested_price,
            "sl": stop,
            "tp": target,
            "deviation": 0,
            "magic": MAGIC_NUMBER,
            "comment": signal_values["trade_id"][-31:],
            "type_time": int(module.ORDER_TIME_GTC),
            "type_filling": _filling_type(module, symbol_info),
        }
        if validation_run:
            validate_demo_account(module, config.login)
            if _position_list(module):
                raise ExecutorError("unexpected open position before submission")
            pending = module.orders_get()
            if pending is None or pending:
                raise ExecutorError("pending orders are present or unavailable before submission")
            if self._time(offset) > planned:
                state["processed_signal_times"].append(signal_time)
                _write_state(self.state_file, state)
                self._log(
                    "signal_missed", offset, signal_time_broker=signal_time,
                    planned_entry_time_broker=planned.isoformat(),
                    direction=signal_values["direction"],
                    details="validation submission decision is after the frozen next-bar open",
                )
                return
        submission_time = self._time(offset).isoformat()
        state["processed_signal_times"].append(signal_time)
        state["active_position"] = {
            "phase": "submitting",
            "signal": signal_values,
            "planned_entry_time_broker": planned.isoformat(),
            "submission_time_broker": submission_time,
            "requested_price": requested_price,
            "intended_entry": intended_entry,
            "entry_spread_pips": (ask - bid) / float(PIP_SIZE),
            "volume": volume,
            "stop_loss": stop,
            "take_profit": target,
        }
        if validation_run:
            validation["phase"] = "submitting"
            validation["trade_id"] = signal_values["trade_id"]
            validation["signal_time_broker"] = signal_time
        _write_state(self.state_file, state)
        self._log(
            "order_submission_started",
            offset,
            signal_time_broker=signal_time,
            planned_entry_time_broker=planned.isoformat(),
            submission_time_broker=submission_time,
            direction=signal_values["direction"],
            volume=volume,
            price=requested_price,
            stop_loss=stop,
            take_profit=target,
            details="single market order; no automatic retry",
        )

        try:
            result = module.order_send(request)
        except Exception as exc:
            self._log(
                "reconciliation_error",
                offset,
                signal_time_broker=signal_time,
                planned_entry_time_broker=planned.isoformat(),
                submission_time_broker=submission_time,
                direction=signal_values["direction"],
                details=f"order_send outcome ambiguous: {exc}",
            )
            raise ExecutorError(
                "order_send outcome is ambiguous; execution stopped for reconciliation"
            ) from exc
        if result is None:
            self._log(
                "reconciliation_error",
                offset,
                signal_time_broker=signal_time,
                planned_entry_time_broker=planned.isoformat(),
                submission_time_broker=submission_time,
                direction=signal_values["direction"],
                details="order_send returned no result; no retry attempted",
            )
            raise ExecutorError(
                "order_send outcome is unknown; execution stopped for reconciliation"
            )
        retcode = int(getattr(result, "retcode", -1))
        if retcode == int(module.TRADE_RETCODE_DONE):
            self._log(
                "order_submitted",
                offset,
                signal_time_broker=signal_time,
                planned_entry_time_broker=planned.isoformat(),
                submission_time_broker=submission_time,
                direction=signal_values["direction"],
                order_ticket=getattr(result, "order", ""),
                deal_ticket=getattr(result, "deal", ""),
                details=f"MT5 retcode={retcode}",
            )
        if retcode != int(module.TRADE_RETCODE_DONE):
            if retcode in {
                int(getattr(module, "TRADE_RETCODE_REJECT", -2)),
                int(getattr(module, "TRADE_RETCODE_INVALID", -3)),
                int(getattr(module, "TRADE_RETCODE_INVALID_STOPS", -4)),
                int(getattr(module, "TRADE_RETCODE_NO_MONEY", -5)),
            }:
                state["active_position"] = None
                if validation_run:
                    validation["phase"] = "rejected"
                    validation["retcode"] = retcode
                _write_state(self.state_file, state)
                self._log(
                    "order_rejected",
                    offset,
                    signal_time_broker=signal_time,
                    planned_entry_time_broker=planned.isoformat(),
                    submission_time_broker=submission_time,
                    direction=signal_values["direction"],
                    order_ticket=getattr(result, "order", ""),
                    details=f"MT5 retcode={retcode}; no retry",
                )
                return
            raise ExecutorError(
                f"order result retcode {retcode} is not definitive; execution stopped"
            )

        deal_ticket = int(getattr(result, "deal", 0) or 0)
        if deal_ticket <= 0:
            raise ExecutorError(
                "order result has no deal ticket; execution stopped for reconciliation"
            )
        deal = _deal_by_ticket(module, deal_ticket)
        position_id = int(getattr(deal, "position_id", 0) or 0)
        if position_id <= 0:
            raise ExecutorError(
                "filled deal has no position identifier; execution stopped for reconciliation"
            )
        fill_time_msc = int(getattr(deal, "time_msc", 0) or 0)
        if fill_time_msc <= 0:
            raise ExecutorError(
                "filled deal has no millisecond timestamp; execution stopped for reconciliation"
            )
        fill_time = epoch_to_broker_time(
            fill_time_msc // 1000, offset
        ).replace(microsecond=(fill_time_msc % 1000) * 1000).isoformat()
        fill_delay_ms = (
            datetime.fromisoformat(fill_time) - planned
        ).total_seconds() * 1000
        fill_price = float(getattr(deal, "price", getattr(result, "price", 0)))
        if fill_price <= 0:
            raise ExecutorError(
                "filled deal has no valid price; execution stopped for reconciliation"
            )

        open_positions = _position_list(module)
        if len(open_positions) != 1:
            raise ExecutorError("unexpected account position state after fill; reconciliation required")
        position = next(
            (
                item
                for item in open_positions
                if int(getattr(item, "identifier", getattr(item, "ticket", 0)))
                == position_id
            ),
            None,
        )
        if position is None:
            raise ExecutorError(
                "filled position is not visible; execution stopped for reconciliation"
            )
        actual_stop = fill_price - float(STOP_PIPS * PIP_SIZE) if buy else fill_price + float(STOP_PIPS * PIP_SIZE)
        actual_target = fill_price + float(TARGET_PIPS * PIP_SIZE) if buy else fill_price - float(TARGET_PIPS * PIP_SIZE)
        if (
            abs(float(getattr(position, "sl", 0)) - actual_stop) > 1e-8
            or abs(float(getattr(position, "tp", 0)) - actual_target) > 1e-8
        ):
            modify = {
                "action": int(module.TRADE_ACTION_SLTP),
                "symbol": SYMBOL,
                "position": int(getattr(position, "ticket", position_id)),
                "sl": actual_stop,
                "tp": actual_target,
                "magic": MAGIC_NUMBER,
            }
            modify_result = module.order_send(modify)
            if (
                modify_result is None
                or int(getattr(modify_result, "retcode", -1))
                != int(module.TRADE_RETCODE_DONE)
            ):
                raise ExecutorError(
                    "could not confirm V1 stop/target from actual fill; execution stopped"
                )
            open_positions = _position_list(module)
            position = next(
                (
                    item
                    for item in open_positions
                    if int(getattr(item, "identifier", getattr(item, "ticket", 0)))
                    == position_id
                ),
                None,
            )
            if position is None or (
                abs(float(getattr(position, "sl", 0)) - actual_stop) > 1e-8
                or abs(float(getattr(position, "tp", 0)) - actual_target) > 1e-8
            ):
                raise ExecutorError(
                    "broker did not confirm attached V1 stop and target; execution stopped"
                )

        active = state["active_position"]
        active.update(
            {
                "phase": "open",
                "position_id": position_id,
                "order_ticket": int(getattr(result, "order", 0) or 0),
                "deal_ticket": deal_ticket,
                "fill_time_broker": fill_time,
                "fill_delay_ms": fill_delay_ms,
                "fill_price": fill_price,
                "actual_stop": actual_stop,
                "actual_target": actual_target,
            }
        )
        if validation_run:
            validation["phase"] = "monitoring"
        _write_state(self.state_file, state)
        common = {
            "signal_time_broker": signal_time,
            "planned_entry_time_broker": planned.isoformat(),
            "submission_time_broker": submission_time,
            "fill_time_broker": fill_time,
            "fill_delay_ms": fill_delay_ms,
            "direction": signal_values["direction"],
            "order_ticket": active["order_ticket"],
            "deal_ticket": deal_ticket,
            "position_id": position_id,
            "volume": volume,
            "price": fill_price,
            "stop_loss": actual_stop,
            "take_profit": actual_target,
        }
        self._log("order_filled", offset, **common)
        self._log("stop_attached", offset, **common)
        self._log("take_profit_attached", offset, **common)

    def _monitor_position(
        self,
        module: Any,
        config: Any,
        symbol_info: Any,
        state: dict[str, Any],
        positions: list[Any],
    ) -> None:
        active = state["active_position"]
        position_id = int(active["position_id"])
        matching = [
            item
            for item in positions
            if int(getattr(item, "identifier", getattr(item, "ticket", 0)))
            == position_id
        ]
        if matching:
            if len(positions) > 1:
                raise ExecutorError("more than one account position is open; execution stopped")
            position = matching[0]
            expected_stop = float(active["actual_stop"])
            expected_target = float(active["actual_target"])
            if (
                abs(float(getattr(position, "sl", 0)) - expected_stop) > 1e-8
                or abs(float(getattr(position, "tp", 0)) - expected_target) > 1e-8
            ):
                raise ExecutorError(
                    "tracked position protection changed; execution stopped for reconciliation"
                )
            return
        if positions:
            raise ExecutorError(
                "tracked position disappeared while another position is open; reconciliation required"
            )
        try:
            deals = module.history_deals_get(position=position_id)
        except Exception as exc:
            raise ExecutorError(f"position history retrieval failed: {exc}") from exc
        if deals is None:
            raise ExecutorError("position close cannot be reconciled; execution stopped")

        entry_code = int(module.DEAL_ENTRY_IN)
        exit_codes = {
            int(module.DEAL_ENTRY_OUT),
            int(getattr(module, "DEAL_ENTRY_OUT_BY", module.DEAL_ENTRY_OUT)),
        }
        entry_deals = [deal for deal in deals if int(getattr(deal, "entry", -1)) == entry_code]
        exit_deals = [deal for deal in deals if int(getattr(deal, "entry", -1)) in exit_codes]
        if not exit_deals:
            raise ExecutorError("closed position has no exit deal; execution stopped")
        offset = config.broker_utc_offset
        try:
            record = build_trade_record(
                signal=active["signal"],
                entry_deals=entry_deals,
                exit_deals=exit_deals,
                symbol_info=symbol_info,
                broker_offset=offset,
                account_alias=os.environ.get("MT5_DEMO_ACCOUNT_ALIAS", "ICM-DEMO"),
                intended_entry=float(active["intended_entry"]),
                entry_spread_pips=float(active["entry_spread_pips"]),
                planned_entry_time=active["planned_entry_time_broker"],
                submission_time=active["submission_time_broker"],
                fill_delay_ms=float(active["fill_delay_ms"]),
                order_reference=f"order={active['order_ticket']};position={position_id}",
                entry_code=entry_code,
                exit_codes=exit_codes,
                deal_buy_type=int(module.DEAL_TYPE_BUY),
                deal_sell_type=int(module.DEAL_TYPE_SELL),
                exit_reason_codes={
                    int(getattr(module, "DEAL_REASON_SL", -1)): "stop_loss",
                    int(getattr(module, "DEAL_REASON_TP", -2)): "take_profit",
                },
                expected_volume=float(active["volume"]),
                expected_order_ticket=int(active["order_ticket"]),
                expected_magic=MAGIC_NUMBER,
                position_id=position_id,
            )
            validation = state.get("single_trade_validation")
            paths = self._check_validation_descriptor(validation) if validation is not None else None
            destination = paths["trade_log"] if paths is not None else self.trade_log
            other_log = self.trade_log if paths is not None else self._validation_paths()["trade_log"]
            from paper_trading.demo_trade_utils import ensure_no_cross_log_conflict
            ensure_no_cross_log_conflict(record, other_log)
            existing = read_trade_log(destination) if destination.exists() else []
            prior = next(
                (trade for trade in existing if trade["trade_id"] == record["trade_id"]),
                None,
            )
            if prior is not None and prior != record:
                raise ReconciliationError(
                    "trade_id already exists with different broker reconciliation data"
                )
            if prior is None:
                append_completed_trade(record, destination)
            if paths is not None:
                self._refresh_validation_reports(paths)
            else:
                self._refresh_reports()
        except (ReconciliationError, ValueError, OSError) as exc:
            self._log(
                "reconciliation_error",
                offset,
                signal_time_broker=active["signal"]["signal_bar_open_time_broker"],
                planned_entry_time_broker=active["planned_entry_time_broker"],
                submission_time_broker=active["submission_time_broker"],
                fill_time_broker=active["fill_time_broker"],
                fill_delay_ms=active["fill_delay_ms"],
                direction=active["signal"]["direction"],
                position_id=position_id,
                details=str(exc),
            )
            raise ExecutorError(f"closed position reconciliation failed: {exc}") from exc

        self._log(
            "position_closed",
            offset,
            signal_time_broker=active["signal"]["signal_bar_open_time_broker"],
            planned_entry_time_broker=active["planned_entry_time_broker"],
            submission_time_broker=active["submission_time_broker"],
            fill_time_broker=active["fill_time_broker"],
            fill_delay_ms=active["fill_delay_ms"],
            direction=active["signal"]["direction"],
            order_ticket=active["order_ticket"],
            deal_ticket=active["deal_ticket"],
            position_id=position_id,
            details=f"trade_id={record['trade_id']}",
        )
        state["active_position"] = None
        if state.get("single_trade_validation") is not None:
            state["single_trade_validation"]["phase"] = "completed"
            state["single_trade_validation"]["record"] = record
        _write_state(self.state_file, state)

    def run_single_trade_validation(
        self, poll_interval_seconds: float = POLL_INTERVAL_SECONDS
    ) -> str:
        """Allow one persisted entry attempt, then monitor only until flat."""
        if poll_interval_seconds <= 0:
            raise ValueError("poll interval must be positive")
        mt5_connector.initialize_connection()
        try:
            with _exclusive_instance_lock(self.lock_file):
                module, config = mt5_connector._require_connection()
                validate_demo_account(module, config.login)
                state = _read_state(self.state_file)
                if state.get("single_trade_validation") is not None:
                    raise ExecutorError("prior single-trade validation exists; manual reconciliation required")
                if state["active_position"] is not None or _position_list(module):
                    raise ExecutorError("single-trade validation requires an idle state and flat account")
                pending = module.orders_get()
                if pending is None or len(pending):
                    raise ExecutorError("pending orders are present or unavailable")
                info = self._verify_symbol_read_only(module)
                self._verify_approved_volume(info, Decimal("0.01"))
                self._verify_validation_startup(module, config)
                state["single_trade_validation"] = {
                    "phase": "armed", **self._validation_descriptor()
                }
                _write_state(self.state_file, state)
                try:
                    while True:
                        self._process_once(validation_run=True)
                        state = _read_state(self.state_file)
                        phase = state["single_trade_validation"]["phase"]
                        if phase in {"rejected", "completed"}:
                            return phase
                        time.sleep(poll_interval_seconds)
                except BaseException:
                    state = _read_state(self.state_file)
                    state["single_trade_validation"]["phase"] = "failed"
                    _write_state(self.state_file, state)
                    raise
        finally:
            mt5_connector.shutdown_connection()

    def recover_single_trade_validation(self) -> None:
        """Reconcile a known closed validation position without sending orders."""
        mt5_connector.initialize_connection()
        try:
            with _exclusive_instance_lock(self.lock_file):
                module, config = mt5_connector._require_connection()
                validate_demo_account(module, config.login)
                state = _read_state(self.state_file)
                validation = state.get("single_trade_validation")
                self._check_validation_descriptor(validation)
                active = state["active_position"]
                if validation.get("phase") not in {"failed", "monitoring"} or not active or active.get("phase") != "open":
                    raise ExecutorError("validation is not a known open position; manual reconciliation required")
                if _position_list(module):
                    raise ExecutorError("account is not flat; operator reconciliation required")
                pending = module.orders_get()
                if pending is None or pending:
                    raise ExecutorError("pending orders are present or unavailable")
                self._monitor_position(module, config, self._verify_symbol_read_only(module), state, [])
        finally:
            mt5_connector.shutdown_connection()

    def write_single_trade_result(self, path: Path = DEFAULT_SINGLE_RESULT) -> None:
        state = _read_state(self.state_file)
        validation = state.get("single_trade_validation") or {}
        record = validation.get("record") or {}
        events = read_events(self.execution_log)
        trade_id = validation.get("trade_id")
        active = state.get("active_position") or {}
        signal_time = validation.get("signal_time_broker") or (
            active.get("signal") or {}
        ).get("signal_bar_open_time_broker")
        if record:
            signal_time = record.get("signal_bar_open_time_broker")
        relevant = [row for row in events if signal_time and row["signal_time_broker"] == signal_time]
        kinds = {row["event"] for row in relevant}
        filled = next((row for row in relevant if row["event"] == "order_filled"), {})
        phase = validation.get("phase", "not_run")
        complete = phase == "completed" and bool(record)
        compliant = record.get("rule_compliant") == "true"
        outcome = "EXECUTOR_FAILED_VALIDATION"
        def val(value: Any) -> str:
            return str(value) if value not in (None, "") else "not observed"
        lines = [
            "# Single-Trade Validation Result", "",
            f"- State: {phase}; trade ID: {val(trade_id)}",
            f"- Order accepted: {'yes' if 'order_submitted' in kinds else 'not established'}",
            f"- SL attached: {'confirmed' if 'stop_attached' in kinds else 'not established'}",
            f"- TP attached: {'confirmed' if 'take_profit_attached' in kinds else 'not established'}",
            f"- Reconciliation successful: {'yes' if complete else 'not established'}",
            f"- Trade capture successful: {'yes' if complete else 'not established'}",
            f"- Metrics updated: {'yes' if complete else 'not established'}",
            f"- Simulated validation gate updated: {'yes' if complete else 'not established'}",
            "- Formal study metrics and gate are not updated by validation.",
            f"- V1 entry/exit compliance: {'yes' if compliant else 'not established or noncompliant'}",
            f"- Signal bar time: {val(signal_time)}",
            f"- Planned entry time: {val(filled.get('planned_entry_time_broker'))}",
            f"- Fill time: {val(filled.get('fill_time_broker'))}",
            f"- Fill delay (ms): {val(filled.get('fill_delay_ms'))}",
            f"- Entry price: {val(filled.get('price'))}",
            f"- Stop: {val(filled.get('stop_loss'))}; target: {val(filled.get('take_profit'))}",
            f"- Exit reason: {val(record.get('exit_reason'))}",
            f"- Commission including fees (pips): {val(record.get('commission_pips'))}",
            f"- Swap (pips): {val(record.get('financing_pips'))}",
            "",
            "One execution does not guarantee future fills. Broker cash costs and tick-value "
            "conversion require independent verification; pips above are computed values. "
            "The final decision remains failed until independently verified.",
            "",
            f"**{outcome}**", "",
        ]
        path.write_text("\n".join(lines), encoding="utf-8")

    def _refresh_reports(self) -> None:
        trades = read_trade_log(self.trade_log)
        metrics = calculate_demo_metrics(trades)
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        self.metrics_file.write_text(
            json.dumps(metrics, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        count = int(metrics["eligible_trade_count"])
        gate_text = self.gate_file.read_text(encoding="utf-8")
        import re

        gate_text, count_updates = re.subn(
            r"(?m)^- \*\*Demo Trades Completed:\*\* \*\*\d+ / 100\*\*$",
            f"- **Demo Trades Completed:** **{count} / 100**",
            gate_text,
        )
        gate_text, reason_updates = re.subn(
            r"(?m)^- \*\*Reason:\*\* \*\*.*\*\*$",
            (
                "- **Reason:** **100 eligible demo trades completed; V2 review may begin.**"
                if count >= 100
                else f"- **Reason:** **{100-count} eligible demo trades remain.**"
            ),
            gate_text,
        )
        gate_text, eligibility_updates = re.subn(
            r"(?m)^- \*\*V2 Eligibility:\*\* \*\*.*\*\*$",
            (
                "- **V2 Eligibility:** **READY_FOR_V2_REVIEW**"
                if count >= 100
                else "- **V2 Eligibility:** **BLOCKED**"
            ),
            gate_text,
        )
        if count_updates != 1 or reason_updates != 1 or eligibility_updates != 1:
            raise ExecutorError("DEMO_GATE_STATUS.md has an unrecognized schema")
        self.gate_file.parent.mkdir(parents=True, exist_ok=True)
        self.gate_file.write_text(gate_text, encoding="utf-8")

    def run(self, poll_interval_seconds: float = POLL_INTERVAL_SECONDS) -> None:
        if poll_interval_seconds <= 0:
            raise ValueError("poll interval must be positive")
        mt5_connector.initialize_connection()
        _, config = mt5_connector._require_connection()
        try:
            while True:
                self.process_once()
                time.sleep(poll_interval_seconds)
        except Exception as exc:
            self._log(
                "reconciliation_error",
                config.broker_utc_offset,
                details=f"executor stopped: {exc}",
            )
            raise
        finally:
            mt5_connector.shutdown_connection()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--verify-only",
        action="store_true",
        help="connect to MT5 and perform read-only startup checks; never submit or modify orders",
    )
    mode.add_argument(
        "--arm-demo-execution",
        action="store_true",
        help="explicitly arm order submission; all demo safety checks remain mandatory",
    )
    mode.add_argument(
        "--single-trade-validation",
        action="store_true",
        help="arm at most one 0.01 lot demo entry, then monitor only until closed",
    )
    mode.add_argument(
        "--recover-validation",
        action="store_true",
        help="reconcile a known closed validation position without submitting or modifying orders",
    )
    mode.add_argument(
        "--verify-validation",
        action="store_true",
        help="read-only validation startup checks without arming or modifying broker orders",
    )
    parser.add_argument(
        "--verify-volume",
        type=Decimal,
        default=Decimal("0.01"),
        help="approved lot size checked by --verify-only (default: 0.01)",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=POLL_INTERVAL_SECONDS,
        help="seconds between completed-bar checks",
    )
    args = parser.parse_args()
    if args.poll_interval <= 0:
        parser.error("--poll-interval must be positive")
    if args.verify_volume <= 0 or not args.verify_volume.is_finite():
        parser.error("--verify-volume must be a positive finite decimal")
    try:
        executor = DemoExecutor()
        if args.verify_only:
            passed = executor.verify_only(approved_volume=args.verify_volume)
            print(f"Integration report: {DEFAULT_INTEGRATION_RESULT}")
            print(
                "READY_FOR_DEMO_TRADE_1" if passed else "EXECUTOR_BLOCKED"
            )
            if not passed:
                return 1
            return 0
        if args.single_trade_validation:
            try:
                phase = executor.run_single_trade_validation(args.poll_interval)
            finally:
                executor.write_single_trade_result()
            return 0 if phase == "completed" else 1
        if args.verify_validation:
            executor.verify_validation_only()
            print("Validation startup checks passed; no order or position was modified.")
            return 0
        if args.recover_validation:
            try:
                executor.recover_single_trade_validation()
            finally:
                executor.write_single_trade_result()
            return 0
        if not args.arm_demo_execution:
            parser.error(
                "select --verify-only for read-only checks or --arm-demo-execution to arm order submission"
            )
        executor.run(args.poll_interval)
    except (ExecutorError, MT5ConnectorError, KeyboardInterrupt) as exc:
        if isinstance(exc, KeyboardInterrupt):
            print("Demo executor stopped by operator.")
            return 0
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
