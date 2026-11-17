# Candidate 9 Lifecycle Test Results

## Commands

| Command | Result |
|---|---|
| `python -m unittest tests.test_candidate9_integrated_simulation tests.test_candidate9_lifecycle_simulation` | 21 tests passed |
| `python -m unittest tests.test_candidate9_order_preview tests.test_candidate9_position_watch tests.test_candidate9_integrated_simulation` | 22 tests passed |
| `python -m unittest tests.test_candidate9_demo_submission tests.test_candidate9_order_preview tests.test_candidate9_integrated_simulation` | 20 tests passed |
| `python -m unittest tests.test_candidate9_demo_submission tests.test_candidate9_position_watch tests.test_candidate9_mt5_history` | 21 tests passed |
| `python -m unittest discover -s tests` | 121 tests passed |
| `python -m unittest discover -s paper_trading\tests` | 54 tests passed |

## Evidence

The simulated happy path persists signal, intent, synthetic acceptance,
position supervision, closure, reconciled history, trade row and shutdown.
Other tests exercise rejection, unknown and timeout results, restart in
pending/open/closed phases and after completion, missing stop and target,
kill switch, reconciliation mismatch, expiry, seeded ten-trade/failure
limits, unexpected startup position/order, spread and daily-loss filters,
invalid operations and two concurrent attempts. The concurrent simulation
commits only one pending intent. No MT5 connection or order was made.

These are simulations using temporary databases and caller-supplied broker
facts. The submitted result is an input to the simulator, **not an
`order_send` call**. The `POSITION_CLOSED` restart test represents a crash
before reconciliation; the normal reconciliation and shutdown commit in
one SQLite transaction, so the externally visible `RECONCILED` crash state
is not exercised separately. The read-only history adapter and its
integration with the simulator were tested with fake broker data, including
closure, identity, costs, early or future timestamps, incomplete fills,
missing history and persisted manual-review failure. No actual broker history
or independent log round-trip is tested. Position monitoring is caller-driven,
not continuous.

The integrated simulation now exercises a single in-memory submission after
durable intent, a second synthetic pre-submission health check, protected
position observation, scripted supervision, independent simulated execution
and validation rows, fake deal reconciliation, and atomic completion. Tests
also cover concurrent attempts, synthetic rejection/unknown/timeout/exception,
changed account conditions, missing protection, kill switch, restart, expiry,
seeded trade limit, mismatched simulated records and exhausted supervision.
The independent rows share one SQLite database; they do not prove an
independently obtained broker record. A scripted poll sequence is not a
continuously running broker monitor.

The order-preview tests use an in-memory MT5-like fake whose `order_send`
raises if called. They cover long and short request prices and protection,
account and risk checks, high spread, unavailable filling mode, explicit
rejections and ambiguous partial or missing results. They do not prove
broker submission, fill protection or authorization. The read-only
position-watch tests also verify a high-spread shutdown.

The hard-inhibited submission scaffold was exercised with fake broker objects
after overriding the inhibit in test memory. Cases cover project kill switch,
disarmed default, daily realized-loss history, broker cash-risk check, broker
constraint mismatch, rejection, partial or unknown result, exception,
concurrency, verified fill and protection, manual-review outcomes for
partial fills and slippage, missing SL/TP, kill switch, floating daily loss,
stale closure, polling and reconciliation. The fake's `order_send` method
records calls; no MT5 API was called. The scaffold has not supervised or
reconciled an actual accepted order and must not be enabled.

See [the state machine](CANDIDATE_9_STATE_MACHINE.md) for all transitions
and [execution readiness](CANDIDATE_9_EXECUTION_READINESS.md) for the
remaining blocking gaps.
