# Broker Integration Options — V1 Demo Collection

**Decision scope:** choose the shortest controlled path to collect 100 eligible
completed Breakout Scalping V1 demo positions. This is an operational
comparison, not a broker endorsement or a profitability assessment.

## Current project readiness

The repository contains an offline CSV backtester, demo recorder/metrics/gate
tools, and a read-only MT5 connector and price feed. It has no live signal
monitor, order sender, broker reconciliation process, or order recovery. A
broker connection alone will therefore not start collecting trades; a
separately authorized V1 execution adapter and operator procedure would still
be required.

V1 remains unchanged: EURUSD M5, strict close outside the prior 20 completed
bars, intended next-bar entry, a 10-pip stop, a 20-pip target, and one active
position. The adapter must implement those existing rules exactly, record
actual fills and costs, and stop if the broker cannot honor the required
execution. It must not substitute a different bar basis, late entry, stop, or
target.

The historical validation is negative. Before any demo order is submitted,
the project owner must review and explicitly authorize demo-only evidence
collection, as required by the
[deployment guide](./DEMO_DEPLOYMENT_GUIDE.md). The recommendation below is
not that authorization.

## Options comparison

Ratings are relative to this repository and current Windows workspace. They
are qualitative engineering estimates, not provider uptime guarantees. Demo
account availability, symbols, contract details, and API access depend on
broker and jurisdiction; confirm them directly before committing to a path.
Demo trades simulate execution and do not establish live performance.

| Option | Required software and access | Deployment complexity | Cost | Operational reliability | First-100 suitability |
|---|---|---|---|---|---|
| **MetaTrader 5 + official Python package (recommended)** | A broker demo with MT5 and EURUSD; Windows MT5 desktop terminal; Python and MetaQuotes' `MetaTrader5` package; optional always-on Windows host/VPS. The package connects to a running terminal and exposes bars and trade operations. | **Low–medium.** Closest match to the repository's Python/Windows stack. Still requires a small, tested adapter and a continuously connected terminal. | The cited MetaQuotes interface documentation does not list a separate API charge. Broker demo conditions and optional VPS pricing vary; verify before use. | **Medium–high when supervised.** Broker-side stops can remain at the broker after entry, but the Python process depends on the terminal, host, network, and broker. Reconcile from terminal/account history after restart or disconnect. No SLA is implied. | **High if an eligible MT5 demo is available.** Direct fit to existing Python tooling and clear visual account/order reconciliation. |
| **MetaTrader 4 (MQL4 Expert Advisor)** | A broker MT4 demo with EURUSD; MT4 terminal; an Expert Advisor coded and run in MQL4. | **Medium–high.** The V1 logic and operational capture must be implemented in an EA. The official MetaQuotes Python-terminal integration found for this comparison is for MT5, not MT4. | Platform, broker demo, and optional VPS costs depend on the broker/vendor; no separate API charge is assumed here. | **Medium.** Execution is native to the terminal, but continuous operation, broker-side stop acceptance, restart recovery, and audited CSV capture still need implementation and verification. | **Medium–low.** Viable if an existing trusted MT4 EA or MT4-only broker is mandatory; otherwise it adds a language port and another place for V1 behavior to diverge. |
| **OANDA v20 Practice REST API** | Eligible OANDA v20 fxTrade demo account; API token; Python HTTP client or official samples; persistent networked process. The API provides pricing/candles, order, trade, position, and transaction endpoints. | **Medium.** No trading terminal is needed, but the adapter must manage API authentication, streaming/polling, retries, transaction reconciliation, and token protection. | OANDA documents a free demo account. The cited API pages do not state a separate API usage fee; account/API eligibility and any other terms must be confirmed for the user's OANDA division. | **Medium–high when implemented with persistent connections and account-update reconciliation.** The API has documented connection practices; token handling and application recovery remain the project's responsibility. | **High if eligible and an OANDA demo is already available; otherwise uncertain.** A clean Python API is attractive, but v20 is not available to all OANDA divisions. |
| **cTrader Open API** | cTrader-affiliated broker demo and cTrader ID; registered Open API application; OAuth credentials/tokens; Python SDK or JSON/Protobuf client; running service. | **Medium–high.** Requires application registration, OAuth authorization/refresh, asynchronous protocol handling, and account/position reconciliation. | The cited Open API documentation does not state an API charge. Broker demo and optional hosting terms vary; confirm directly. | **Medium–high when supervised.** Supports demo, market data, trading, and history, but depends on a persistent service and correct auth/reconnect handling. Published request limits apply. | **Medium.** A capable option where the chosen broker already uses cTrader, but more setup than the recommended MT5 Python route for this Windows project. |

### Cost and reliability qualifications

- “No separate API charge stated” is not a promise that every broker, account,
  data feed, or hosting arrangement is free. Confirm demo duration, order
  conditions, data access, and any fees with the selected broker.
- A VPS is optional for initial supervised collection from an always-on,
  secured Windows computer. If one is used, it is an operational hosting cost;
  no vendor-specific price is assumed here.
