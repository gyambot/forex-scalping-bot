# Manual Demo Trade Workflow

This is a human-operated, demo-only capture process. The signal tools do not
place orders, and the importer only validates and appends a completed record.
V1 parameters remain frozen; no V2 or strategy changes are authorized by
recording a trade.

## 1. Observe a V1 signal

Use the read-only signal observer and its `SIGNAL_OBSERVATION_LOG.csv`. Confirm
the account displayed in MT5 is the IC Markets **demo** account and the symbol
is EURUSD (or the broker-confirmed EURUSD mapping).

Use the signal bar timestamp, close, direction, and breakout level from the
observation row. A `NO SIGNAL` row is not an entry instruction. The raw signal
observer does not know whether a V1 position is already open; the human must
check the one-position rule and follow the frozen V1 next-M5-bar entry rule.
If the next-bar entry is missed, do not enter late and call it the original V1
entry.

MT5 API wall-clock fields are retained directly. Confirm the configured
`MT5_BROKER_UTC_OFFSET` matches the terminal's displayed server clock before
transcribing timestamps. Preserve broker-native evidence; do not convert the
bar label to UTC.

## 2. Human reviews the signal

Before any action, check the per-signal and incident-stop items in
`DEMO_EXECUTION_CHECKLIST.md`. Confirm:

- The account is demo, not live, and the broker connection is stable.
- The signal is based on a completed M5 bar and the strict close beyond the
  prior 20-bar high/low.
- No V1 position is already active.
- Signal and next-bar entry times are correctly understood.
- Required order protection and manual broker operations are understood.

If any check fails or the signal is ambiguous, pause and document the incident.
The signal itself does not authorize an order.

## 3. Human manually enters in MT5 demo

Only the human may enter the position in the MT5 desktop UI, after reviewing
the checklist. Enter only the manually approved demo position and apply the
frozen V1 initial stop and target relative to the actual fill. Do not use this
project's Python tools to submit, modify, or close orders; they have no such
workflow.

Capture the actual entry fill time and price, observed spread, order/position
references, and the accepted stop/target from MT5. If the order is rejected,
partially filled, late, duplicated, or otherwise deviates from V1, preserve
the evidence and record the incident; do not represent it as a compliant V1
trade.

## 4. Record the outcome after the position is flat

Wait until the broker confirms the whole position is closed. Export or retain
the relevant MT5 history/deal evidence. Reconcile all partial entry/exit fills
into one broker position using quantity-weighted prices, and resolve actual
commission, financing, and other costs.

Copy `trade_import_template.csv` to a separate local working file. Create a
unique `trade_id`; fill all columns using the meanings in
`TRADE_CAPTURE_SPECIFICATION.md`. Use broker timestamps with explicit offsets
and preserve raw source evidence. Do not store passwords, access tokens, or
other credentials in the CSV.

Set `completed=true` only when flat, the record is complete, costs are
resolved, and broker history has been reconciled. Set `rule_compliant=false`
if the recorded execution deviated from frozen V1; explain the deviation.
Never delete or hide a loss or an operationally noncompliant completed
position.

## 5. Validate and append

Save exactly one completed trade row under the template header. Then run:

```powershell
python -m paper_trading.manual_trade_capture --trade-csv paper_trading\trade_import.csv
```

The importer validates the full capture schema, explicit-offset timestamp order, positive
prices, V1 signal/stop/target relationships, nonnegative hold time and
spread, the completed flag, and unique trade ID. It refuses to append a
partial or duplicate record. The import CSV must have the exact schema and
exactly one data row. For a test or alternate log, specify
`--log path\to\DEMO_TRADING_LOG.csv`; the existing file must use the exact
schema.

If validation fails, correct the working import from the broker evidence and
retry. Do not edit the operational log by hand to bypass a validation failure.
Keep the raw broker export immutable and link its filename/reference in
`notes`.

## 6. Save, recalculate, and verify gate

After a successful append, verify the new row against MT5 history and run:

```powershell
python -m paper_trading.generate_demo_metrics
python -m paper_trading.check_gate
```

Metrics and the gate use completed, rule-compliant, reconciled demo records;
noncompliant records remain in the log but are excluded from eligibility. A
signal observation is not a trade and does not advance the count. The gate
remains **0 / 100** until eligible records are actually captured; reaching 100
allows a V2 review only, not automatic creation or promotion of V2.

## Operational boundary

This workflow never reads MT5 account positions or calls MT5 order APIs.
Observation, human review, manual UI execution, reconciliation, and CSV
capture are separate steps. No automation opens, manages, or closes a trade.
