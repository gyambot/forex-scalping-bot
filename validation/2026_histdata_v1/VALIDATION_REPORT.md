# Breakout Scalping V1 — Temporal Validation Report

## Run identification

- Validation period: 2026-01-01 through 2026-10-31 (available complete monthly data)
- Data provider/source: HistData.com generic ASCII EUR/USD M1 bid bars
- Converted data: [`eurusd_m5_2026_01_10.csv`](../../data/eurusd_m5_2026_01_10.csv)
- Source details and SHA-256: [data provenance](../../data/README.md)
- Run date: 2026-11-12
- Code revision: local workspace snapshot; no Git repository available
- Frozen strategy version: Breakout Scalping V1
- Parameters changed from frozen specification: **No**
- Validation period was not used to tune or change parameters: **Yes**

## Data checks

- Instrument/timeframe: EURUSD / M5
- Timezone and price side: UTC / bid OHLC
- Complete M5 bars: 60,551
- Coverage of retained bars: 2026-01-01T22:05:00Z to 2026-10-30T20:50:00Z
- Source issues: 8 duplicate M1 rows; 3 out-of-order source dates
  (2026-07-05, 2026-09-24, 2026-10-09) excluded; 955 incomplete M5 buckets
  excluded; 784 gaps over five minutes remain.
- Known limitations: same provider as the 2025 baseline; fixed EST-to-UTC
  interpretation; constant modeled 1.0-pip spread; no commission, slippage,
  financing, or tick-level fills; provider disclaims warranty/certification.

## Required performance metrics

| Metric | Result |
|---|---:|
| Net Profit | -2,203.7 pips |
| Profit Factor | 0.7802 |
| Expectancy | -1.6121 pips / -0.1612 R |
| Win Rate | 28.6759% |
| Maximum Drawdown | 2,415.6 pips |
| Average Trade | -1.6121 pips |
| Average Hold Time | 186.9751 minutes (bar-count estimate) |
| Trades Per Day | 5.2780 |
| Trade Count | 1,367 historical trades |

Generated files: [`metrics.json`](./metrics.json) and
[`trades.csv`](./trades.csv).

## Review

Both expectancy and profit factor remained negative/sub-1 on this later sample.
The historical validation therefore does not support a promotion or a claim of
robust positive performance. A pre-declared account-level drawdown limit was
not supplied, and pip drawdown cannot be converted to account risk without
position sizing and capital assumptions.

This is a temporal holdout from the same vendor, not an independent-provider
replication or a demo result. It cannot identify a causal session or volatility
weakness by itself. The strategy and its parameters remain unchanged.

## Decision

- Outcome: **Fail for promotion**
- Reason: Net profit and expectancy are negative, and profit factor is 0.7802;
  promotion requirements are not met.
- If rejected, market condition that exposed weakness: Not established by this
  aggregate validation alone. Use the descriptive weekly analysis and future
  completed demo records; do not infer a filter or parameter change.
- Evidence-supported next hypothesis: **None proposed**
- Demo gate: **0 / 100 completed demo trades**; historical trades do not count.
- Reviewer/date: Automated report / 2026-11-12