- None of the cited platform/API documentation establishes end-to-end
  reliability for this project. The reliability ratings describe dependency
  count and recovery burden, not guaranteed availability, fill quality, or
  profitability.
- Do not put terminal passwords, API tokens, or account credentials in source
  control, CSVs, notes, or reports.

## Recommended Option

**MetaTrader 5 with MetaQuotes' official Python integration, on a broker's
demo account.**

This recommendation is conditional on confirming a broker that is available
to the operator and offers an MT5 demo with EURUSD, reconcilable broker-time
history,
and attached 10-pip/20-pip protective orders. If no such broker is available,
do not force the selection; re-evaluate OANDA v20 Practice only after confirming
regional v20 eligibility.

## Justification

### Why this is the fastest path in this repository

1. The project already runs in Python on Windows and has a frozen Python V1
   specification plus the trade recorder, metrics generator, and gate checker.
   The official MT5 Python package communicates with the MT5 desktop terminal
   and documents retrieving rates and sending trade requests. This avoids
   first porting the frozen rules to MQL4 or implementing an OAuth/REST or
   Protobuf service.
2. The terminal visibly exposes the selected account/server, symbol, open
   positions, orders, and history for operator checks. This complements the
   existing broker-reconciled CSV workflow; it does not replace it.
3. MT5's documented Python trade request supports explicit stop-loss and
   take-profit values. The demo adapter can therefore request protection with
   the entry and verify the broker's accepted order result. Broker contract
   rules may still reject or constrain the request; if exact V1 protection is
   not accepted, stop rather than approximate it.

### Why this is the safest practical path

- Keep all initial operation **demo-only** and supervise the terminal and
  Python process. Assert the account is demo before allowing any order request;
  fail closed if account identity, connection, price data, or order result is
  uncertain.
- Use broker-side stop/target protection and verify it after every entry.
  Reconcile positions and history on startup, after reconnect, and on close to
  prevent duplicate entries and incomplete records.
- Keep the implementation narrow: only the frozen V1 signal/entry/exit
  behavior, data validation, order/state reconciliation, and existing trade
  capture. No parameter tuning, filters, V2, or manual trade-management
  discretion.
- Do not describe this as safest in an absolute sense. A directly supported
  broker REST API may be operationally better if it is already available and
  the owner can secure and supervise it. MT5 is selected for fit and minimum
  integration work here, not because its fills or uptime are guaranteed.

## Minimum implementation requirements before first order

1. **Owner authorization:** review the negative validation result and record
   explicit approval for demo-only evidence collection. No live credentials
   or live account may be used.
2. **Eligible demo environment:** choose a broker available in the operator's
   jurisdiction; obtain an MT5 demo; verify account/server identity and
   EURUSD symbol mapping, contract/pip size, volume increment, order execution
   policy, and trading hours.
3. **Bar fidelity:** retrieve completed M5 bars, identify the signal candle's
   broker-time label convention, preserve the MT5 wall-clock fields with an
   explicit configured offset, and verify that the broker's bar basis is
   compatible with V1's documented bid OHLC input.
   Reject stale, missing, duplicate, out-of-order, or incomplete bars. Do not
   act on the currently forming candle.
4. **Exact V1 signal and timing:** use only the last 20 completed bars before
   the signal bar; signal only on strict close beyond that prior range; submit
   at the next M5 bar opening opportunity. A missed opportunity is logged as
   missed, not entered late.
5. **Account and position controls:** enforce the demo account assertion and
   one-position maximum using broker state, not only local process memory.
   Recover open positions/orders from terminal history after restart.
6. **Execution protection:** use EURUSD pip size 0.0001 and verify that
   broker-side stop and target are exactly 10 and 20 pips from the actual
   entry fill. Request attached protection with entry when supported, then
   verify actual fill and accepted levels. Test whether fill slippage changes
   those distances; if the broker cannot safely establish the frozen levels
   from the actual fill, do not collect trades on that setup. Halt and
   reconcile if levels are rejected, changed, or missing. Do not substitute
   different distances.
7. **Observability and audit:** log broker-time signal, submit, fill, exit,
   prices, spread, costs, order/position references, and errors without secrets.
   Preserve raw broker exports unchanged. Call the existing recorder only for
   fully closed, reconciled, eligible positions.
8. **Operational recovery:** handle terminal disconnect, process restart,
   rejected orders, partial fills, unknown position state, missing/stale
   quotes, and log-write failure by pausing new signals and reconciling broker
   state. Do not invent a numeric spread cutoff. Never retry an ambiguous
   order blindly.
9. **Demo-only dry checks:** confirm connectivity, account assertion, M5 bars,
   signal calculation against known input, broker-offset configuration, order request
   validation, and history reconciliation without sending a live order. Do
   not manufacture a signal or count a test order toward the 100-trade gate.
10. **Supervised collection:** after all
    [execution checklist](./DEMO_EXECUTION_CHECKLIST.md) items pass, start
    supervised demo collection. After each eligible closed position, update
    the log, run `python -m paper_trading.generate_demo_metrics` and
    `python -m paper_trading.check_gate`, and regenerate the descriptive report
    with `python -m paper_trading.generate_demo_review`. Review
    `paper_trading/DEMO_WEEKLY_REVIEW.md` descriptively; do not change V1.

