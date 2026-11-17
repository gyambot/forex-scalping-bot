# Breakout Scalping V1 — Demo Deployment Guide

## Status and scope

- Strategy: **Breakout Scalping V1**, frozen at EURUSD M5, 20-bar breakout,
  next-bar-open entry, 10-pip stop, 20-pip target, and one active position.
- Deployment environment: **demo account only**. Never connect this workflow to
  a live account.
- The repository's `scripts/backtest.py` is an offline CSV backtester. The
  read-only MT5 connector can inspect terminal/account state and fetch EURUSD
  quotes and completed M5 bars, but it does not calculate live signals, send
  or manage orders, monitor positions, or recover executions.
- This guide documents readiness requirements; it does not authorize demo
  orders until a broker/platform procedure can reproduce the frozen V1 signal
  and execution rules without discretionary additions.
- The historical baseline and temporal validation were both negative. Treat
  this as controlled evidence collection, not a profitability claim.
- The validation report records a failed historical promotion check. Before
  any demo order is placed, the project owner must explicitly review and
  acknowledge that result and authorize demo-only evidence collection. This
  guide is not that authorization.

## Broker requirements

Select a regulated, reputable broker/platform that provides a clearly
identified **demo** environment and supports all of the following:

1. EURUSD prices and market order execution during the intended demo period.
2. Timestamped M5 candles or the underlying timestamped quotes needed to
   establish the close of each M5 signal bar and the next-bar entry.
3. Executed order records with broker timestamps carrying explicit offsets, actual fill prices,
   direction, filled quantity, and order/position references.
4. Bid and ask quotes, or enough information to record the actual spread at
   signal, entry, and exit. Record costs as charged; do not replace them with
   the backtest's fixed-spread assumption.
5. Attached stop-loss and take-profit orders at the specified V1 levels, plus
   observable status for accepted, rejected, modified, and filled orders.
6. Written contract details: symbol mapping, pip/tick size, contract size,
   minimum and step volume, stop-distance rules, order execution policy,
   margin/leverage, trading hours, commissions, and financing treatment.
7. An exportable or otherwise auditable order/trade history. Broker statements
   or platform records should be retained as evidence for each completed
   position.

Broker-specific symbol suffixes (for example, `EURUSD.a`) are acceptable only
when the broker confirms that the instrument is EURUSD and its contract and
pip conventions have been documented. Do not silently substitute another
instrument or contract.

## Account requirements

- Use a separate account explicitly marked **DEMO**. Verify the account label
  and server before each session.
- Record a non-sensitive account alias in the trade log. Never put passwords,
  API keys, account credentials, or full payment/account details in project
  files, screenshots, or reports.
- Use a fixed demo balance and currency during the 100-trade collection
  period. Record the starting balance, account currency, leverage, and any
  broker reset or balance change in the operations log.
- Before the first order, document the demo order size and confirm it is
  accepted by the broker. The repository specifies one normalized unit, not a
  broker lot size or account-risk budget. Do not infer a live size or increase
  size to compensate for losses.
- Do not deposit funds or place live trades as part of this workflow. Demo
  results do not guarantee live execution or outcomes.

## Timeframe and signal requirements

- Use **M5** bars only. Confirm the platform's candle boundary and broker-time
  convention; retain MT5 wall-clock fields with the configured explicit offset.
- A signal is evaluated after an M5 candle is complete, using the prior 20
  completed candles, excluding the signal candle.
- Entry is intended at the next M5 bar open. Record the actual first available
  fill and its deviation from the intended entry; do not backdate an order or
  substitute the signal-bar close for an actual fill.
- One position maximum. Do not add to a position, hedge it, or open another
  V1 position while it is active.
- Preserve the specified 10-pip stop and 20-pip target from actual entry as
  defined by the strategy. Do not trail, widen, tighten, manually close early,
  or alter orders for strategy reasons. If broker constraints prevent these
  levels or the required order sequence, stop and resolve readiness before
  collecting trades; do not approximate a different rule.

## Symbol, price, and spread requirements

- Instrument is EURUSD only; record the broker's exact display symbol.
- Confirm EURUSD pip size is 0.0001 for the selected contract. Record quote
  precision and minimum price increment.
- Record bid/ask spread at signal, entry, and exit when available; also record
  actual commission, slippage, financing, and other charges. V1 backtest's
  constant 1.0-pip spread is not a demo execution guarantee or a substitute
  for observed costs.
- Do not invent a numeric spread cutoff or add a strategy spread filter. The
  checklist's spread check means that current bid/ask quotes are available and
  their actual spread is recorded. If quotes are stale, missing, or the
  platform cannot execute the specified order safely, halt the operational
  session, record the incident, and do not count a nonexistent or unfilled
  position as a completed trade.

## Data and record requirements

- Keep broker-provided M5 bars or quote/order exports needed to reconstruct
  each signal and fill. Preserve original exports unchanged; store working
  copies separately.
- Store broker-time timestamps with an explicit offset for the signal, order
  submission, fill/entry, every partial fill or exit, and final exit. Preserve
  the broker's raw timestamp and export unchanged.
- Capture one trade record per fully closed position using
  [`TRADE_CAPTURE_SPECIFICATION.md`](./TRADE_CAPTURE_SPECIFICATION.md) and
  [`DEMO_TRADING_LOG.csv`](./DEMO_TRADING_LOG.csv). Preserve broker references
  and evidence paths.
- Use the recorder and reporting commands in the repository README. The
  recorder rejects non-demo accounts, incomplete records, malformed values,
  and duplicate trade IDs.
- Count a trade toward the gate only after the position is flat, costs are
  known or explicitly marked pending, required fields are complete, and
  broker history reconciles to the record.
- Backtest and validation trades do not count toward the 100-demo-trade gate.

## Operational limitations and stop conditions

- No order placement, automated execution, position monitoring, alerting, or
  order recovery exists in this repository. The MT5 interface is read-only. Do
  not assume running the Python backtester will place or supervise demo orders.
- Manual handling can miss the next-bar entry or misread a candle. Any
  discrepancy from V1 must be recorded; do not silently “correct” it. A
  non-compliant or unverified trade does not count toward the gate.
- M5 OHLC cannot determine exact intrabar order of stop/target touches. Broker
  demo records are the source of actual fills and costs; they will not be
  identical to historical OHLC simulation.
- Pause and record an incident if the broker disconnects, quotes are stale,
  timestamps cannot be reconciled to the configured broker offset, order state is uncertain, the account is
  not clearly demo, a stop/target is rejected, or a duplicate/overlapping
  position may exist. Resume only after positions and records are reconciled.
- Do not modify the strategy or introduce discretionary filters during the
  100-trade collection period. Record operational incidents separately from
  strategy outcomes.

## First-session sign-off

Do not begin order entry until the project owner has reviewed the negative
historical validation and explicitly authorized demo-only evidence collection,
and the execution method has been checked against the frozen V1 specification
and the checklist in
[`DEMO_EXECUTION_CHECKLIST.md`](./DEMO_EXECUTION_CHECKLIST.md) passes. Record
the broker, platform, demo alias, symbol mapping, configured server offset, volume,
and responsible operator. If any requirement cannot be verified, the
deployment is **not ready**.
