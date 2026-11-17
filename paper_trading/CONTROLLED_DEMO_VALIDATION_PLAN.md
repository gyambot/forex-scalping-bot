# Controlled Demo Validation Plan

> Historical assessment: a single-trade validation mode has since been added.
> Its fake-adapter tests are documented in
> [Single-Trade Validation Result](./SINGLE_TRADE_VALIDATION_RESULT.md); the
> actual attended demo lifecycle remains unverified. The assessment below
> records the conditions that applied when this plan was written.
> Its section 5 count guidance is superseded: engineering validation trades
> are isolated from the formal study and its gate. See
> [Blocker Report](./BLOCKER_REPORT.md) for the current execution decision.

## Decision

**EXECUTOR_BLOCKED**

One completed, broker-executed demo position is the minimum prospective
experiment that can exercise the executor's actual submit, fill, protection,
closure and reconciliation path. The earlier read-only preflight cannot do
that. A single trade can provide evidence for that particular execution; it
cannot guarantee exact fills in future or establish profitability.

The current executor is not yet demonstrated to enforce the requested
**maximum of one validation trade**: its armed loop continues polling after a
rejection and after a closed position is recorded. An operator watching for
the first closure cannot guarantee that the loop stops before the next signal
is submitted. Do not start an armed run until an independently verified
one-trade stop procedure or safeguard is available. Designing or implementing
that safeguard is outside this assessment.

The project owner must also explicitly authorize this specific demo-only
experiment after reviewing the negative historical validation, as required by
the deployment guide. This request is for a plan, not authorization to place
an order.

## Why execution evidence is needed

| Question | What the existing evidence shows | Minimum additional evidence |
|---|---|---|
| Fill timing and price | The executor detects a completed bar and submits a market order during the next M5 bar; neither polling nor a market order guarantees the exact open. | One actual V1 signal, submission and broker fill with planned open, millisecond fill time, next-bar bid open and actual entry price. One result measures one fill, not a future guarantee. |
| SL/TP acceptance | The request includes both levels; the executor checks the position and can send one protective adjustment. Mock tests and read-only checks do not prove broker acceptance. | Broker order/position evidence for both 10-pip and 20-pip levels relative to actual entry, including any adjustment response. One position can show both attachments, but will normally exit through only one of them. |
| Deal and cost reconciliation | Code validates entry provenance and full volume, then converts recorded cash amounts using tick value and tick size. The preflight checked API availability, not a real lifecycle. | A fully closed position's entry and exit deals, costs, volume, symbol metadata, resulting trade record, and an independent comparison with the broker statement and calculation. Existing suitable broker history, if available, could supplement cost checks without a new order, but cannot prove this executor's new lifecycle. |

## 1. Preconditions

1. Owner reviews the historical validation and expressly authorizes **one**
   controlled `0.01`-lot demo position for execution validation only.
2. Before arming, establish and test a deterministic way to prevent a second
   submission, including after a known rejection and after position closure.
   The existing executor has no one-trade limit; a manual stop after seeing a
   closure is not sufficient proof. A failed or rejected attempt is not a
   completed validation trade and must not be retried without a new decision.
3. Ensure the intended connected account is DEMO on `ICMarketsSC-Demo`, with
   EURUSD M5 visible, `MT5_DEMO_VOLUME=0.01`, and explicit broker offset
   `+02:00` verified as current. Recheck the offset when the broker clock
   changes.
4. Ensure the account is flat, has no relevant pending orders or unresolved
   executor state, and only the supervised executor can trade the account.
   Identify an attended operator, a stop/escalation contact and a safe
   broker-side response if protection is missing. Do not deploy on a live
   account.
5. Record baseline hashes/copies of the trade log, execution log if present,
   metrics and gate. Preserve credentials and account identifiers outside
   evidence intended for sharing.

## 2. Startup checks

Run the existing read-only preflight immediately before the experiment:

```powershell
python -m paper_trading.demo_executor --verify-only --verify-volume 0.01
```

Require exit code zero and inspect every result: connected demo account and
exact server, EURUSD, permissions, volume, broker-time configuration/feed,
logging, idle/flat reconciliation state, metrics and gate. Independently
check pending orders and fresh terminal quotes. Stop if any check is
unavailable, fails, or the account state changes. Save the preflight report
and starting trade/gate counts. Passing preflight alone does not establish
order or fill behavior.

## 3. Execution checks