The repository is **not ready to place broker orders** until the adapter,
broker/account selection, owner authorization, and above checks are complete.
The first 100 count includes only unique, fully closed, reconciled,
rule-compliant V1 demo positions with resolved costs. At 100, status becomes
`READY_FOR_V2_REVIEW` only; no V2 is thereby approved or created.
The elapsed collection time depends on genuine V1 signals and market
availability. Do not manufacture trades, increase size, or enter late to
accelerate the count.

## Step-by-step setup plan

### Phase A — Select and prepare the broker account

1. Confirm a legally available MT5 broker and demo account; verify the broker
   permits demo EA/API trading and EURUSD orders with attached protective
   levels.
2. Record the broker, exact demo server, account alias (not credentials),
   exact EURUSD symbol, contract details, account currency, timezone, and demo
   size in the operational setup record.
3. Install the broker's MT5 desktop terminal on the current Windows computer.
   Sign in only to the clearly labeled demo server and verify its account
   identity in the terminal.
4. Confirm M5 bars are complete, chronological, explicitly offset, and on
   five-minute boundaries. Confirm the price basis and bid/ask spread values
   against broker records.

### Phase B — Build the smallest tested adapter

5. Install the MetaQuotes `MetaTrader5` Python package in the project's chosen
   Python environment and pin the version verified with the installed
   terminal. Keep credentials in the terminal's secure account store or an
   approved secret store, not in command lines or project files.
6. Add a narrow broker adapter that: attaches to the expected terminal;
   asserts the account is demo and the server/symbol are allow-listed; reads
   completed M5 bars; applies only the exact frozen V1 rules; deduplicates
   signals; checks broker positions/orders; sends the next-bar market request
   with the required stop and target; and records terminal retcodes and
   execution references. Verify that accepted protection is exactly 10/20
   pips from actual fill; reject a broker setup that cannot safely meet this
   requirement.
7. On process start and every reconnect, query positions, pending orders, and
   recent history before accepting another signal. The state in the broker
   account is authoritative.
8. Implement fail-closed behavior: any unexpected account, symbol, quote,
   timestamp, fill, stop/target, process, or log condition pauses new orders
   and raises a visible error. Pause if quote/spread data is unavailable or
   stale, but do not add a numeric spread cutoff. Do not silently retry an
   ambiguous submission.
9. Test signal behavior with recorded inputs and mocked broker responses.
   Verify that an order request cannot be created for non-demo accounts,
   incomplete bars, a duplicate signal, an already-open position, or a
   rejected stop/target configuration.

### Phase C — Verify and collect

10. Run dry checks without submitting a live order. Then use only a genuine
    frozen-V1 signal for any demo execution check; never submit an artificial
    order and count it as evidence.
11. For each closed demo position, reconcile the terminal's fills, costs, and
    final flat status; record the complete trade via
    `python -m paper_trading.trade_recorder --trade-json <trade.json>`.
12. Generate metrics and gate status, keep immutable broker exports, and
    produce a descriptive weekly review. Count only eligible completed trades.
    Stop at 100 for review; do not implement V2 as part of this deployment.

## Official documentation checked

The following official vendor documentation was reviewed on **2026-11-12**.
Broker availability and fees must be reconfirmed at account setup.

- MetaQuotes, [Python integration with MetaTrader 5](https://www.mql5.com/en/docs/python_metatrader5) — terminal IPC, quotes/rates examples.
- MetaQuotes, [initialize](https://www.mql5.com/en/docs/python_metatrader5/mt5initialize_py) — terminal path, account/server connection options.
- MetaQuotes, [copy_rates_from](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesfrom_py) — OHLC rate retrieval and UTC example.
- MetaQuotes, [order_send](https://www.mql5.com/en/docs/python_metatrader5/mt5ordersend_py) — trade request fields including `sl` and `tp`.
- MetaQuotes, [MT5 algorithmic trading / Expert Advisors](https://www.metatrader5.com/en/terminal/help/algotrading) — native terminal robots.
- MetaQuotes, [MQL4 OrderSend](https://docs.mql4.com/trading/ordersend) — MT4 order function and protective levels.
- OANDA, [v20 REST API introduction](https://developer.oanda.com/rest-live-v20/introduction/) — v20 account divisions, free demo, API capabilities, account/API setup.
- OANDA, [authentication](https://developer.oanda.com/rest-live-v20/authentication/) — personal token handling and security.
- OANDA, [pricing endpoints](https://developer.oanda.com/rest-live-v20/pricing-ep/) and [order endpoints](https://developer.oanda.com/rest-live-v20/order-ep/) — candle/pricing and order requests/results.
- OANDA, [API best practices](https://developer.oanda.com/rest-live-v20/best-practices/) — persistent connections and account-update reconciliation.
- Spotware, [cTrader Open API](https://help.ctrader.com/open-api/) — demo support, market data/trading/history, Python SDK availability and rate limits.
- Spotware, [Open API authentication](https://help.ctrader.com/open-api/account-authentication/) — OAuth application/account authentication and token lifecycle.
