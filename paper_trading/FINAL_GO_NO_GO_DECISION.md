# Final Go/No-Go Decision

## Owner decision and scope

The owner accepts actual demo-broker fills as execution evidence; an exact
theoretical next-bar-open fill is not required for this engineering
validation. This resolves the prior conceptual objection to measuring a
real fill. It does not change the frozen V1 specification, make a late
fill V1-compliant, or include this engineering trade in the formal study.

## Operational assessment

**The current validation mode is not ready to perform the authorized
experiment.** It still rejects a submission decision made even one
microsecond after the planned next-bar open. It reads completed bars and
performs account, position, order and quote checks before that decision.
Consequently, a naturally detected breakout will ordinarily be logged as
missed rather than submitted, even though the owner accepts the resulting
actual fill for engineering validation. A fake-adapter test verifies this
late-decision rejection. A passing preflight does not exercise this path.
This is an implementation blocker, not a remaining demand for an exact
broker fill.

The validation-only submission guard must be reconciled with the owner's
decision and tested before arming. This assessment does not change that code
or authorize a normal study trade. A validation fill that deviates from
frozen V1 must retain its true compliance status and remain isolated.

## Risk, recovery, and study evidence

- The executor requires the configured demo account on
  `ICMarketsSC-Demo`, EURUSD and `0.01` lots; it checks account-wide positions
  and pending orders and persists a single-attempt latch before submission.
  Fake-adapter tests cover rejection, ambiguity, restart refusal and
  unexpected positions; these are not evidence of actual broker behavior.
- The order request includes SL/TP, and the executor checks protection after
  the fill. If a submission is ambiguous, protection cannot be confirmed, or
  the terminal disconnects, execution stops but an open position is **not**
  automatically closed. An attending operator must inspect and manage the
  demo position in the terminal. Automated recovery handles only a known,
  already closed position, not an ambiguous submission or an open position.
- Completed engineering trades use separate validation trade, metrics and
  simulated-gate files. The shared latch and lock remain in use. Fake tests
  exercise isolated capture and recovery without changing study outputs.
  The formal gate was `0 / 100` on the successful read-only check.
- Actual acceptance, protection, closure, broker deal history and independent
  cost conversion are not yet verified; these are the objectives of the
  controlled exercise, not evidence that a broker order already succeeded.

## Current read-only checks

On 2026-11-16, `--verify-validation` initially failed because the EURUSD
quote was judged stale or in the future. A subsequent read-only inspection
found zero open positions and zero pending orders, with the last quote
approximately 1.3 seconds **ahead** of the configured broker clock. A later
repeat of `--verify-validation` passed and `check_gate` reported `0 / 100`.
This was intermittent; repeat the preflight immediately before arming and
stop on failure rather than assume clock or feed consistency.

`python -m unittest paper_trading.tests.test_demo_executor` passed all
21 executor tests. No order was placed, no position was modified, and no
strategy rules were changed in this assessment.

## Decision

**UNAVOIDABLE_BLOCKER**