Only after the one-trade stop condition is independently verified and
authorization is recorded, use the existing executor on a naturally occurring
V1 LONG or SHORT signal; do not manufacture a signal or manually substitute a
trade. Stay in attendance and record the signal bar and prior 20 bars, planned
next-bar open, submitted order, result code, order/deal/position references,
submission and fill timestamps, fill delay and fill price.

Compare the broker's actual millisecond fill time with the planned next-bar
open. Compare actual price with the frozen backtest's intended entry: next-bar
bid open plus one pip for LONG, bid open for SHORT. Any timing or price
deviation is a V1 entry-fidelity failure, not an accepted tolerance.

Confirm broker-displayed SL and TP after any executor adjustment: LONG entry
minus 10 pips and plus 20 pips; SHORT entry plus 10 pips and minus 20 pips.
Monitor the demo position and protection while it is open. Do not add, scale,
trail or manually close for strategy reasons. Wait for broker-side closure at
SL or TP and ensure the one-trade stop condition prevents subsequent entry
while allowing closure capture and reconciliation.

## 4. Reconciliation checks

After the position is flat, obtain broker entry and exit deal history and
statement records. Compare timestamps, symbol, direction, order and position
references, magic number and filled volumes with executor state and events.
Confirm total entry and exit volume equals `0.01`; investigate partial fills,
extra deals, missing fields or inconsistent references rather than guessing.

Independently compare realized broker profit, commission, swap and fees with
the record. Capture broker tick size and tick value and verify the conversion
used by the code: pip value = tick value × `0.0001` / tick size × entry
volume; net pips = (profit + commission + swap + fees) / pip value.
Verify that this conversion matches the broker's contract/account currency
and realized statement, including any conversion-rate effects. If it cannot
be substantiated, leave reconciliation unresolved.

Require one complete validated trade record, matching broker evidence, with
no duplicate trade ID. Preserve planned entry, submission, fill and delay in
the execution log and trade notes.

## 5. Metrics and gate checks

Recalculate metrics from the validated log and compare them with the saved
metrics and gate. A **fully closed, broker-reconciled, rule-compliant** trade
may increase the eligible gate count by exactly one; from the recorded
`0 / 100` baseline that would be `1 / 100`. An early manual safety close,
late or otherwise noncompliant fill, or unresolved trade must not be counted.
If the existing eligibility result is wrong, stop and investigate rather than
manually force a count. A single trade is execution validation, not a
performance assessment or evidence of profitability.

## 6. Failure conditions

Stop new execution immediately on a second-submission risk, live/unknown
account, server mismatch, missing permission or fresh quote, stale offset,
disconnect, unexpected position/order, rejection, partial or ambiguous
submission, missing/incorrect protection, missing deals or costs, mismatched
volume/identity, incorrect trade record or inconsistent metrics/gate.
Treat a late or differently priced fill as a fidelity failure even if broker
submission and protection work. Do not retry an uncertain order.

## 7. Rollback and recovery

Stop the executor's new submissions and preserve its state and logs. Inspect
the demo terminal's actual positions, pending orders and history before any
restart; a `submitting` state may represent a filled order and must not be
cleared or retried blindly. Stopping the process does **not** close or protect
an open position. If the demo position is unprotected or another urgent
operational hazard occurs, the authorized operator must manage the demo
position through the broker terminal to contain the risk; record any manual
intervention and treat an early safety close as noncompliant.

Keep original broker exports and append-only evidence. Do not delete trade
records, reset state, restore stale gate/metrics files, or hide discrepancies.
Resolve broker state and reconcile using the project's documented workflow
before a separately authorized restart. If the end-to-end automatic capture
cannot be safely completed under the one-trade constraint, stop and record
the experiment as incomplete rather than risking another submission.

## 8. Evidence to collect

- Owner authorization, operator, starting demo account/server and preflight
  report; redact credentials and unnecessary account details.
- Proof of the independently verified one-trade stop mechanism and its result.
- Signal bar and preceding 20 bars, next-bar bid open, signal direction,
  order request/result, broker order/deal/position references.
- Planned, submission and actual fill times with offsets and milliseconds,
  fill delay, intended and actual prices, entry spread, and SL/TP screenshots
  or broker records before and after any adjustment.
- Broker history/statement with entry/exit prices, volumes, profit, commission,
  swap, fees, tick metadata and independent pip-conversion calculation.
- Execution events, state transitions, final trade record, metrics and gate
  snapshots before and after, plus any incident or manual safety intervention.

No order is placed by this plan. No V1 rules, stop, target, entry logic or
strategy parameters are changed.
