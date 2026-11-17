# Candidate 9: Automatic Shutdown Safeguards

## Status

**SAFEGUARD_FAILURE.** The isolated
[safeguard model](paper_trading/candidate9_safeguard_model.py) is a test
foundation only. It has no signal feed, MT5 adapter, order submission,
position supervision, or execution interface. `MODEL_CHECKS_PASSED_NO_EXECUTION`
is not permission to trade. No automatic shutdown protection has been
connected to a broker.

The separate [read-only broker observer](paper_trading/candidate9_broker_observation.py)
can inspect an injected already-connected MT5-like module and derive a
weekend signal from supplied completed bars. It does not initialize MT5,
prove timestamp semantics or submit orders. A separate
[deal evidence reconciler](paper_trading/candidate9_reconciliation.py)
validates supplied records and costs but does not retrieve broker history,
confirm closure itself or write a trade log.
The [isolated journal](paper_trading/candidate9_validation_journal.py) adds
durable intent, completion and uncertain-restart records; it is likewise
not wired to broker execution.
The [pure risk checker](paper_trading/candidate9_risk.py) checks explicit
volume and tick constraints and a supplied stop-loss-and-cost estimate
against a 1R cash budget. It does not retrieve or verify broker values, size
a position automatically, or guarantee a maximum realized loss.

The [read-only preflight](paper_trading/candidate9_readiness_preflight.py)
combines the observer, signal derivation, model, journal and risk checks in
one testable path. It uses caller-supplied inputs, has no order interface,
and does not record an entry intent. Its successful result is explicitly
`READ_ONLY_CHECKS_PASSED_NO_EXECUTION`; it is not an arm or trade signal.
The helper does not establish a process-wide lock around any future order
call or independently measure the daily account loss.

The [position watcher](paper_trading/candidate9_position_watch.py) checks a
caller-supplied expected active position, demo account, protective prices,
quote freshness, kill switch and modeled daily P&L; unsafe results latch the
isolated journal. It is not scheduled or connected to an executor and
cannot cancel or close exposure. No automatic monitoring is running.

The requested [kill-switch file](paper_trading/KILL_SWITCH.txt) has been
created and remains present. It does not control the pre-existing V1
executor or automatically cancel or close broker exposure. Removing it does
not arm or authorize anything.

| Safeguard | Model behavior | Broker-integrated status |
|---|---|---|
| One-trade latch | SQLite shutdown on modeled completion, rejection, or reconciliation failure; persists on restart. | Not wired to actual broker outcomes. |
| Daily loss | Synthetic net P&L at or below -1R shuts down. | No verified account-currency R, realized/unrealized or cost calculation. |
| Failure limit | Third modeled execution exception shuts down. Rejection or reconciliation failure shuts down immediately. | No real execution exception path. |
| Spread | More than 3 pips skips modeled signal. | No verified live bid/ask or freshness integration. |
| Extreme gap | Absolute gap over 20 pips skips modeled signal. | No candidate live signal wiring. |
| Positions and orders | Any modeled open position or pending order shuts down. | No broker query or race-free enforcement. |
| Broker health | Synthetic failures or unknown values fail closed. | No actual MT5 account/permission/quote verification. |
| Kill switch | Present file triggers persistent modeled shutdown. | No active-order/position supervision. |
| Ten trades | At 10 modeled completions the model shuts down. | Automatic summary/report not implemented. |
| Expiry | 90 days maximum from model creation, or shorter; persistent. | Not connected to a live study lifecycle. |

Three pips is the requested default. The 20-pip extreme-gap limit is a
conservative **unvalidated engineering assumption** (twice the 10-pip
stop), not a broker-derived risk threshold or evidence of expected market
behavior. Skip events do not count as trades. Unknown data must stop rather
than be treated as zero in any future integration.

## Conflicting operational constraints

The one-trade latch is stricter than the ten-trade limit: it stops the
study after the first completion, so ten completions cannot occur in a
single uninterrupted study. A rejection or reconciliation failure also
immediately latches off, so the three-failure threshold is normally
reachable only through execution exceptions before such a terminal event.
No reset or rearm mechanism is implemented. A future study-wide rearm
protocol would need an explicitly authorized design that retains the
immutable start/expiry, cumulative trade count, audit trail and broker
reconciliation across sessions; simply deleting model state is unsafe.

`check_model` consumes caller-supplied synthetic facts, not trusted broker
facts. Its SQLite record is not a verified production-grade lifecycle or a
cross-process order-submission lock. Loss thresholds, state corruption,
ambiguous submissions, partial fills, unprotected exposure and operator
recovery must be handled in an integrated implementation before use.
