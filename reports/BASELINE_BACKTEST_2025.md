# Breakout Scalping V1 — 2025 Historical Baseline

**Run:** `backtests/2025_histdata_v1/`  
**Strategy:** Frozen Breakout Scalping V1; no parameter tuning  
**Result:** Negative under this historical sample and modeled execution costs

## Required metrics

| Metric | Result |
|---|---:|
| Net Profit | -3,261.4 pips |
| Profit Factor | 0.7982 |
| Expectancy | -1.4431 pips / -0.1443 R |
| Win Rate | 28.5841% |
| Maximum Drawdown | 3,285.3 pips |
| Average Trade | -1.4431 pips |
| Average Hold Time | 123.6549 minutes |
| Trades Per Day | 7.2436 |
| Trade Count | 2,260 |

Machine-readable results and individual trades are in
[`metrics.json`](../backtests/2025_histdata_v1/metrics.json) and
[`trades.csv`](../backtests/2025_histdata_v1/trades.csv).
The ISO-week breakdown is in the
[weekly review](./weekly/WEEKLY_REVIEW.md).

## Data and method

- Source: HistData.com generic ASCII EUR/USD M1 bars for calendar year 2025;
  vendor states bar OHLC are bid-based.
- Canonical input: [`eurusd_m5_2025.csv`](../data/eurusd_m5_2025.csv)
- Raw archive and conversion details: [data provenance](../data/README.md)
- Input coverage: 73,683 complete M5 bars; timestamps normalized from fixed
  EST (UTC-05:00) to UTC.
- Data exclusions: one out-of-order source date (2025-10-26) was excluded;
  incomplete five-minute buckets were omitted; remaining gaps are retained as
  gaps rather than filled with invented prices.
- Frozen V1 cost assumption: 1.0-pip constant spread. Commission, slippage,
  latency, financing, variable spread, and tick-level fills are not modeled.
- A position open at the sample end is closed at the final available bar close
  under the documented `end_of_data` rule.

## Findings

The baseline loses 3,261.4 pips with profit factor 0.7982 and expectancy
-0.1443 R per trade. This is a rejection of the **historical performance
hypothesis for this sample and model**, not evidence that a specific filter
would improve it. The weekly breakdown is descriptive and uses fixed UTC
session buckets; it must not be treated as an optimization instruction.

The later, unchanged-parameter temporal validation is also negative; see the
[2026 validation report](../validation/2026_histdata_v1/VALIDATION_REPORT.md).
The 2025 and 2026 trade counts are historical only and do not satisfy the
100-completed-demo-trade gate.

## Decision and next steps

- V1 parameters: **remain frozen**.
- V2: **not designed or proposed**.
- Validation: run a distinct later sample with the same V1 settings before
  forward demo operation, following the validation workflow.
- Demo: record only actual completed demo positions in the paper-trading log.
  At least 100 completed demo trades are required before V2 may be proposed.
- No historical trades count toward the 100-demo-trade gate. No demo trades
  were supplied for this report.
