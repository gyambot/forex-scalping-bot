import csv
import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.prepare_histdata import convert_archive
from scripts.backtest import load_bars


def source_row(timestamp, open_price, high, low, close):
    return (
        f"20250101 {timestamp};{open_price:.6f};{high:.6f};{low:.6f};{close:.6f};0\n"
    )


class PrepareHistDataTests(unittest.TestCase):
    def test_merges_duplicates_converts_fixed_est_and_drops_incomplete_bucket(self):
        rows = [
            source_row("170000", 1.1000, 1.1002, 1.0998, 1.1001),
            source_row("170100", 1.1001, 1.1003, 1.1000, 1.1002),
            source_row("170200", 1.1002, 1.1004, 1.1001, 1.1003),
            source_row("170200", 1.1003, 1.1008, 1.0999, 1.1005),
            source_row("170300", 1.1005, 1.1006, 1.1002, 1.1004),
            source_row("170400", 1.1004, 1.1007, 1.1003, 1.1006),
            source_row("170500", 1.1006, 1.1007, 1.1005, 1.1006),
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir) / "eurusd.zip"
            output_path = Path(temp_dir) / "eurusd_m5.csv"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("DAT_ASCII_EURUSD_M1_2025.csv", "".join(rows))

            summary = convert_archive(archive_path, output_path)
            with output_path.open(newline="", encoding="utf-8") as file:
                bars = load_bars(file)

        self.assertEqual(summary["source_rows"], 7)
        self.assertEqual(summary["duplicate_rows_merged"], 1)
        self.assertEqual(summary["complete_m5_bars"], 1)
        self.assertEqual(summary["incomplete_m5_buckets_excluded"], 1)
        self.assertEqual(len(bars), 1)
        self.assertEqual(bars[0].timestamp.isoformat(), "2025-01-01T22:00:00+00:00")
        self.assertAlmostEqual(bars[0].open, 1.1000)
        self.assertAlmostEqual(bars[0].high, 1.1008)
        self.assertAlmostEqual(bars[0].low, 1.0998)
        self.assertAlmostEqual(bars[0].close, 1.1006)

    def test_excludes_out_of_order_source_date(self):
        rows = [
            source_row("170000", 1.1000, 1.1002, 1.0998, 1.1001),
            source_row("170100", 1.1001, 1.1003, 1.1000, 1.1002),
            source_row("170200", 1.1002, 1.1004, 1.1001, 1.1003),
            source_row("170300", 1.1003, 1.1005, 1.1002, 1.1004),
            source_row("170400", 1.1004, 1.1006, 1.1003, 1.1005),
        ]
        rows.extend(
            row.replace("20250101", "20250102")
            for row in [
                source_row("170100", 1.1000, 1.1002, 1.0998, 1.1001),
                source_row("170000", 1.1001, 1.1003, 1.1000, 1.1002),
            ]
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir) / "eurusd.zip"
            output_path = Path(temp_dir) / "eurusd_m5.csv"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("DAT_ASCII_EURUSD_M1_2025.csv", "".join(rows))
            summary = convert_archive(archive_path, output_path)
            with output_path.open(newline="", encoding="utf-8") as file:
                bars = load_bars(file)

        self.assertEqual(summary["out_of_order_source_dates_excluded"], ["2025-01-02"])
        self.assertEqual(len(bars), 1)


if __name__ == "__main__":
    unittest.main()
