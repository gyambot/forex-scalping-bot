# Validation Trade Isolation

> Implementation update: single-trade validation now uses the isolated log,
> metrics and simulated gate described below, with a persistent classification.
> Fake-adapter tests exercise isolation and recovery. The execution decision
> is tracked separately in [Blocker Report](./BLOCKER_REPORT.md); this document
> retains its original design assessment for history.

## Decision

**VALIDATION_TRADE_ISOLATION_BLOCKED**

The design below is proposed, not implemented or tested. The existing
single-trade mode writes a completed validation trade to the normal demo
log and refreshes the normal metrics and gate. A compliant trade can
therefore advance the study. Do not execute a validation trade until the
isolation changes and acceptance tests below pass. This assessment does not
authorize or place an order.

## 1. Recommended design

Use a **separate validation trade log**, with a durable validation
classification in the existing one-trade state. The operational boundary
is:

| Purpose | Completed trade destination | Metrics and gate destination |
|---|---|---|
| Formal study | `DEMO_TRADING_LOG.csv` | Existing `DEMO_METRICS.json` and `DEMO_GATE_STATUS.md` |
| Engineering validation | `VALIDATION_TRADING_LOG.csv` | Separate, clearly labeled validation metrics and simulated gate evidence |

Keep the existing trade CSV schema and the actual `rule_compliant` result.
Store the classification, run identifier and trade/order/position references
in the persisted validation state and the validation report. The validation
log itself is the durable classification for captured records; do not rely
only on a note, filename supplied by an operator, or a falsified compliance
flag. Preserve the existing shared execution log, shared state and shared
lock, so isolation does not bypass the one-attempt latch or hide activity.

Compared with adding a flag to the normal CSV, this avoids a schema migration
and changes to every metric and gate consumer. Merely marking a compliant
trade noncompliant would misrepresent V1 fidelity; filtering only the gate
would still contaminate profit factor and expectancy. A separate log alone
is insufficient unless routing and recovery fail closed and the standard
reporting paths are never used for validation.

## 2. Required code changes

1. In `demo_executor.py`, route single-trade validation explicitly to a
   fixed validation log and isolated output paths. Normal execution keeps its
   existing study paths. Do not rely on the current CLI defaults or on
   callers remembering to pass alternate paths.
2. Persist `engineering_validation` classification and the intended
   destination in the shared latch **before** an entry attempt. On every
   capture or recovery, derive and verify the destination against that
   persisted classification. Missing, mismatched, invalid or legacy
   ambiguous classification must stop for manual reconciliation, not fall
   back to the study. Reject output paths that resolve to study files.
3. Before arming, validate the separate output directory, existing
   validation log schema, and writable paths. Keep the existing account,
   flat-account, pending-order, broker-time, single-attempt, lock and
   reconciliation safeguards. A failed startup must not submit an order.
4. On closure, use the same reconciliation and trade validation functions,
   append idempotently to the validation log, and refresh only isolated
   validation outputs. Persist the outcome and references in the latch.
   Preserve the existing stop-on-uncertainty behavior, including after a
   crash between capture and report updates.
5. Update the executor specification, operator workflow, and gate policy to
   distinguish engineering records from the formal study. Ensure manual
   import/recovery procedures cannot silently reclassify the same broker
   position as a study trade: check validation and study records for matching
   trade ID and broker position/order references, and require explicit
   investigation on conflict. No manual copying or reclassification is
   authorized by this design.

This is a routing and provenance change, not a change to V1. Current
`DemoExecutor` accepts alternate paths internally, but the CLI currently
constructs it with study defaults. Merely passing different paths to one
invocation is not a sufficient persistent, restart-safe implementation.

## 3. Impact on existing metrics

The normal metrics generator and review read the study log by default.
They must continue to consume only that log; a validation trade must not
change its trade count, profit factor, expectancy, or any other study
metric. Preserve baseline files and compare their contents and computed
values before and after the test.

Run the existing metrics calculation on the isolated log and save its result
as **engineering-only** evidence. The calculator filters by
`rule_compliant`: a late or otherwise noncompliant validation trade may
produce zero eligible observations, so verify its raw record and the
calculator's exclusion output as well as the calculated result. One trade
is not a profitability assessment. Do not overwrite or use the isolated
metrics as study performance.

## 4. Impact on gate logic

The formal gate continues to count eligible records from the study log only;
neither its count nor its eligibility status changes for validation.
Exercise the same counting logic against the isolated log and label the
result **simulated validation gate**, not study progress. A compliant
record can count in this simulated check, while a noncompliant record does
not. Never call the current gate-refresh routine with the formal gate path
for an engineering trade.

The existing [gate policy](./DEMO_GATE_STATUS.md) describes qualifying demo
positions generally; update it to make this prospective exclusion explicit.
The [charter](../docs/PROJECT_CHARTER.md) still requires at least 100
completed demo trades for V2 review: excluding an engineering trade does not
reduce that threshold. The earlier
[controlled plan](./CONTROLLED_DEMO_VALIDATION_PLAN.md) describes the old
possibility of counting this trade; its metrics section must be superseded
when the isolation is implemented.

## 5. Impact on reconciliation

Keep `build_trade_record` and its provenance, direction, volume, timestamps,
cost conversion and V1 compliance calculation unchanged. Route its validated
record to the isolated log only after the position is fully closed. Persist
the true compliance result even though it has no study eligibility.
Continue to compare broker entry and exit deals, costs, tick metadata and
statement independently; an isolated record is not proof that conversion or
broker evidence is correct. If reconciliation or output persistence fails,
stop and retain the state and broker evidence for manual recovery without
resubmission or an automatic study-log fallback.

## 6. Auditability and acceptance tests

Retain the shared execution events, latch, broker order/deal/position IDs,
entry and exit details, costs, actual compliance, isolated CSV and isolated
reports. Associate them with the validation run and record why it is excluded
from the study. Check for cross-log duplicates using broker references as well
as trade IDs; a same-ID or same-position conflict must fail closed rather
than silently append or overwrite. Capture before/after hashes of the three
formal outputs and independent computed metrics and gate status.

Before any real run, fake-broker tests must demonstrate:

- A compliant and a noncompliant full lifecycle each write exactly one
  accurate isolated record and leave formal trade log, all study metrics
  including profit factor and expectancy, and gate progress unchanged.
- Validation metrics and simulated gate use only the isolated record and
  correctly report its eligibility; study-mode behavior remains unchanged.
- A rejected, ambiguous, disconnected or failed attempt cannot submit
  again; latch and shared lock remain effective across restart and normal
  mode cannot bypass them.
- Missing, corrupt or inconsistent classification, aliased output paths,
  invalid output schemas, conflicting broker references, and write failures
  stop without fallback to study files.
- Interruption after trade append but before reports/state completion is
  recoverable without duplicate records, false completion or another order.
  Recovery preserves validation classification and reruns the isolated
  reporting steps only.

After implementation and tests, repeat the real read-only preflight and
independently verify flat account, no pending orders, fresh quote, current
offset, operator attendance and the recovery plan immediately before any
separately authorized execution. A successful fake test or design review
does not establish real broker execution or reconciliation.
