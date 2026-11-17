# Controlled Validation Trade: Blocker

## Decision

**UNAVOIDABLE_BLOCKER**

The engineering trade is isolated from the study, but the currently
permitted execution mechanism cannot guarantee the frozen V1 entry at the
next M5 bar's open. No validation order was submitted in this phase.

## 1. Exact blocker

The [frozen V1 specification](../strategies/breakout_scalping_v1.md)
requires entry at the next M5 bar open. The
[manual execution tolerance review](./MANUAL_EXECUTION_TOLERANCE.md)
states that a late entry is a missed V1 opportunity, with no positive
tolerance. The executor learns the completed breakout-bar result at or
after that boundary, then persists and logs state and sends a market order.
The broker determines when and at what price it fills. Even if the
submission decision is exactly on the boundary, the code cannot ensure
that submission or fill occurs at that exact instant and frozen modeled
entry price.

Validation mode now declines a submission decision already observed after
the planned open. This prevents a known late decision but **does not**
guarantee an on-time fill, and in normal operation may mean that no signal
can be submitted. A real trade could demonstrate one fill but cannot
guarantee compliance before submission or for future fills. Merely marking
a late fill noncompliant afterwards does not make the entry compliant.

## 2. Why code cannot resolve it under the current constraints

Polling, faster local computation, retries or clock checks cannot control
network transit, broker processing, or market-order fill price. Predicting
the signal before the bar closes or changing to another order type would
change the authorized execution assumptions. The approved validation
mode permits market orders and does not permit pending entry orders.
No evidence establishes an allowed broker mechanism that guarantees the
specified time and price. No V1 entry rule was changed.

## 3. Why configuration cannot resolve it

The explicit broker offset and approved demo volume configure timestamp
representation and position size; neither controls the broker's fill.
The read-only `--verify-validation` command passed against the configured
demo terminal, including account, server, symbol, permissions, offset,
fresh quote, flat account, no pending orders, study outputs and isolation
paths. It cannot prove order acceptance, protection or fill behavior.
The broker-time contract also notes that the API epoch semantics are not
independently proven and the fixed offset must be rechecked by the operator.

## 4. Why documentation cannot resolve it

Documentation can record deviations, recovery and independent broker
evidence, but cannot make a late or differently priced market fill equal the
frozen entry. Isolating a trade protects study metrics; it does not alter
the entry rule. One demonstration would not prove future execution fidelity.

## 5. Human action required

The project owner must resolve the conflict before arming: establish and
authorize a broker-supported method that actually satisfies the frozen
entry and other existing order restrictions, **or** explicitly decide in a
later scope whether an engineering-only noncompliant execution experiment
is permissible without representing it as V1-compliant. The latter is not
authorization to change V1, count the trade, or start the study. A
separately approved strategy-rule change would require the charter's
version and evidence controls; none is proposed or implemented here.

Regardless of that decision, repeat the read-only preflight immediately
before an attended session, verify broker clock, flat account and pending
orders, and provide operator recovery for ambiguous or unprotected
positions. Do not retry an uncertain order. Actual broker acceptance,
SL/TP, exit and independent deal-cost conversion remain unverified.

## Work completed and evidence

- Validation capture routes to `VALIDATION_TRADING_LOG.csv`; isolated
  metrics and a simulated gate are separately labeled. The persisted
  classification, shared state and lock prevent a validation restart from
  bypassing the one-attempt latch. A no-order recovery command is available
  only for a known, already closed validation position.
- Fake-broker tests cover compliant and noncompliant capture, an interrupted
  report followed by idempotent recovery, unchanged study files and metrics,
  classification/path failures, stale quote, offset, pending orders, late
  decisions, unexpected positions, rejection and ambiguous submissions.
  They do not prove a real broker lifecycle.
- `python -m unittest discover -s paper_trading\tests`: **54 passed**.
  `python -m unittest discover -s tests`: **21 passed**.
  The read-only validation preflight passed. The formal gate remains
  **0 / 100**.

No V2, optimization, or strategy filter was added.
