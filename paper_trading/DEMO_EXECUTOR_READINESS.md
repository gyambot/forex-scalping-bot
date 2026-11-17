# Demo Executor Readiness

## Conclusion

**EXECUTOR_BLOCKED**

The executor implementation and mock-based safety/reconciliation tests exist,
but it is **not ready to place Demo Trade #1**. The user-reported visually
verified broker offset `+02:00` and approved demo volume `0.01` are now
explicitly configured. All real-terminal read-only preflight checks passed;
see [Final Executor Verification](./FINAL_EXECUTOR_VERIFICATION.md). No demo
order round-trip has been performed to verify broker fill semantics, attached
protection, deal-history availability, and monetary-cost conversion.
Polling attempts to submit at the
next M5 bar as soon as the completed breakout bar is available; it cannot
guarantee a fill at the exact bar-open time or price. Such fills are logged
with their measured delay and are noncompliant unless they meet the frozen
entry assumptions.

## Implemented and tested

- The signal source is the existing `evaluate_v1_signal()`; only LONG/SHORT
  candidates are actionable and no V1 signal arithmetic was changed.
- Every poll requires a connected terminal, known demo account mode, exact
  `ICMarketsSC-Demo` server, trade permissions, and tradable EURUSD. Any live,
  unknown, disconnected, or wrong-server state fails closed.
- A completed signal is eligible for an attempt only while the MT5 current
  M5 bar timestamp is exactly the planned next bar. Missed bars are logged,
  never entered late.
- Market BUY/SELL only; one-position account rule; attached 10-pip stop and
  20-pip target; no entry-order retries after an ambiguous response.
- Execution events include signal, planned entry, submission, fill,
  fill-delay milliseconds, stop/target confirmation, closure, and errors.
- Completed position history is reconciled to the existing trade schema and
  sent through the existing validator; metrics and gate status are refreshed.
- Mock tests cover demo account acceptance, live/unknown/server rejection,
  duplicate suppression, one-position handling, executor-lock contention,
  changed-protection fail-stop, ambiguous result fail-stop, deal provenance,
  full-close reconciliation, trade-record validation, and the complete
  close-to-trade-log-to-metrics/gate path.

## Required before any demo run

1. The project owner must document and approve the demo lot size corresponding
   to one normalized unit, then configure `MT5_DEMO_VOLUME`. Approved and
   configured value: `0.01`.
2. The user reported the broker offset as `+02:00`; it has been explicitly
   configured and the read-only integration preflight passed. Recheck it when
   the broker clock changes.
3. Before collecting a trade, verify that broker history exposes required
   deal costs and that
   `trade_tick_value` / `trade_tick_size` produce correct account-currency
   to pip conversion for this account and symbol. If not, reconciliation
   fails closed.
4. Review the historical negative baseline and explicitly authorize
   demo-only execution as required by the deployment guide.

## Validation evidence

- `python -m unittest discover -s paper_trading\tests` — 45 tests passed.
- `python -m unittest discover -s tests` — 21 tests passed.
- `python -m compileall -q paper_trading\demo_executor.py paper_trading\execution_logging.py paper_trading\execution_reconciliation.py paper_trading\tests\test_demo_executor.py` — passed.
- The 2025 historical backtest was rerun on 73,683 bars; its entire performance
  object exactly matches `backtests/2025_histdata_v1/metrics.json` (`True`).
- The prior real-terminal read-only preflight connected to `ICMarketsSC-Demo`.
  Account mode, server, visible/tradable EURUSD, permissions, approved volume
  and broker volume limits, log path, idle/flat state, reconciliation API,
  metrics, and gate checks passed, but the explicit offset was then missing.
- The subsequent preflight on 2026-11-16 passed all startup checks with
  explicit `+02:00`. That preflight does not validate real fills, protection,
  or deal-cost conversion. See
  [`FINAL_EXECUTOR_VERIFICATION.md`](./FINAL_EXECUTOR_VERIFICATION.md).
- A fake-MT5 lifecycle test verified one reconciled closed trade is validated,
  appended, counted by metrics, and reflected in the gate. The fake adapter
  does not connect to a terminal or submit an actual order.
- No baseline, signal, stop, target, or position-sizing strategy rule was
  modified. No live or demo order was submitted.

Demo gate remains **0 / 100**. The executor is opt-in and does not start
without `--arm-demo-execution`; that flag does not bypass any account checks.
Do not treat this implementation report as execution authorization.

EXECUTOR_BLOCKED
