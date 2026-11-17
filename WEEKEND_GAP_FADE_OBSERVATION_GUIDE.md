# Weekend Gap Fade: Observation Guide

Follow the [validation plan](WEEKEND_GAP_FADE_VALIDATION_PLAN.md). This is
read-only observation: do not submit any live or demo order, arm an
executor, or automate trading.

## Before Friday close

1. Use a broker EURUSD chart with the exact symbol and bid M5 bars recorded.
   Record the broker server, chart timezone and a verified UTC offset for
   the specific date. If offset or data provenance is unverified, mark the
   relevant observation unknown rather than guessing.
2. Create an evidence folder named for the Friday date. Capture the most
   recent Friday bar as close as practicable, then confirm the final observed
   Friday M5 candle after close. Capture its timestamp and OHLC and preserve
   the exported bar history, if available.
3. Note observation start time, expected broker schedule and clock source.
   Begin monitoring before the expected reopen; verify time synchronization
   and retain any offset or uncertainty.

## At reopening

1. Capture the first *observable* quote with bid, ask, quote timestamp,
   local capture timestamp and symbol in the same screenshot if possible.
   If monitoring started late, record that explicitly; do not claim it was
   the broker's first quote. Record spread `(ask - bid) / 0.0001` pips.
2. Save timestamped ticks if the broker provides them. Capture the first
   post-reopen M5 bid bar open and, once completed, its OHLC and open time.
   Convert bar timestamps to UTC with documented offsets; check the frozen
   Friday-to-Sunday/Monday and 36-hour conditions.
3. Calculate the signed gap and the >=5-pip rule. Save the calculation
   before looking at later outcomes. Signal is available only after the
   first bar completes, not at the first quote.
4. For a signal, capture the next available bar's theoretical bid open and
   time. Capture the first valid bid/ask at or after that time, its quote
   timestamp, and capture time. Record the entry-quote spread, quote delay
   and the signed adverse quote-movement proxy defined in the plan.
   A late quote is not a fill and the proxy is not actual slippage.
5. Record the reference entry and observed-quote proxy entry, each path's
   initial 10-pip stop and 20-pip target, and whether a previous hypothetical
   position blocks this signal. Record time-stamped bid/ask evidence until
   each hypothetical path exits. Record missing ticks, unresolved intrabar
   ordering, and pending paths explicitly. Do not claim a stop-level fill
   through a price gap without evidence.

## CSV field conventions

Write one row per planned weekend in
[the log](WEEKEND_GAP_FADE_VALIDATION_LOG.csv); its columns are an index to
the detailed evidence packet:

| Field | Entry |
|---|---|
| `weekend_id` | Friday UTC date in `YYYY-MM-DD` form. |
| `signal_present` | `yes`, `no`, or `unknown`. A blocked signal remains `yes`. |
| `friday_close`, `sunday_open` | Bid prices; reopening may occur Monday. Leave empty when unavailable. |
| `gap_size_pips` | Signed pips; leave empty if unknown. |
| `gap_direction` | `up`, `down`, `flat`, or `unknown`. |
| `spread_pips` | First **observable** quote's spread; leave empty when unavailable. Entry spread belongs in the evidence packet. |
| `slippage_pips` | Signed adverse entry quote-movement proxy from the plan; **not actual fill slippage**. Empty if not applicable or unknown; negative means favorable. |
| `expected_trade` | `long`, `short`, `none`, `blocked`, or `unknown`; record signal direction separately in notes if blocked. |
| `expected_result` | Reference-path `target`, `stop`, `stop_gap`, `pending`, `unknown`, or `not_applicable`; record proxy outcome separately in packet. |
| `notes` | Evidence packet location, entry/reference prices and UTC times, entry spread, proxy result, missing data and limitations. Quote CSV values containing commas. |

For unavailable observations use `unknown` and blank numeric fields—not
zeros or fabricated prices. Store timestamps, entry price, stop, target,
source and both path results in the packet even though the required compact
CSV has no dedicated columns for them.

## Reduce observer bias

Record all ten scheduled weekends in order, including missed and no-signal
cases. Save the signal calculation and timestamped screenshots before
reviewing future price action; keep originals and append corrections with
date, reason and source instead of overwriting history. Do not alter the
5-pip threshold, range, stop/target, window or selection based on observed
results. Report unavailable data and unobserved quote intervals. Do not
confuse a screenshot of a quote with an executed order or an audited
tick-level record.

Remove or obscure account numbers, credentials and unrelated personal
information from copies used for reporting; preserve the relevant prices,
timestamps, symbol and data source.
