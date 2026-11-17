# Post-Migration Acceptance — Demo Trade #1

Assessment date: 2026-11-12

## Conclusion

**BLOCKED**

The migration removed the runtime requirement that MT5 timestamps be UTC.
Historical backtest metrics are unchanged, the read-only live observer
produced a correctly shaped broker-offset observation, and the manual capture
pipeline passed an isolated end-to-end check. However, the current live
observation arrived **205.2 seconds after the expected M5 bar close**, beyond
the observer's 120-second tolerance and after the V1 next-bar entry point.
The configured offset also remains manually managed and was not visually
verified against the terminal chart during this acceptance. The project
therefore cannot safely begin collecting Demo Trade #1 yet.

## Previous timestamp blockers

| Previous blocker | Acceptance finding |
|---|---|
| Live and trade validators required UTC/zero offset | **Removed.** Live bars and trade records accept explicit offsets; demo trade columns use `*_broker`. A scan of active runtime code found no UTC-only validation. |
| MT5 API values appeared about two hours ahead of Windows UTC | **No longer a UTC-format blocker.** The active contract preserves the observed MT5 clock fields and tags them with `MT5_BROKER_UTC_OFFSET`; it does not claim that the epoch's global-time semantics were proven. |
| Chart/API same-bar screenshot and exact clock comparison were absent | **Still absent.** This remains a configuration/source-semantics risk. The contract requires the configured offset to match the terminal's displayed broker clock; no visual verification was performed for this acceptance. |
| Seasonal GMT+2/GMT+3 transition | **Partially handled, not automated.** The offset is explicit and configurable, but it must be changed manually when the server clock changes. |
| Observer could confuse UTC observation time with broker bar time | **UTC mismatch removed, live timing still fails.** A real read-only observation was generated using `+02:00` for both clocks, but it was late by 205.2 seconds. |
| Trade timestamps and reporting required UTC | **Removed for the demo workflow.** Capture validates explicit-offset event order and metrics sort using parsed broker-offset timestamps. |

The older [DEMO_EXECUTION_READINESS.md](./DEMO_EXECUTION_READINESS.md)
records the pre-migration UTC-specific conclusion. Its UTC conversion
requirement is superseded by the broker-time contract, but its caution against
acting on unverified or late signal timing remains applicable.

## UTC-only validation audit

No UTC-only timestamp validator was found in the active live signal, observer,
MT5 feed/connector, manual capture, or demo metrics/gate paths. These paths
require explicit offsets and ordering rather than an offset of zero.

UTC references remain in historical-data preparation and the MT5 epoch
rendering primitive. `scripts/prepare_histdata.py` converts its historical
source data to UTC; that is source normalization, not an MT5 live-input
validator. `broker_time.py` uses UTC-rendered epoch fields as an intermediate
to preserve the observed MT5 wall-clock fields, then attaches the configured
offset; it is not requiring the resulting timestamp to be UTC.

## Historical metrics

The 2025 dataset was rerun through the current backtest runner:

- Input bars: **73,683**
- Current performance metrics versus
  `backtests/2025_histdata_v1/metrics.json`: **exactly equal**
- Comparison result: `performance_equal=True`

No V1 price rule or parameter was changed for this acceptance.

## Live observation check

A one-poll read-only run of `signal_observer.observe()` completed against the
configured MT5 terminal, wrote one observation to a temporary file with the
expected CSV schema, emitted an explicit `+02:00` bar timestamp, generated its
report, and shut down the connection. No account identifiers or quotes are
included here.

Observed timing:

| Event | Broker-time reading |
|---|---|
| Completed bar open | `2026-11-12T07:25:00+02:00` |
| Expected bar close | `2026-11-12T07:30:00+02:00` |
| Observer timestamp | `2026-11-12T07:33:25.153123+02:00` |
| Delay after expected close | **205.2 seconds** |
| Observer tolerance | **120 seconds** |

The observer reported a timing anomaly. V1 requires entry at the next M5 bar
open (`07:30:00+02:00` here), which had already passed when this observation
was recorded. The observer remains operational as a logger, but this sample
is not timely enough to establish a valid Demo Trade #1 opportunity.

## Manual trade-capture workflow

The workflow was exercised without touching the operational log:

- A completed explicit-offset trade record was appended to a temporary CSV.
- The record passed schema, timestamp, price, completion, and uniqueness
  validation.
- Demo metrics counted the isolated eligible fixture as one trade.
- The isolated gate correctly reported `1/100 BLOCKED`.

This verifies the software path only; it is not evidence of an actual trade.
The operational gate remains **0 / 100**. No trade or order was submitted.

## Test evidence

- `python -m unittest discover -s tests` — **21 passed**
- `python -m unittest discover -s paper_trading\tests` — **33 passed**

## Acceptance disposition

The broker-time migration removed UTC identity as a software prerequisite,
but it did not establish timely next-bar observation. The current live
observation exceeded the timing tolerance and missed the V1 entry point, while
the configured offset has not been visually checked against the terminal
clock. Do not count this observation as a trade signal eligible for
execution; wait until a fresh observation is timely and the configured offset
is confirmed against the displayed broker clock. Follow the
[demo execution checklist](./DEMO_EXECUTION_CHECKLIST.md) before any
human-operated demo activity.

BLOCKED
