# Demo Gate Status

**V1 = ACTIVE**

- **Demo Trades Completed:** **0 / 100**
- **V2 Eligibility:** **BLOCKED**
- **Reason:** **100 demo trades not yet completed.**

Historical backtest and validation trades do not count. Count only unique,
fully closed, broker-reconciled V1 demo positions that meet the
[trade-capture specification](./TRADE_CAPTURE_SPECIFICATION.md). Maintain the
count from the operational demo trade log and update this status only after
the records have been checked.

Prospectively designated engineering validation trades are recorded separately
and do not count toward the formal study or its 100-trade gate. A simulated
validation gate is not study progress. This exclusion does not lower the
100-trade threshold.

No V1 strategy rules or parameters are changed by this status document. No V2
is defined or authorized.
