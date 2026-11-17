import csv
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from paper_trading.broker_time import parse_broker_timezone
from paper_trading.signal_observer import (
    OBSERVATION_FIELDS,
    _read_observations,
    generate_report,
    observe,
    observe_latest_bar,
)


def bars_ending_at(timestamp):
    base = timestamp.replace(minute=timestamp.minute - timestamp.minute % 5, second=0, microsecond=0)
    output = []
    for index in range(21):
        bar_time = base - timedelta(minutes=(20 - index) * 5)
        output.append(
            {
                "timestamp": bar_time.isoformat(),
                "open": 1.1000,
                "high": 1.1005,
                "low": 1.0995,
                "close": 1.1000,
            }
        )
    return output


class SignalObserverTests(unittest.TestCase):
    def test_records_completed_bar_and_deduplicates_by_bar_timestamp(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log = Path(temp_dir) / "observations.csv"
            bars = bars_ending_at(datetime.now(parse_broker_timezone("+02:00")))
            with patch(
                "paper_trading.signal_observer.get_recent_m5_bars",
                return_value=bars,
            ) as get_bars, patch(
                "paper_trading.signal_observer.mt5_connector.get_broker_utc_offset",
                return_value="+02:00",
            ):
                first = observe_latest_bar(log)
                second = observe_latest_bar(log)
            self.assertIsNotNone(first)
            self.assertIsNone(second)
            self.assertEqual(get_bars.call_args.kwargs, {"count": 21, "symbol": "EURUSD"})

            rows = _read_observations(log)
            self.assertEqual(len(rows), 1)
            self.assertEqual(tuple(rows[0]), OBSERVATION_FIELDS)
            self.assertEqual(rows[0]["signal_type"], "NO SIGNAL")
            self.assertEqual(rows[0]["raw_signal_status"], "NO_BREAKOUT")
            self.assertEqual(rows[0]["symbol"], "EURUSD")

    def test_existing_duplicate_bar_is_not_appended_again(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log = Path(temp_dir) / "observations.csv"
            bars = bars_ending_at(datetime.now(parse_broker_timezone("+02:00")))
            with patch(
                "paper_trading.signal_observer.get_recent_m5_bars",
                return_value=bars,
            ), patch(
                "paper_trading.signal_observer.mt5_connector.get_broker_utc_offset",
                return_value="+02:00",
            ):
                first = observe_latest_bar(log)
                self.assertIsNone(observe_latest_bar(log))
            rows = _read_observations(log)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["bar_timestamp"], first["bar_timestamp"])

    def test_records_breakout_status_and_level(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log = Path(temp_dir) / "observations.csv"
            bars = bars_ending_at(datetime.now(parse_broker_timezone("+02:00")))
            bars[-1]["close"] = 1.1006
            bars[-1]["high"] = 1.1007
            with patch(
                "paper_trading.signal_observer.get_recent_m5_bars",
                return_value=bars,
            ), patch(
                "paper_trading.signal_observer.mt5_connector.get_broker_utc_offset",
                return_value="+02:00",
            ):
                row = observe_latest_bar(log)
            self.assertEqual(row["signal_type"], "LONG")
            self.assertEqual(row["raw_signal_status"], "BREAKOUT")
            self.assertEqual(row["breakout_level"], 1.1005)
            self.assertEqual(row["close_price"], 1.1006)

    def test_observer_writes_report_on_bounded_stop_and_shuts_down(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log = Path(temp_dir) / "observations.csv"
            report = Path(temp_dir) / "report.md"
            bars = bars_ending_at(datetime.now(parse_broker_timezone("+02:00")))
            with (
                patch("paper_trading.signal_observer.mt5_connector.initialize_connection"),
                patch("paper_trading.signal_observer.mt5_connector.shutdown_connection") as shutdown,
                patch("paper_trading.signal_observer.mt5_connector.get_broker_utc_offset", return_value="+02:00"),
                patch(
                    "paper_trading.signal_observer.get_recent_m5_bars",
                    return_value=bars,
                ),
                patch("paper_trading.signal_observer.time.sleep"),
            ):
                observe(
                    poll_interval_seconds=0.1,
                    log_path=log,
                    report_path=report,
                    max_polls=2,
                )
            shutdown.assert_called_once()
            self.assertTrue(report.is_file())
            text = report.read_text(encoding="utf-8")
            self.assertIn("Observations logged: 1 completed bars", text)
            self.assertIn("Demo trades remain 0 / 100", text)
            self.assertIn("not trade-performance analysis", text)

    def test_report_flags_timestamp_skew_and_no_signal_period(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log = Path(temp_dir) / "observations.csv"
            report = Path(temp_dir) / "report.md"
            now = datetime.now(parse_broker_timezone("+02:00")).replace(
                second=0, microsecond=0
            )
            base = now - timedelta(minutes=10)
            with log.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=OBSERVATION_FIELDS)
                writer.writeheader()
                for index in range(2):
                    bar_time = base + timedelta(minutes=5 * index)
                    writer.writerow(
                        {
                            "timestamp": now.isoformat(),
                            "signal_type": "NO SIGNAL",
                            "symbol": "EURUSD",
                            "bar_timestamp": bar_time.isoformat(),
                            "breakout_level": "",
                            "close_price": "1.1",
                            "raw_signal_status": "NO_BREAKOUT",
                        }
                    )

            text = generate_report(log, report)
            self.assertIn("0/2 observed bars (0.00%)", text)
            self.assertIn("2 completed bars", text)
            self.assertIn("Logging anomalies", text)
            self.assertIn("bar close time differs from observation clock", text)
            self.assertIn("configured broker offset", text)

    def test_rejects_bad_log_header(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log = Path(temp_dir) / "observations.csv"
            log.write_text("timestamp,signal_type\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "observation log header"):
                _read_observations(log)


if __name__ == "__main__":
    unittest.main()
