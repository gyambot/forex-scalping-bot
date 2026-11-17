# Candidate 9: Simulated Lifecycle State Machine

The [implementation](paper_trading/candidate9_lifecycle_simulation.py) is
a persistent **simulation**, not a broker executor. It imports the frozen
candidate signal calculation, risk checker and isolated deal reconciler.
It never connects to MT5 and has no order submission, modification or
position-closing API. It does not use or change the V1 state, logs, metrics
or gate. A synthetic submission response is supplied by the test caller.
The [integrated simulation](paper_trading/candidate9_integrated_simulation.py)
additionally drives the state machine using a concrete in-memory broker,
and does not accept a real broker adapter. It persists intent before a single
simulated submission, checks a second synthetic account snapshot, and
records a separate simulated execution row and validation journal row.
The separate [submission scaffold](paper_trading/candidate9_demo_submission.py)
is inhibited and disarmed; a fake broker fill reaches POSITION_OPEN only
after deal identity, volume, exact entry, position and protection checks.
Its caller-driven polling path checks broker-like snapshots and reconciles
the resulting fake history. It has not been tested with an actual broker
and must not be enabled.

## Valid transitions

| From | To | Condition or meaning |
|---|---|---|
| IDLE | PRECHECK | Simulated study has not expired, hit a limit or been killed. |
| IDLE | SHUTDOWN | Kill switch, expiry, completed count or failure limit. |
| IDLE | MANUAL_REVIEW_REQUIRED | Reserved safety halt. |
| PRECHECK | SIGNAL_DETECTED | Completed weekend bar produces the frozen gap signal. |
| PRECHECK | SHUTDOWN | No signal, missed entry, or 1R loss. |
| PRECHECK | MANUAL_REVIEW_REQUIRED | Unknown health, position/pending order, invalid data or restart. |
| SIGNAL_DETECTED | ORDER_PENDING | Risk and spread checks pass; simulated intent committed. |
| SIGNAL_DETECTED | SHUTDOWN | Spread or extreme-gap filter skips signal. |
| SIGNAL_DETECTED | MANUAL_REVIEW_REQUIRED | Bad quote, risk, magic or restart. |
| ORDER_PENDING | POSITION_OPEN | Synthetic accepted response with positive order/position IDs. |
| ORDER_PENDING | SHUTDOWN | Synthetic rejection; one-attempt latch. |
| ORDER_PENDING | MANUAL_REVIEW_REQUIRED | Unknown/timeout response or restart. No retry. |
| POSITION_OPEN | POSITION_SUPERVISION | Synthetic position and protection verified, or position already closed in the older state-machine-only path. The integrated path requires an observed protected position first. |
| POSITION_OPEN | MANUAL_REVIEW_REQUIRED | Unsafe supervision or restart. |
| POSITION_SUPERVISION | POSITION_CLOSED | Flat synthetic position snapshot; history still required. |
| POSITION_SUPERVISION | MANUAL_REVIEW_REQUIRED | Kill, loss, health, spread, protection mismatch or restart. |
| POSITION_CLOSED | RECONCILED | Synthetic history agrees with stored intent and internal order ID. |
| POSITION_CLOSED | MANUAL_REVIEW_REQUIRED | Reconciliation failure or restart. |
| RECONCILED | SHUTDOWN | Trade recorded and completed count updated atomically; one-trade latch. |
| RECONCILED | MANUAL_REVIEW_REQUIRED | Restart before final shutdown (defensive transition). |

`SHUTDOWN` and `MANUAL_REVIEW_REQUIRED` are terminal. **Every transition
not listed above is invalid** and the transition function raises an error.
Some valid graph edges are defensive; atomic database transactions mean
individual intermediate states may not be externally observable.
Restart from any in-flight state persists manual review. Restart after
shutdown remains shut down. SQLite transactions and an immediate write lock
serialize competing simulated intents. Unknown outcome cannot be retried.

## Boundaries

Supervision only occurs when a caller invokes it; there is no deployed
service. The scaffold has a polling loop and the integrated simulator can
consume a scripted polling sequence;
if that sequence ends before closure, it latches manual review. Snapshot,
account status, positions, price and P&L are caller-supplied,
not broker-verified. Synthetic close is not proof of broker closure.
Reconciliation can use supplied synthetic deals or the read-only
[history adapter](paper_trading/candidate9_mt5_history.py) against an injected
broker-like object. The latter was tested only with a fake; it does not
connect to MT5. The internal order ticket is caller supplied and the trade
record is a SQLite row in the same simulated transaction, not a separately
verified external trade log. Restart fails closed rather than recovering or
managing a live position.

The integrated path compares the lifecycle intent with the separately
persisted simulated execution and validation rows and fake broker deals.
Those rows share the simulation database and are not independent broker
evidence. Completion and journal results commit together; a restart during
an in-flight attempt remains a manual-review event and cannot resubmit.

The one-trade latch stops after the first completion; ten completions are
unreachable in one simulation without a separately designed manual rearm
protocol. The 10-count branch is tested by seeding state, not by placing ten
trades. Similarly, the three-failure check is tested with seeded state;
rejection and ambiguous submission stop the first attempt. No summary at
ten completed trades is implemented. No reset mechanism is provided.
