# Demo Executor Integration Result

- Run time: 2026-11-16T12:59:11.582171+08:00
- MT5 configured server: ICMarketsSC-Demo
- Broker offset setting: +02:00
- Approved demo volume: 0.01
- Mode: read-only verification; no order/position/pending-order modification attempted.
- No trade record was created by this verification run.

The MT5 connection shutdown path was executed after verification.

| Check | Result | Evidence |
|---|---|---|
| MT5 startup connection | PASS | MT5 initialization succeeded. |
| Demo account and server | PASS | Account mode=DEMO; connected server=ICMarketsSC-Demo. |
| EURUSD symbol | PASS | EURUSD visible=True; trade mode=4; tick size=1e-05. |
| Trade permissions | PASS | Terminal, API, account, and expert permissions are enabled. |
| Broker-time configuration | PASS | Explicit configured broker offset=+02:00. |
| Approved demo volume | PASS | MT5_DEMO_VOLUME=0.01; broker limits 0.01..200.0, step 0.01. |
| Broker-time feed | PASS | Offset=+02:00; quote is 248.0s after the current M5 bar open; current M5 bar=2026-11-16T06:55:00+02:00. |
| Execution logging | PASS | Execution log path and schema are writable/readable; 0 existing events; no execution event was appended. |
| Position and reconciliation readiness | PASS | Trade schema validated; 0 existing trade records; executor state is idle; account is flat; deal-history API is available. |
| Metrics startup | PASS | Saved metrics match an in-memory calculation; eligible trades=0; no file was changed. |
| Gate startup | PASS | Gate schema is valid and count matches 0 eligible trade(s); no file was changed. |

This startup verification does not test broker order acceptance, protective-order attachment, actual fill behavior, or live deal-cost conversion because order submission is prohibited in this phase.

**READY_FOR_DEMO_TRADE_1**
