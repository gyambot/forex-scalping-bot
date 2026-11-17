# Candidate 9: Controlled Demo Validation Plan

## Decision

**SAFEGUARD_FAILURE.** The requested controlled demo mode is not safe for
use or ready for activation. The current deliverable is an isolated
non-submitting safeguard model, not an order executor.

An isolated read-only broker observer and pure deal-evidence reconciliation
helper were added as preliminary building blocks. They have only been tested
with fakes and caller-supplied data and cannot execute, supervise or recover
a trade.
An isolated journal records simulated intent and terminal outcomes and
marks unresolved intents uncertain after restart. It has not been integrated
with actual order submission, broker history or position recovery.
A pure risk checker validates supplied broker constraints and an explicit
cash budget, but has no verified live values or execution authority.
The read-only preflight joins those checks but cannot submit an order; a
passing preflight is not a controlled demo validation.
An isolated position watcher adds mocked checks for a known position and
protection, but has no running loop, trusted live P&L or ability to cancel,
close or repair positions.

The safety review in [Automatic Shutdown Safeguards](AUTOMATIC_SHUTDOWN_SAFEGUARDS.md)
and [test results](SAFEGUARD_TEST_RESULTS.md) separate modeled safeguards
from the missing broker integration. The kill-switch file is present; no
live or demo order was sent, no executor was armed and no broker connection
was made during this work.

## Isolation and protected studies

The model has no code path calling MT5 or writing V1 trade logs, metrics,
reconciliation or gate state. Its tests use temporary SQLite files and
synthetic snapshots. V1, candidate results, existing reconciliation, metrics
and gate logic were not modified. This isolation holds for the delivered
model; a future broker adapter must preserve it and verify output paths
against V1 study files.

## Prerequisites before further authorization

1. Complete and integrate an isolated demo-only broker adapter that verifies
   terminal connection, expected account identity and demo mode, permissions,
   EURUSD availability, fresh executable quotes, and flat positions and
   pending orders. Repeat checks at entry and guard against concurrent
   submissions. An unknown or ambiguous result must never trigger retry.
2. Verify MT5 weekend bar timestamp semantics and historical completeness;
   reject stale Friday references and ambiguous data rather than inferring
   times. Reproduce the frozen five-pip gap rule and log Friday close,
   reopening open, gap direction, signal and timing separately from the V1
   study.
3. Implement broker-compatible volume sizing and a clearly defined
   account-currency 1R loss budget with costs and floating exposure, approved
   before any execution. A stop does not guarantee a maximum loss during a
   gap. Verify broker stops, volume/tick constraints, attached protections
   and actual fill semantics; no protection may be assumed from a mock.
4. Persist the submission intent before sending, protect against duplicate
   orders and process crashes, and reconcile every deal and open position
   against durable internal records. Rejection, ambiguous submission,
   failed reconciliation or lost protection must block new entries and
   require review. Define safe position-management behavior separately:
   stopping new entries alone does not close an existing broker position.
5. Implement isolated, durable logging for gap, spread, signal, fills,
   P&L, slippage, exit and shutdown reason; verify complete trade history
   and generate a ten-trade report. Resolve the one-trade-latch versus
   ten-trade requirement without resetting cumulative safety state.
6. Exercise connected safety paths with extensive mocks, process-restart
   and crash tests, concurrency tests and controlled broker read-only
   verification. Tests must cover kill switch during entry and active
   exposure, daily-loss calculation, partial fills, clock/quote failures,
   history failure, and storage failure. Never use a live account.
7. Collect weekend observations and broker spread evidence using the
   [manual validation plan](WEEKEND_GAP_FADE_VALIDATION_PLAN.md). Obtain
   explicit separate owner authorization for any future demo order; no
   ten-weekend observation or mock test by itself proves an edge.

## Decision boundary

Only a fully implemented, independently verified and explicitly authorized
demo-only implementation can advance. Current synthetic tests do not meet
that condition; the project must not start automated execution.

**SAFEGUARD_FAILURE**
