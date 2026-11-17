# Timestamp Blocker Resolution Plan

> **Status update:** This plan's UTC-evidence blocker was superseded by the
> broker-time contract migration documented in
> [BROKER_TIME_MIGRATION_REPORT.md](./BROKER_TIME_MIGRATION_REPORT.md).
> Historical evidence remains unchanged; broker-time operation uses the
> configured explicit offset instead of requiring UTC conversion.

## 1. Remaining unresolved question

For `ICMarketsSC-Demo`, what time basis does the MT5 Python API's raw
`rate["time"]` epoch represent: true UTC, the broker's chart/server wall time
encoded as an epoch, or another basis? The existing samples convert to
approximately two hours ahead of the contemporaneous UTC clock. No MT5 chart
timestamp has been captured for the same bar, so the API-to-chart mapping and
the correct date-aware conversion remain unverified.

## 2. Exact evidence required

Capture one completed EURUSD M5 bar from the connected demo terminal, with
these items retained together:

1. **Chart evidence:** a screenshot of the MT5 EURUSD M5 chart with the
   selected completed bar's displayed time and OHLC visible. Include enough
   of the terminal to identify its displayed clock and account server.
2. **API evidence:** the raw integer `rate["time"]` and raw OHLC for that bar,
   captured using the existing read-only MT5 feed or an equivalent
   read-only call. Preserve the epoch; do not rely only on a formatted `Z`
   timestamp.
3. **Clock evidence:** Windows local time and timezone, plus UTC time, sampled
   immediately before and after the API read. The existing Windows timezone
   is `Taipei Standard Time` (UTC+08:00), but record it again with the capture.
4. **Bar identity and calculation:** match the chart bar to the API bar by
   symbol, timeframe, date, and OHLC; record any ambiguity if OHLC repeats.
   Show the epoch converted as UTC and compare it with both the chart label
   and UTC clock. This must establish whether the epoch tracks UTC or the
   displayed broker time.
5. **Offset authority:** retain written IC Markets confirmation for the
   `ICMarketsSC-Demo` server's chart-time convention and seasonal
   GMT+2/GMT+3 transition rule, or equivalent authoritative documentation
   that explicitly covers the account server.

For a conversion intended to cover historical bars across daylight-saving
changes, also verify a bar from each server-time regime (GMT+2 and GMT+3), or
obtain an authoritative API-specific statement that defines the returned
epoch semantics and conversion across those transitions. A single current
bar proves only the observed date's mapping.

## 3. Method for obtaining evidence

1. In an attended session, connect the existing terminal to the confirmed
   demo server and open EURUSD M5. Do not submit, modify, or close orders.
2. Choose a completed bar and select it in the chart so its timestamp and
   OHLC are visible. Capture the screenshot without obscuring the chart's
   time scale or terminal identity.
3. At the same time, run the existing read-only API capture for the latest
   completed M5 bar. Record the unmodified epoch and OHLC, along with local
   and UTC clock readings immediately before and after. Keep the raw output
   and screenshot together as evidence.
4. Match the same bar by OHLC and date, then compare the chart's displayed
   timestamp with the raw epoch interpreted as UTC. Compute the observed
   offset from the UTC clock; do not assume or apply a two- or three-hour
   correction before this comparison.
5. Ask IC Markets to confirm the server's chart timezone and whether the
   MetaTrader 5 Python API's returned bar epochs are UTC epochs or broker
   wall-clock values. Record the response or authoritative reference.
6. If historical timestamps will be used across seasonal changes, repeat the
   comparison for the other GMT regime or validate the API-specific
   date-aware rule against authoritative documentation.
7. Record the evidence and conversion rule in the timestamp verification
   report. Recheck that completed bars are ordered and that a bar is not
   acted on before its actual close and next-bar opportunity.

This uses the already working MT5 connection, existing read-only price feed,
Windows/UTC clocks, and an attended MT5 chart. The prior unattended session
could not view the chart because Computer Use was unavailable; if it remains
unavailable, the operator can capture the screenshot and readings manually.
No code change or order access is required to collect this evidence.

## 4. Estimated effort

- Same-session chart/API/clock capture and comparison: **20–40 minutes**.
- Request and review of broker confirmation: **15–30 minutes of operator
  effort**, excluding broker response time.
- Additional GMT+2/GMT+3 verification for historical timestamp use:
  **30–60 minutes** if suitable history and authoritative semantics are
  readily available; otherwise dependent on broker response.

These are planning estimates, not measured durations.

## 5. Feasibility decision

**The blocker can realistically be resolved with the available tooling.**
The API connection and clock readings have already been obtained, and the
missing evidence is an attended same-bar visual comparison plus confirmation
of the broker/API time basis. This is a bounded evidence-gathering task; it
does not require changing V1 or building an execution system.

If unattended Computer Use is unavailable, manual chart capture by the
operator is sufficient for the visual part, provided the raw API epoch/OHLC
and clock readings are captured contemporaneously. A broker response may
take longer, but does not make the question inherently unresolvable.

## 6. Decision

**BLOCKER_REMAINS**

The blocker is realistically resolvable, but it is **not removed by this
plan**: the same-bar screenshot, verified API-to-chart comparison, and
authoritative time-basis evidence have not yet been collected. Do not accept
the discrepancy as residual operational risk while a direct verification
path remains available. Keep timestamp-dependent demo execution blocked until
the evidence is captured, reviewed, and the conversion rule is documented.

No strategy rules, signal behavior, or trade records are changed by this
plan.
