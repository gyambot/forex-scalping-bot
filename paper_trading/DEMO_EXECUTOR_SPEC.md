# Demo Executor Specification

## Status and boundaries

`demo_executor.py` is an explicitly armed, demo-only order sender for frozen
Breakout Scalping V1. It uses `live_signal_engine.evaluate_v1_signal()` and
the existing completed-bar feed. It does not change V1 price logic, thresholds,
stops, targets, add filters, or submit orders on import. The module is not
enabled by default.

Starting it requires:

```powershell
python -m paper_trading.demo_executor --arm-demo-execution
```

The read-only startup preflight can be run without arming execution:

```powershell
python -m paper_trading.demo_executor --verify-only --verify-volume 0.01
```

Verification mode is mutually exclusive with the execution arm flag. It
connects and inspects account, symbol, permissions, timestamps, state, and
reporting readiness, but never sends or modifies broker orders. Results are
written to `DEMO_EXECUTOR_INTEGRATION_RESULT.md`.

The separate `--single-trade-validation` mode permits at most one entry
attempt of `0.01` lots. It persists a validation latch before submitting,
disarms new entries on the first attempt, and monitors a confirmed position
until closure and reconciliation. Rejection, ambiguous submission, disconnect,
an unexpected open position while awaiting a signal, or reconciliation error
stops the run. The state and account must be
reconciled before any restart; neither normal execution nor validation mode
will bypass the persisted latch. The mode holds the executor lock throughout
the run and writes `SINGLE_TRADE_VALIDATION_RESULT.md` on exit.

Run only in an explicitly authorized, attended demo session. This mode does
not guarantee execution at the next-bar open; see
[Blocker Report](./BLOCKER_REPORT.md) before arming. A validation submission
decision already later than the planned open is logged as missed and is not
sent. This check cannot guarantee an on-time broker fill. Stopping it does not close an
open position. The result remains failed pending independent review of the
actual broker costs and reconciliation.

The arm flag is not an account-safety override. Every poll still checks the
connected account and the exact `ICMarketsSC-Demo` server. Live, unknown, or
mismatched account states fail closed, with no override path.

## Preconditions

- Configure `MT5_DEMO_VOLUME` explicitly in the process environment or local
  `paper_trading/.env`. No broker lot size is inferred from V1's
  “one normalized unit.” Volume must satisfy MT5 symbol minimum, maximum, and
  step constraints.
- Configure and verify the existing broker-time offset before starting.
- The MT5 terminal must be connected and its account and expert trade
  permissions must be enabled by the operator. The code never changes those
  permissions.
- EURUSD must be visible and allow new market orders.
- The demo account must not have an unresolved executor state. An ambiguous
  prior submission blocks startup and requires reconciliation.
- Only one executor process may operate on the default state file; a
  Windows byte-range lock protects each polling/submission cycle.

The executor uses one market DEAL request per signal, with a broker-supported
FOK or IOC fill mode. It does not submit limit or stop entry orders. No
automatic retry is issued after an uncertain order result.

## Signal and entry sequence

1. Validate terminal connection, demo account, exact server, trade
   permissions, and EURUSD availability.
2. Read the latest 21 completed M5 bars and call the shared V1 signal engine.
3. Ignore `NO SIGNAL`. Suppress any signal bar already recorded as processed.
4. Compute the planned entry time as the completed breakout-bar timestamp plus
   five minutes.
5. Require the current MT5 M5 bar to be the planned next bar. If that entry
   bar has ended or the current bar timestamp does not match, log the signal
   as missed; do not enter late.
6. If any account position is already open, log and ignore a new signal.
   The executor will not create a second position.
7. Persist a submission-in-progress state before calling MT5 once. If the
   response cannot be classified, stop and retain the state for reconciliation.
8. For LONG, submit BUY; for SHORT, submit SELL. The initial request includes
   the V1 stop and target. After the fill, verify them against the actual fill
   and issue one protective SL/TP adjustment if needed; failure to confirm
   both levels stops the executor.

The executor acts as soon as the completed bar is available during the
planned next M5 bar. Poll interval defaults to 100 ms. Neither polling nor a
market order can guarantee a fill at the exact bar-open instant or price.
`fill_delay_ms` and actual fill price are recorded; a fill that does not meet
the frozen entry assumptions is marked noncompliant and does not advance the
gate.

## Position and recovery behavior

- At most one account position is allowed while the executor manages a V1
  position. If a separate position is open, new V1 signals are ignored.
- The executor never scales, averages, adds, trails, or sends a discretionary
  close. It waits for the broker-attached stop or target to flatten the
  position.
- A partial broker close is not treated as a completed position. Deal volumes
  must reconcile to a fully closed position before capture.
- Persistent `EXECUTOR_STATE.json` records a pending or open position. A
  `submitting` state after a crash is ambiguous and blocks any retry.
- Disconnection, missing account/position state, unknown order result,
  unconfirmed protection, invalid deal history, or unreconciled costs stops
  new execution and requires operator reconciliation.
- While a position is open, each poll verifies the persisted stop and target
  are still attached. Any change stops execution for reconciliation.

## Event and trade recording

`execution_logging.py` appends `EXECUTION_LOG.csv` events for detection,
submission, fill, stop/target confirmation, rejection, missed/ignored
signals, closure, and reconciliation errors. Each applicable event stores
planned entry time, submission time, fill time, and fill delay in milliseconds.

When a position is flat, `execution_reconciliation.py` aggregates broker
history, verifies direction and full entry/exit volume, derives weighted
prices, converts recorded account-currency P&L/costs to pips using the
broker-reported tick value/size, and creates the existing trade schema.
Entry deals must match the executor's magic number, order ticket, position,
symbol, and configured volume; unrelated or merged netting-account activity
fails reconciliation.
`manual_trade_capture.append_completed_trade()` performs the existing
validation and duplicate-ID check. Then the executor regenerates
`DEMO_METRICS.json` and updates the count/reason in `DEMO_GATE_STATUS.md`.

Single-trade engineering validation instead uses
`VALIDATION_TRADING_LOG.csv`, `VALIDATION_METRICS.json` and
`VALIDATION_GATE_SIMULATION.json`. The gate simulation is not study progress.
The existing state and lock are shared; a persistent classification binds
the validation state to those destinations. Normal study output is not
refreshed for this trade. Cross-log conflicts require reconciliation.
The read-only `--verify-validation` checks the validation startup, and
`--recover-validation` can reconcile a known, already closed validation
position without placing or modifying orders. It cannot resolve an ambiguous
submission or an open position.

The trade CSV schema is not expanded. Planned time, submission time, fill
time, and fill delay remain auditable in `EXECUTION_LOG.csv` and in the trade
notes; `entry_time_broker` remains the actual first fill time. Broker deal
history remains the reconciliation source of truth.

## Tests and operational limitations

Tests use a fake MT5 module only. They do not connect to MT5 or place any order.
The broker's real tick-value conversion, fill mode, order result codes,
stop/target acceptance, history completeness, and response/position timing
must be verified in an explicitly authorized demo integration session before
counting any trade.
