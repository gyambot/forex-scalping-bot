# Strategy Evolution Log

No V2 or later version is designed or approved. V1 remains frozen. A new
version cannot be proposed until baseline metrics exist and at least 100
completed demo trades have been recorded; historical trades do not count.
Current demo count: **0 / 100**.

## Breakout Scalping V1 — frozen baseline

- **Hypothesis:** A close outside the prior 20 completed M5 bars' range,
  entered at the next bar's open, can achieve positive expectancy with a fixed
  10-pip stop and 20-pip target.
- **Historical sample:** EURUSD M5 bid data, 2025-01-01 through 2025-12-31;
  73,683 complete M5 bars after documented data-quality exclusions.
- **Modeled spread:** Fixed 1.0 pip; no commission, slippage, financing, or
  variable spread.
- **Backtest result:** See
  [2025 baseline report](../reports/BASELINE_BACKTEST_2025.md) and generated
  [metrics](../backtests/2025_histdata_v1/metrics.json).
- **Temporal validation:** January-October 2026, unchanged V1 settings; see
  [validation report](../validation/2026_histdata_v1/VALIDATION_REPORT.md).

| Metric | V1 result |
|---|---:|
| Net Profit | -3,261.4 pips |
| Profit Factor | 0.7982 |
| Expectancy | -1.4431 pips / -0.1443 R |
| Win Rate | 28.5841% |
| Maximum Drawdown | 3,285.3 pips |
| Average Trade | -1.4431 pips |
| Average Hold Time | 123.6549 minutes (bar-count estimate) |
| Trades Per Day | 7.2436 |
| Trade Count | 2,260 historical trades |

### Validation result (not demo)

The later 2026 sample also produced negative expectancy (-0.1612 R) and profit
factor 0.7802, with net profit -2,203.7 pips and maximum drawdown 2,415.6 pips
across 1,367 historical trades. This does not pass validation for promotion.
These trades are not demo trades and do not count toward the 100-trade gate.

### Weakness and interpretation

The V1 baseline is negative over this historical sample: net P&L and expectancy
are negative, profit factor is below 1, and pip drawdown is substantial. This
weakens the hypothesis under this data source and the frozen execution model.
It does not establish that any particular session or volatility condition
caused the losses; consult the descriptive weekly breakdown and collect
forward-demo evidence.

### Next action

No next-version hypothesis is proposed. Keep V1 frozen; do not treat either
historical run as demo evidence. Any demo activity must be explicitly reviewed
against the negative results, and at least 100 completed demo trades must be
recorded before V2 may be proposed.
Historical backtest trades do not contribute to that count. Record any
rejection cause and evidence before considering a future version.
