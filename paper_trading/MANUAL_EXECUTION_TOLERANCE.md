# Manual Execution Tolerance Review

## Decision

**AUTOMATED_EXECUTION_REQUIRED**

For evidence that is comparable to frozen Breakout Scalping V1, entry must
remain at the next M5 bar open. No positive manual delay tolerance is
supported by the current V1 specification, latency evidence, or demo results.
The only V1-conforming timing tolerance is **0 seconds after the planned next
bar open**. This report does not implement, authorize, or recommend enabling
order automation; it identifies that a human-operated process cannot be
assumed to meet the frozen timing rule.

## 1. Is exact next-bar-open execution essential?

Yes, for a trade to be represented as the frozen V1 baseline. The strategy
specification sets **Entry execution = Next M5 bar open** and computes the
simulated entry from that bar's open (with the specified modeled spread for
longs). Entry time and price jointly determine the position's stop, target,
and subsequent P&L. Entering later can produce a different fill, different
risk levels, and a different outcome. It is an execution-rule deviation, not
just a timestamp-label difference.

The observer latency report found that continuous five-second polling can
detect a bar shortly after close in simulation, but detection after the open
is still late relative to the V1 entry point. Human review and manual order
entry add variable latency that has not been measured or shown to preserve
the V1 result.

## 2. Maximum manual entry delay

**Maximum delay for a V1-compliant entry: 0 seconds after the planned next
M5 bar open.** No positive delay can be declared acceptable from the available
evidence. A tolerance such as 1, 5, or 30 seconds would be an unsupported
change to the execution assumption and must not be introduced by relabeling
the trade as compliant.

This is a timing criterion, not a claim that a real broker fill will occur at
the exact nominal open price. Actual fill prices and any price slippage must
still be recorded and reconciled. A missed open is a missed V1 opportunity;
do not enter late and count it as a compliant V1 trade.

If the project later proposes a positive delay allowance, it must be handled
as a separately versioned, single execution hypothesis under the project
charter, with a pre-defined threshold and evidence/validation plan. No such
version or hypothesis is created here.

## 3. Entry timing evidence fields

Record these fields for every attempted execution, including missed or
noncompliant attempts in an incident log:

| Field | Definition |
|---|---|
| `planned_entry_time_broker` | The timestamp of the next M5 bar open. Under the current contract this is the signal bar close time plus five minutes. Store ISO-8601 with the explicit configured broker offset. |
| `actual_entry_time_broker` | Timestamp of the first actual broker fill. This corresponds to the existing `entry_time_broker` trade field; preserve its full broker precision and explicit offset. |
| `entry_delay_seconds` | Actual first-fill timestamp minus planned entry timestamp, computed from the offset-aware instants in seconds. Positive is late; zero is on time; negative is before the planned open and must be investigated. Preserve the unrounded source timestamps. |

The existing capture schema has `entry_time_broker` and `intended_entry`
(the latter is a **price**, not a time). It does not have dedicated planned
entry time or delay columns. For future evidence collection, store
`planned_entry_time_broker` and `entry_delay_seconds` as explicit fields or
in a structured, machine-readable supplemental record linked by `trade_id`.
Do not silently overload `intended_entry` or change the current schema in
this review.

The planned timestamp is calculated from the observed signal-bar label and
the M5 duration; the actual timestamp comes from broker execution history.
Retain the raw broker record so the derived delay is auditable.

## 4. Analysis after 100 trades

Yes. Once 100 completed, reconciled observations are available, delay can be
summarized descriptively with count, median, mean, standard deviation, and
percentiles (for example p90 and maximum), plus counts on-time, early, and
late. It can also be tabulated alongside actual entry price deviation and
trade outcomes to describe the collected sample.

Such analysis does not make delayed trades V1-compliant retroactively and
does not establish that delay caused a performance difference. Under the
current frozen V1 rule, positive-delay trades must be marked noncompliant and
excluded from the V1 gate's eligible count and primary V1 metrics. If fewer
than 100 compliant trades can be collected manually, the project must not
weaken the rule in the capture log; any proposed tolerance requires a
separately approved and validated versioned hypothesis.

## Scope

No V1 logic, parameter, or capture implementation was changed. No V2 or new
strategy hypothesis was created. No order was submitted. This document
defines the evidence and decision boundary only.

AUTOMATED_EXECUTION_REQUIRED
