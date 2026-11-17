# Broker-Time Normalization Assessment

## Decision

**BROKER_TIME_ACCEPTABLE**

The prior UTC-required assessment described the pre-migration code. The
project now adopts an explicit-offset broker-time contract for MT5 live bars,
signal observations, trade records, and demo metrics. See
[BROKER_TIME_CONTRACT.md](./BROKER_TIME_CONTRACT.md) for active behavior. The
remaining sections preserve the pre-migration inventory for audit.

The historical observations and remaining configuration risks are recorded
in [BROKER_TIME_MIGRATION_REPORT.md](./BROKER_TIME_MIGRATION_REPORT.md). No
V1 price rule changes.

## Pre-migration UTC assumptions and affected modules

| Component | Actual implementation | Consequence for broker-time-only data |
|---|---|---|
| `mt5_connector.py` | Converts tick epochs to UTC and computes quote age against `datetime.now(timezone.utc)`. `verify_market_status()` requires a nonnegative age within the freshness limit. | If an API epoch is a broker wall clock represented as a UTC-like epoch, its age against real UTC is about -2 hours and the freshness check rejects it. A broker-time label cannot be substituted without changing the clock comparison semantics. |
| `mt5_price_feed.py` | Converts rate epochs with `datetime.fromtimestamp(..., timezone.utc)`, emits `Z`, and requires M5-boundary alignment. Tick age is also computed against the UTC system clock. | It currently exposes an explicitly UTC-shaped timestamp, not a broker-time value. The repeated offset means this label is unverified; no broker offset is applied. |
| `live_signal_engine.py` | Parses timestamps and rejects any whose UTC offset is not zero; requires M5 boundaries and strictly increasing bars. | Broker timestamps carrying a nonzero offset are rejected. Removing that guard alone would make validation accept values under a different meaning than the current contract. |
| `signal_observer.py` | Writes observation time from the UTC system clock, parses both observation and bar timestamps as UTC, and flags a discrepancy between observation time and expected bar close above 120 seconds. It deduplicates on the stored bar timestamp. | A broker-time bar label compared with the UTC observation clock will continue to appear anomalous. Deduplication also depends on stable, unique labels; repeated local times at DST fall-back need special handling. |
| `scripts/backtest.py` | Requires timezone-aware UTC CSV timestamps on M5 boundaries. It uses bar sequence for the breakout and position simulation, but labels outputs `_utc`; `trades_per_day` groups by the UTC calendar date. | A non-UTC timestamp is rejected. If a fixed offset were merely applied to all labels, raw signals, fills, and P&L would be unchanged, but UTC-day grouping and reported timestamps could change. |
| `demo_trade_utils.py` / `manual_trade_capture.py` | Trade fields are explicitly named `_utc`; parser requires offset zero. It checks signal close equals signal-bar-open plus five minutes and calculates elapsed hold time from entry/exit timestamps. | Broker-time rows are rejected by the existing recorder. A wall-clock difference across DST could misstate elapsed hold minutes unless actual elapsed-time semantics are separately defined. |
| `generate_demo_metrics.py` | Parses UTC exit times to sort trades and reports a `reporting_period_utc`. P&L metrics are then calculated in exit order. | A consistent, monotonic constant shift would preserve order and P&L statistics, but broker-local dates/labels could change reporting periods; DST ambiguity can break ordering and elapsed-time correctness upstream. |

These are source-level behaviors. The timestamp evidence reports document
approximately +2-hour API-vs-UTC observations, but do not include a verified
chart screenshot and API record for the same bar. The reports therefore do
not prove that the MT5 chart, API, and internal signal timestamps are
identical broker-time labels.

## What is and is not time-dependent in V1

- **Breakout detection:** `breakout_signal_at()` in `scripts/backtest.py`
  compares the close to the high/low of the preceding 20 bars. It reads no
  timestamp. With the same OHLC values in the same completed-bar order, a
  uniform timestamp shift does not change LONG/SHORT/NO SIGNAL.
- **Completed-bar sequencing:** The predicate needs the correct 20 preceding
  completed bars and the signal bar's close. Absolute UTC is not part of that
  arithmetic. Live use additionally needs to know that the bar is complete
  and that the next M5 entry opportunity has not been missed.
