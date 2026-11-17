# Final Executor Verification

## Result

**EXECUTOR_BLOCKED**

The real-terminal read-only startup preflight passed every check and reported
`READY_FOR_DEMO_TRADE_1`. That result establishes startup readiness only. It
does not resolve the execution-fidelity and broker reconciliation prerequisites
identified in [Demo Executor Readiness](./DEMO_EXECUTOR_READINESS.md), so it
does not establish that the executor is ready to collect a V1-compliant trade.

## Configuration and observed evidence

- The user reported visually observing UTC `04:41:44` and the MT5 EURUSD
  clock `06:41:44`, a difference of `+02:00`. This is user-reported visual
  evidence; no screenshot was captured in this run.
- `MT5_BROKER_UTC_OFFSET=+02:00` is explicitly configured in the local
  environment file. The connector's active configuration also returned
  `+02:00`. No offset was inferred or detected automatically.
- The configured, approved demo volume is `0.01`.
- At `2026-11-16T12:44:08+08:00`, the command
  `python -m paper_trading.demo_executor --verify-only --verify-volume 0.01`
  exited with code `0`. The complete observed output is in
  [Demo Executor Integration Result](./DEMO_EXECUTOR_INTEGRATION_RESULT.md).

## Startup checks

| Check | Result | Evidence |
|---|---|---|
| MT5 connection | PASS | MT5 initialization succeeded. |
| Demo account and server | PASS | Account mode DEMO; server `ICMarketsSC-Demo`. |
| EURUSD | PASS | Visible, trade mode `4`, tick size `0.00001`. |
| Permissions | PASS | Terminal, API, account and expert permissions enabled. |
| Broker-time configuration | PASS | Explicit active offset `+02:00`. |
| Demo volume | PASS | `0.01` within reported min/max and step. |
| Broker-time feed | PASS | M5 bar `2026-11-16T06:40:00+02:00`; quote 249 seconds after bar open. This checks quote/bar consistency, not independent clock accuracy. |
| Logging | PASS | Execution-log path and schema checked; no event appended. |
| Reconciliation startup | PASS | No existing trade records, idle executor state, flat account and callable deal-history API. Actual deal history and cost conversion were not verified. |
| Metrics | PASS | Saved metrics match a fresh in-memory calculation; zero eligible trades. |
| Gate | PASS | Count matches zero eligible trades. |

Failed or skipped startup checks: **none**.

## Remaining blockers and limitations

1. The executor submits a market order after detecting a completed bar and
   cannot guarantee the frozen V1 entry at the exact next-bar open time and
   price. Actual broker fill semantics and protection attachment are untested.
2. The preflight checks that the history API exists and tick metadata is
   positive; it does not demonstrate that actual deal costs or the
   account-currency-to-pips conversion are correct. The existing readiness
   report requires these to be verified before collecting a trade.
3. The deployment guide requires owner review of the negative historical
   validation and explicit authorization for demo-only evidence collection;
   this verification-only request is not authorization to place an order.
4. The broker offset is a manually maintained value and must be rechecked when
   the broker changes its clock.

## No-order verification

The verification mode is mutually exclusive with the execution arm flag and
does not call the order-submission or modification path. The account was flat
when checked. The trade log, metrics, and gate file had identical SHA-256
hashes before and after the run; no execution log or executor-state file was
created. The demo gate remains `0 / 100`. No V1 code or rules were changed.
