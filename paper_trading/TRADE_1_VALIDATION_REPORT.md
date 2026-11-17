# Controlled Demo Validation Trade #1

## Decision

**EXECUTOR_FAILED_VALIDATION**

No order was submitted and no trade was opened. The authorized validation
trade was not attempted because an operator's continuous attendance and
ability to intervene if a position is unprotected or execution is ambiguous
could not be confirmed. This is an incomplete validation, not evidence that
the broker rejected an order or that the executor failed a live trade.

## Preflight

At approximately 2026-11-16 12:56 +08:00, the read-only verification command
completed with exit code 0. Its
[integration result](./DEMO_EXECUTOR_INTEGRATION_RESULT.md) recorded:

- Connected demo account on `ICMarketsSC-Demo`; EURUSD visible and tradable.
- Configured broker offset `+02:00`; configured demo volume `0.01` within
  reported broker limits.
- Trade permissions, logging, idle reconciliation state, metrics and gate
  startup checks passed.
- Independent read-only account inspection found **0 open positions** and
  **0 pending orders**. The EURUSD quote age was approximately **0.68 s**
  at that inspection.
- The executor's 16 fake-MT5 tests passed, including one-attempt latch
  scenarios. These tests are not proof of broker execution.

The preflight's deal-history check establishes API availability, not actual
deal completeness or correct account-currency conversion. Its feed check
establishes quote/bar timestamp consistency, not a guarantee of later fills.
The checks are a point-in-time snapshot and must be repeated before arming.

## Trade summary and execution timeline

| Evidence | Observation |
|---|---|
| Signal, planned entry, submission and fill timestamps | Not observed; executor was not armed. |
| Fill delay, entry price, broker ticket | Not observed. |
| Stop-loss and take-profit | Not submitted or verified against a broker position. |
| Exit time, exit price and reason | Not observed. |
| Commission and swap | Not observed. |
| Trade reconciliation and capture | Not performed; no validation trade exists. |
| Metrics and gate | Startup consistency passed; no validation trade was added. Gate remained `0 / 100` at preflight. |
| One-trade latch | Tested with a fake adapter; not exercised against a real order. |

## Observed issues and recommendations

1. Establish an attended operator and a concrete broker-terminal recovery
   procedure for a disconnected, ambiguous or unprotected position before
   starting the authorized one-trade run. Stopping the executor does not close
   or protect an open position.
2. Repeat all preflight checks, including pending orders and quote freshness,
   immediately before arming. Review the
   [controlled validation plan](./CONTROLLED_DEMO_VALIDATION_PLAN.md).
3. This request describes an engineering test, not the start of the 100-trade
   study. The existing executor refreshes the normal metrics and gate after a
   completed record, and may increment the eligible count if the trade is
   rule-compliant. Resolve this handling before running rather than silently
   counting or discarding a validation trade.
4. An actual result still requires broker-side evidence for fill timing,
   attached protection, deal costs and independent reconciliation. One trade
   cannot guarantee future exact-open fills or establish performance.

No V1 strategy rules, stop loss, take profit or entry rules were changed.
