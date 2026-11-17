# Single-Trade Validation Result

**EXECUTOR_FAILED_VALIDATION**

No real demo validation order was submitted in this implementation session.
The single-trade mode was tested with a fake MT5 adapter only; this does not
establish real broker behavior.

| Required evidence | Result |
|---|---|
| Order accepted | Not observed |
| SL attached | Not observed |
| TP attached | Not observed |
| Reconciliation successful | Not observed |
| Trade capture successful | Not observed |
| Metrics updated | Not observed |
| Gate updated | Not observed |
| Signal, planned entry, fill, delay and entry price | Not observed |
| Exit reason, commission and swap | Not observed |

The new mode persists an entry-attempt latch and disarms new entries before
the first submission; a confirmed open position is monitored for closure.
Fake-adapter tests cover rejection, ambiguous submission, restart refusal,
fill monitoring and closure/gate update. All 49 paper-trading and 21 root
tests passed. These tests are not a broker execution.

Actual validation remains outstanding. The controlled validation plan requires
an attended demo session and an operator prepared to handle an unprotected or
ambiguous position. A real trade could remain open beyond this session; it
was not safe to start one without confirming that supervision and recovery
are available. A single future fill cannot guarantee future exact-open
execution, and cash costs and tick-value conversion require independent broker
verification.