- **Stop and target:** V1's 10-pip stop and 20-pip target are price distances
  from actual entry, so timestamp labels do not change them for an identical
  fill. If a timing error results in a different entry bar or price, the
  absolute stop/target prices and resulting trade can differ.
- **Trade order and metrics:** A constant offset that preserves chronological
  order leaves P&L, R, win/loss classification, and closed-trade drawdown
  unchanged. `hold_minutes` is based on elapsed entry-to-exit time; it remains
  unchanged only if the timestamp representation preserves actual elapsed
  time. Backtest `trades_per_day` groups bars by calendar date, so shifting
  from UTC to broker time can change day boundaries/counts. Demo metrics sort
  exits and label the reporting period in UTC.
- **DST and local wall time:** GMT+2/GMT+3 server clocks are not one constant
  offset across the year. A naive broker-local series can contain skipped or
  repeated wall-clock labels at seasonal transitions. That conflicts with
  strict uniqueness, ordering, exact five-minute intervals, and elapsed-time
  calculations unless the transition semantics are explicitly handled.

## Risks identified before migration

1. **The API meaning is unsettled.** The connector converts epochs to UTC,
   while runtime observations are roughly two hours ahead of the actual UTC
   clock. Existing reports describe broker time as plausible, not proven.
   The requested same-bar chart/API evidence and API-specific timestamp
   semantics remain outstanding.
2. **There is no broker-time clock contract in the code.** The observer and
   connector compare API timestamps against a real UTC system clock. Merely
   renaming fields or removing UTC validation would not make those comparisons
   correct.
3. **The persisted trade schema is UTC-specific.** Capture fields, validation,
   reconciliation, gate inputs, and metric outputs use explicit UTC fields
   and UTC ordering. Changing them requires a coordinated schema migration;
   current validators reject broker-local timestamps.
4. **Seasonal changes require more than a constant two-hour relabeling.**
   A broker-local representation must explain DST gaps/folds and preserve
   actual elapsed minutes. No verified date-aware conversion or transition
   evidence is present.
5. **Current evidence does not justify changing the operational gate.**
   The live observer already detects that API-bar time and UTC observation
   time do not align. Treating the observed offset as acceptable risk would
   bypass a check whose purpose is to ensure completed-bar and next-bar
   timing.

## Migration requirements identified by the prior assessment

This is not a recommendation to implement a broker-time-only system now. A
future proposal would first need:

1. Authoritative evidence of the `ICMarketsSC-Demo` chart/server timezone and
   the MT5 Python API's raw bar/tick timestamp semantics.
2. A same-completed-bar chart/API comparison with matching OHLC and
   contemporaneous Windows local and UTC clock values, plus verification of
   both GMT+2 and GMT+3 regimes.
3. A documented canonical representation, including an explicit timezone
   identifier, DST gap/fold policy, and rules for bar labels versus bar-close
   instants. Do not use an unqualified local datetime or append `Z` to
   broker-local wall time.
4. A coordinated contract change across MT5 freshness checks, the price
   feed, live signal engine, observer, backtest input/output, trade-import
   schema and validator, metrics ordering/reporting, templates, and tests.
5. A schema migration that preserves original raw broker evidence and avoids
   silently reinterpreting existing `_utc` records. Recompute and compare
   outputs from identical OHLC and trade inputs, including cases around
   midnight and both DST transitions.
6. Revalidation that completed-bar selection, next-M5 opportunity,
   deduplication, chronological ordering, actual hold duration, and all
   documented metrics retain their intended meaning.

Those requirements informed the implementation but do not prove that a
single fixed offset remains valid across broker seasonal clock changes. The
active contract retains explicit source offsets and exposes that
configuration risk.

## Migration disposition

The migration has been implemented. `MT5_BROKER_UTC_OFFSET` defaults to
`+02:00` based on the observed current server offset and must be updated to
`+03:00` when the broker changes its server clock. Raw MT5 bar clock fields
are preserved; trade records and metrics store explicit-offset broker times.
See the migration report for tests and limitations. No V1 rules were changed.

BROKER_TIME_ACCEPTABLE
