# Candidate 9 Execution Readiness

## Decision: UNAVOIDABLE_EXECUTION_BLOCKER

The [integrated simulation](paper_trading/candidate9_integrated_simulation.py)
and [tests](CANDIDATE_9_LIFECYCLE_TEST_RESULTS.md) exercise a modeled
signal-to-reconciliation sequence with one in-memory submission, scripted
supervision, and separately recorded simulated execution and validation data.
They do **not** implement or prove the actual demo submission/supervision/
recovery lifecycle requested. The simulation cannot submit broker orders.

## Blocking evidence

1. The [submission scaffold](paper_trading/candidate9_demo_submission.py)
   contains a single MT5-like `order_send` call, but is hard-inhibited and
   defaults to disarmed. Tests override the inhibit only in memory and use
   fakes. The scaffold now verifies an entry deal and attached protection,
   polls the position and reconciles fake broker history against separately
   recorded execution and validation rows. Those rows share one database;
   they are not an independent external execution log. No actual broker
   response, attached protection or history has been verified. The
   scaffold is not a usable executor; do not enable it.
   The [read-only order preview](paper_trading/candidate9_order_preview.py)
   constructs an unsubmitted request from a fresh demo-account observation
   and classifies responses, but it does not call `order_send`, check the
   kill switch or expiry, verify account-currency risk against the broker,
   or authorize an order. Its inputs and quote can become stale immediately.
2. A caller-driven polling loop exists but no supervised service or process
   watchdog is deployed. Polling, kill detection and protective orders are
   not guaranteed during process or network outages. The kill switch stops
   execution but does not cancel an order or close exposure. Account-currency
   daily loss uses broker-like UTC-day deals plus open profit and swap; the
   inputs and timestamp semantics are unverified with the broker. Non-trade
   account deals fail closed. No stop or target is repaired automatically.
3. Broker timestamp/quote semantics and cost/1R conversion are not verified
   for candidate 9. The one-trade latch is terminal and persists across
   restart, so without an authorized, safe manual rearm protocol a clean
   study cannot reach ten completed trades. The seeded ten-count test does
   not resolve this conflict, and no ten-trade summary or rearm is
   implemented. The latch has not been bypassed.
4. The user prohibits MT5 connections and demo orders in this phase.
   Consequently real broker acceptance, position protection, fill costs
   and reconciliation cannot be observed here. Mock success must not be
   presented as broker-level proof.

These are implementation and evidence gaps, not proof that the strategy
cannot ever be implemented. Resolving them requires candidate-specific
broker integration and separate permission for appropriate read-only and
eventual demo execution verification. No order has been placed, no executor
armed, and the kill switch remains in place. V1 and its gate remain untouched.

**UNAVOIDABLE_EXECUTION_BLOCKER**
