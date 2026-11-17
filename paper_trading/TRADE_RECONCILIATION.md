# Manual MT5 Demo Trade Reconciliation

Reconcile one complete broker position to one project trade record. A signal,
order request, partial fill, and partial close are not separate trades for
the 100-trade gate.

## Evidence to retain

Before normalizing values, save the MT5 account-history/deal export or
screenshots that establish the account is demo and show the relevant symbol,
order/position references, fills, costs, and final flat state. Keep the raw
export immutable. Record its filename or reference in `notes`; never include
credentials.

## Match the V1 signal

1. Match the observation by EURUSD symbol and the **signal bar opening
   timestamp**. Confirm that its row is `LONG` or `SHORT`, not `NO SIGNAL`.
2. Verify from the corresponding completed M5 bar and preceding 20 completed
   bars that the close is strictly above the prior high for a long or strictly
   below the prior low for a short. Record the signal close, prior 20-bar high,
   and prior 20-bar low.
3. Populate `signal_bar_open_time_broker` with the bar label and
   `signal_time_broker` with the time that bar completed and its close became
   available (normally five minutes after the label). Preserve the raw broker
   timestamp and configured offset.

## Match entry and exit

- **Entry:** Match MT5 deal/order references, direction, and fills to the
  manually entered position. Record the first fill time in
  `entry_time_broker`; aggregate partial entry fills to a quantity-weighted
  `actual_entry`. Record `intended_entry` separately as the reference next-M5
  open and state whether it is bid or ask in notes. Capture actual entry
  spread when available; otherwise use `unavailable: reason`.
- **Exit:** Match every closing deal to the same position until MT5 confirms
  it is fully flat. Record `exit_time_broker` when the position became flat and
  aggregate partial close fills to a quantity-weighted `actual_exit`.
  Reconcile the broker-confirmed exit reason, position/order/deal references,
  and exit spread (or state why unavailable).
- **Outcome:** Reconcile gross realized price P&L, commission, financing, and
  other fees against broker history. Convert all costs and net P&L consistently
  to pips using the documented 0.0001 pip size and the same conversion basis;
  document account currency and conversion evidence in notes. Record
  `pnl_r` as net `pnl_pips / 10`. `hold_minutes` must equal elapsed time from
  first fill to final flat time.

## Validation and eligibility

Before import, verify all capture fields, explicit-offset broker timestamps and their
order, actual broker evidence, V1 signal direction/close condition, initial
10-pip stop and 20-pip target from actual entry, resolved costs, unique
`trade_id`, `completed=true`, and accurate `rule_compliant` status. The
importer rejects invalid timestamps, prices, incomplete records, and duplicate
IDs. It does not replace broker reconciliation or establish that a trade was
rule-compliant.

Keep deviations visible. If an order was late, the stop/target differed,
multiple positions overlapped, or management departed from V1, mark
`rule_compliant=false` and describe the facts. Do not alter timestamps or
prices to make the record pass.

Only one fully closed, reconciled, rule-compliant demo position advances the
gate by one. Signals, unfilled/rejected requests, partial exits before flat,
historical trades, and noncompliant demo positions do not count.
