# Demo Execution Integration Test

## Purpose and safety boundary

This is a read-only preflight for the approved 0.01-lot EURUSD demo setup on
`ICMarketsSC-Demo`. Run it while attended with the intended demo terminal
connected:

```powershell
$env:MT5_DEMO_VOLUME = "0.01"
python -m paper_trading.demo_executor --verify-only --verify-volume 0.01
```

`--verify-only` is mutually exclusive with `--arm-demo-execution`. The
verification path does not call `order_send`, select symbols in Market Watch,
write executor state, append execution events, generate metrics, or update the
gate. It only reads terminal/account/symbol/quote/bar/position/history
capabilities and validates local paths and schemas. A temporary file probe is
created and removed in each output directory to verify write access.

The command writes its observed results to
[`DEMO_EXECUTOR_INTEGRATION_RESULT.md`](./DEMO_EXECUTOR_INTEGRATION_RESULT.md).
The result report contains no account login or credentials.

## Startup validation sequence

| # | Check | Pass evidence |
|---|---|---|
| 1 | MT5 startup | MT5 initializes successfully and reports a connected terminal. |
| 2 | Demo account validation | The configured login matches the connected account and the reported account mode is DEMO. No login number is copied to the report. |
| 3 | Server validation | The configured and connected server are exactly `ICMarketsSC-Demo`. |
| 4 | EURUSD validation | `EURUSD` symbol information is available and already visible; trade mode is not disabled or close-only; tick metadata is available. The checker will not make the symbol visible because that would mutate terminal state. |
| 5 | Broker-time validation | `MT5_BROKER_UTC_OFFSET` is explicitly configured, valid, and matches active MT5 configuration. The quote time follows the current M5 bar time within that bar after applying the configured broker-time representation. The checker does not infer a seasonal offset. |
| 6 | Trade-permission validation | Terminal trading, terminal API, account trading, and expert-trading permissions are enabled. The checker reads permissions and does not change them. |
| 7 | Logging validation | Existing execution-log CSV schema is valid, if present, and its parent directory supports a temporary create/delete probe. No execution event is appended. |
| 8 | Reconciliation startup validation | Existing trade log schema is readable; executor state is idle; the account has no open positions; MT5 deal-history API is available; tick size/value are positive. No history is changed. |
| 9 | Metrics startup validation | Stored metrics parse and exactly match a fresh in-memory calculation from the trade log. The metrics file is not rewritten. |
| 10 | Gate startup validation | Gate schema is recognized and its demo count matches the current number of eligible trades. The gate file is not rewritten. |

Any failed or skipped required check yields `EXECUTOR_BLOCKED`. The verifier
closes its MT5 connection in a `finally` path.

## Interpretation

`READY_FOR_DEMO_TRADE_1` means only that this startup preflight passed. It is
not evidence that the broker has accepted an order, that stops/targets attach
correctly, or that deal history and account-currency cost conversion have been
verified on a completed trade. This phase submits no order; those execution
facts cannot be established here.

No V1 rules, parameters, signal calculations, trade records, metrics, or gate
counts are changed by the verification.
