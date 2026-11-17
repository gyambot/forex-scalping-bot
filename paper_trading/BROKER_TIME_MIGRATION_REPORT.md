# Broker-Time Contract Migration Report

## Decision

**BROKER_TIME_CONTRACT_IMPLEMENTED**

The active live and demo-trade interfaces now accept and emit explicit-offset
broker-time timestamps without requiring UTC identity or UTC conversion.
MT5's observed clock fields are preserved and tagged with the configured
offset. The migration does not claim that the API epoch semantics have been
independently proven.

## Implementation summary

- Added `paper_trading/broker_time.py` with explicit-offset parsing,
  configured broker-offset handling, and MT5 epoch-to-observed-clock labeling.
- Updated `paper_trading/mt5_connector.py`,
  `paper_trading/mt5_price_feed.py`, and
  `paper_trading/mt5_healthcheck.py` to use the configured broker offset for
  quote freshness and feed/healthcheck timestamps.
- Updated `paper_trading/live_signal_engine.py` and
  `paper_trading/signal_observer.py` to accept, compare, and log explicit
  broker-offset times.
- Updated `paper_trading/demo_trade_utils.py`,
  `paper_trading/generate_demo_metrics.py`,
  `paper_trading/generate_demo_review.py`, trade templates, and demo CSV
  headers to use broker-time fields and ordering.
- Updated `scripts/backtest.py` to accept explicit source offsets and retain
  the input offset in output. Historical backtest input remains in its source
  timezone; no historical price or strategy rule was changed.
- Added `MT5_BROKER_UTC_OFFSET` to `.env.template`, defaulting to `+02:00`.
  The operator must update it to match the server clock when that clock
  changes; there is no automatic seasonal-offset detection.
- Updated the V1 timestamp data contract, capture/metrics specifications,
  demo workflow and checklist, reconciliation/validation guidance, README,
  integration guidance, and the previous timestamp/readiness assessments'
  status notes. Added `BROKER_TIME_CONTRACT.md`.
- Migrated the two existing observation-log labels from their former `Z`
  representation to explicit `+02:00` labels. This reflects the contract
  migration and observed offset; it is not independent verification of those
  historical labels. The operational demo trade log had no trade rows.

## Removed runtime UTC requirements

- Live signal validation no longer requires a zero UTC offset.
- MT5 quote freshness no longer compares broker-labeled tick fields directly
  against a UTC clock.
- Observer timestamps and bar comparisons use the same configured broker
  offset.
- Manual demo trade validation requires timezone awareness and event ordering,
  not UTC identity. Trade columns are explicitly named `*_broker`.
- Demo metric and weekly-review ordering/reporting use broker-time fields.
- The historical HistData preparation script still converts its source data
  to UTC. This is a historical input preparation convention, not a runtime
  requirement for MT5 live data.

## Regression evidence

- `python -m unittest discover -s tests` — **21 tests passed**.
- `python -m unittest discover -s paper_trading\tests` — **33 tests passed**.
  Together, the two complete test directories ran **54 tests successfully**.
- Added regression cases verify unchanged V1 entry/stop/target/P&L results
  when the same bars are represented as UTC or `+02:00`, and preserve bar
  ordering, entry/exit labels, and elapsed hold time across an explicit
  `+02:00` to `+03:00` offset transition.
- Pylance syntax checks reported no syntax errors in the modified observer
  and regression-test files.
- Re-ran the 2025 historical dataset through the current backtest runner:
  **73,683 bars**; the complete performance metrics object exactly equals the
  frozen baseline in `backtests/2025_histdata_v1/metrics.json` (`True`).

## Records and generated outputs

- `paper_trading/DEMO_TRADING_LOG.csv`,
  `paper_trading/DEMO_TRADING_LOG_SEED.csv`, and
  `paper_trading/trade_import_template.csv` use the broker-time schema.
- `paper_trading/SIGNAL_OBSERVATION_LOG.csv` uses explicit `+02:00` labels.
- `paper_trading/SIGNAL_OBSERVATION_REPORT.md`,
  `paper_trading/DEMO_METRICS.json`, and
  `paper_trading/DEMO_WEEKLY_REVIEW.md` are regenerated from the migrated
  schemas.
- `paper_trading/MT5_HEALTHCHECK.json` is retained as a historical snapshot
  from before this contract migration. Its `_utc` keys are not current
  runtime output and were not rewritten as if a fresh terminal check had
  occurred.
- Demo collection remains **0 / 100**. No demo trade was created, and no
  order was submitted.

## Remaining risks and limitations

1. `MT5_BROKER_UTC_OFFSET` is a manually maintained fixed offset. If it does
   not match the terminal's current seasonal server clock, labels and quote
   freshness checks can be wrong.
2. The prior chart/API same-bar visual comparison was not captured.
   `epoch_to_broker_time()` intentionally preserves UTC-rendered epoch fields
   and attaches the configured offset based on the observed clock convention;
   the migration does not independently prove the API's epoch semantics.
3. A timestamp change does not make the observer fail closed or confirm
   next-M5-bar human entry. Existing demo-readiness restrictions remain in
   force; this report is not authorization to trade.
4. Historical timestamp/readiness documents retain their original findings
   as evidence and are marked as pre-migration. The broker-time contract and
   this report define current software behavior.
5. Validation so far used unit tests and the local historical dataset. No
   live MT5 terminal verification was performed as part of this migration.

## Strategy invariants

No V1 breakout rule, lookback, stop distance, target multiple, position
constraint, or strategy filter was changed. No V2 was created. Historical
performance metrics are identical to the frozen baseline.
