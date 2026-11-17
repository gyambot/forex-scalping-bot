# Operator-Authorized Demo Validation: Trade 1

The owner explicitly confirmed presence and authorized one demo validation
trade. The executor was not armed and no order was submitted in this phase.
This is an incomplete validation, not a broker rejection or a failed live
trade.

## Pre-arm evidence

The read-only preflight completed at 2026-11-16 12:59:11 +08:00 with exit
code 0. The [integration result](./DEMO_EXECUTOR_INTEGRATION_RESULT.md)
records a demo account on `ICMarketsSC-Demo`, EURUSD availability, trade
permissions, configured offset `+02:00`, approved volume `0.01`, and passing
logging, reconciliation, metrics and gate startup checks. The gate had zero
eligible trades. A separate read-only inspection found zero open positions,
zero pending orders, and a fresh EURUSD quote approximately 1.06 seconds old.
These are point-in-time observations and must be repeated before arming.

## Timeline, execution and protection

No signal was awaited, and no submission or fill occurred. Signal time,
planned entry, submission, fill, fill delay, ticket, entry price, stop, target,
exit time, exit price, reason, commission and swap were therefore not
observed. Broker order acceptance, position opening, SL/TP attachment and
normal position closure remain unverified.

## Reconciliation, capture, metrics and gate

No trade existed to reconcile or capture; no trade-driven metrics or gate
update occurred. The current validation path writes completed trades to the
normal demo log and recalculates the normal metrics and 100-trade gate.
The existing fake-broker closure test demonstrates that a compliant
validation trade can advance that gate to `1 / 100`. This conflicts with
the requested engineering-only exercise that must not begin the study.
The gate's existing policy also counts qualifying demo positions; excluding
this one without an explicit, durable classification would be misleading.
The trade was not attempted rather than silently counting or discarding it.

## Executor shutdown and safety

The one-attempt latch has been tested with a fake broker but not exercised
against a real order. A safety gap was corrected: during an armed validation,
an unexpected open position now stops execution before signal evaluation.
The existing runner failure path persists the failed latch. The paper-trading
suite passed 50 tests, including 17 executor tests; these do not establish
real broker behavior.

## Remaining work

Establish and verify an engineering-trade recording and gate treatment that
does not start or contaminate the study, while retaining accurate broker
records and an auditable metrics/gate check. Then repeat all pre-arm checks,
including account-wide positions, pending orders and quote freshness. Run
only with continued operator attendance and a broker-terminal recovery plan;
stopping the executor does not itself protect or close an open position.
Independent broker evidence is still required for fill timing, protection,
deal costs and reconciliation. No V1 rules were changed.

**EXECUTOR_FAILED_VALIDATION**
