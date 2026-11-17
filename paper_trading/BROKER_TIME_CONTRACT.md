# Broker-Time Contract

## Purpose and scope

This contract defines timestamp representation for MT5 live observations,
signal processing, manual trade capture, and demo reporting. It does not
change Breakout Scalping V1 price rules, authorize order submission, or make
timestamp evidence more conclusive than the underlying observations.

## Definition

**Broker time** is the MT5 clock value observed in the terminal/API, represented
as an ISO-8601 timestamp with the configured explicit offset. For MT5 epoch
values, `broker_time.py` renders the numeric epoch as UTC calendar fields and
attaches `MT5_BROKER_UTC_OFFSET` without shifting those fields. This is a
deliberate representation of the observed broker wall clock, not a verified
conversion of the epoch into a globally correct instant.

The configured offset defaults to `+02:00`. The operator must set it to the
offset currently displayed by the connected broker server (for example,
`+03:00` during the broker's seasonal clock period). The code does not discover
or update seasonal changes automatically.

## Source and flow

1. MT5 tick and completed-M5-bar epochs are read directly from the API.
2. The configured offset is attached by `epoch_to_broker_time()`.
3. Live signal evaluation validates explicit-offset, ordered M5 timestamps;
   breakout decisions continue to use completed-bar OHLC and sequence.
4. The observer records its observation clock and the source bar using the
   configured broker offset.
5. Manual trade capture validates explicit-offset event times and stores
   `*_time_broker` columns.
6. Demo metrics order eligible trades by parsed exit time and report their
   interval as `reporting_period_broker_time`.

The observer and tools must not reinterpret a broker timestamp as UTC merely
because it has an ISO offset, nor append `Z` to a broker wall-clock value.

## Storage rules

- Persist timestamps as ISO-8601 with an explicit numeric offset, such as
  `2026-11-12T08:40:00+02:00`.
- Use `*_broker` names for demo trade timestamp fields and
  `reporting_period_broker_time` for demo metric periods.
- Preserve the original broker export and its execution references as source
  evidence. Do not silently rewrite broker-native evidence.
- Historical datasets may retain their original explicit source offset,
  including UTC, where that is how the data was provided. The MT5 contract
  does not require historical sources to be relabeled as broker time.
- Never store account credentials in logs or reports.

## Validation and ordering

- Every stored timestamp must parse as ISO-8601 and include an explicit
  numeric offset.
- Bar inputs must remain on M5 boundaries and strictly increase in source
  sequence. Duplicate bar labels are rejected.
- Trade timestamps must satisfy the signal-bar, signal-close, entry, and exit
  ordering rules in the capture specification. Elapsed hold time is calculated
  from offset-aware timestamps, so offset changes preserve elapsed time when
  the supplied offsets are correct.
- Ordering compares timestamp instants; reporting labels retain the supplied
  broker offset. Do not compare raw offset-less strings to determine event
  order.
- A fixed offset can be wrong or stale. Verify it against the current terminal
  clock before using live timestamps; quote freshness warnings are not
  permission to trade.

## V1 and metrics invariants

- The V1 breakout is a close beyond the prior 20 completed-bar high/low.
  Timestamp representation does not enter that price comparison.
- Entry sequencing remains next-bar sequence; stop and target distances remain
  the frozen V1 values. This migration does not add filters or change those
  rules.
- Trade P&L, win/loss, expectancy, profit factor, and closed-trade drawdown
  use the captured trade sequence and P&L values. Demo metrics sort by parsed
  exit time and label reporting periods in broker time.
- Calendar-day labels can differ from a UTC-source report near midnight.
  Historical backtests continue to use the timestamps supplied by their
  source data; broker-time adoption does not rewrite that historical source.

## Known limitations

- The fixed offset is configured manually. A seasonal change not reflected in
  `MT5_BROKER_UTC_OFFSET` can make clock freshness and timestamp labels wrong.
- Existing timestamp evidence did not include a same-bar chart screenshot and
  API comparison. The conversion convention follows the observed chart/API
  clock alignment and is not independent proof of MT5 epoch semantics.
- The observer can report timing anomalies; it does not enforce a human's
  next-M5-bar entry. A timestamp contract alone does not establish trade
  compliance or authorize demo execution.
- Existing timestamp/readiness reports preserve their historical UTC-era
  findings. Refer to the migration report for which records and tools were
  updated and for test evidence.
