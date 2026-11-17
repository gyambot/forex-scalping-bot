# Roadmap

## Phase 1 — Breakout Scalping V1 foundation (complete)

- Project structure, V1 specification, runner, metrics, and workflow templates
  are in place.

## Evidence collection — current

- **Historical baseline:** Full calendar-year 2025 EURUSD M5 bid data processed;
  results are recorded in
  [the baseline report](../reports/BASELINE_BACKTEST_2025.md).
- **Validation:** A distinct January-October 2026 period was tested with
  unchanged V1 parameters and was negative; details are in
  [the validation report](../validation/2026_histdata_v1/VALIDATION_REPORT.md).
  V1 has not passed validation.
- **Demo:** Start only after data/backtest review and validation; record every
  completed demo trade in the paper-trading log. No demo trades have been
  supplied or counted yet.
- **100-trade gate:** Current demo count is recorded in
  [the demo journal](../paper_trading/DEMO_TRADING_JOURNAL_TEMPLATE.md).
  V2 remains prohibited until baseline metrics exist and at least 100 demo
  trades are completed.
- **Weekly review:** Generate descriptive session, trade, spread, volatility,
  drawdown, and lesson summaries in
  [the weekly review](../reports/weekly/WEEKLY_REVIEW.md).

V1 parameters remain frozen. No optimization or V2 design is allowed before
the evidence gate.

## Version decision record

| Version | Hypothesis | Evidence | Decision |
|---|---|---|---|
| Breakout Scalping V1 | Baseline: enter on a close outside the prior 20-bar range; fixed 10-pip stop and 2R target. | 2025 baseline and 2026 temporal validation are negative; no demo evidence. | Keep frozen; no promotion decision and no V2 proposal. |

## Evidence gates

1. **Backtest:** Record all required metrics and data provenance.
2. **Validation:** Use a distinct period and unchanged parameters.
3. **Demo:** Log every signal, order, execution, cost, and operational issue;
   count only completed demo trades toward the mandatory minimum of 100.
4. **Review:** Compare validation and forward-demo results with pre-declared
   risk and performance criteria.
5. **Decision:** Keep V1 as baseline unless all promotion requirements in the
   [project charter](./PROJECT_CHARTER.md) are met and the 100-demo-trade gate
   is satisfied.
