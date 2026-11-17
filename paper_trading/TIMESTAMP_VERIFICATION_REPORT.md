# MT5 Timestamp Verification Report

> **Status update:** This report documents the pre-migration UTC investigation.
> Its UTC-alignment conclusion remains valid for that question, but the
> project has since adopted the explicit-offset broker-time contract in
> [BROKER_TIME_CONTRACT.md](./BROKER_TIME_CONTRACT.md). UTC conversion is no
> longer the live timestamp contract.

**Status:** Timestamp alignment is not verified for demo execution.  
**Conclusion:** **TIMESTAMP_ALIGNMENT_UNRESOLVED**

## Summary

The observed discrepancy is approximately **+02:00:00** in MT5 API timestamps
relative to the Windows UTC clock. This matches IC Markets' published statement
that its server time and charts use GMT+2 or GMT+3 during daylight saving.
The likely explanation is that broker-server wall time is being represented
or interpreted as though it were UTC.

This is not yet a proven root cause. The MT5 desktop chart clock could not be
observed in this unattended session, and MetaQuotes' Python documentation
describes rate data as UTC. The broker-specific runtime values therefore
conflict with the documented UTC expectation. Do not apply a two-hour offset
or use these timestamps to time demo entries until the same bar has been
visually compared in MT5 and the broker's timestamp semantics confirmed.

## Requested timezone findings

| Item | Finding | Evidence / confidence |
|---|---|---|
| Local computer timezone | Windows reports `Taipei Standard Time`, UTC+08:00, with no DST. | Direct Windows `Get-TimeZone` output; high confidence. |
| Local clock and UTC | At the runtime sample: local `2026-11-12T12:51:36.679962+08:00`; UTC `2026-11-12T04:51:36.679998+00:00`. These agree to within about 0.00004 seconds. | Direct Python runtime values; high confidence for the observed clock relationship. |
| Windows time synchronization | `w32tm /query /status` returned `The service has not been started`. | Direct command output. External NTP synchronization was not verified. |
| Broker server/chart timezone | IC Markets' public trading-hours page says its server time and charts are GMT+2, or GMT+3 when daylight saving is in effect. The account is connected to `ICMarketsSC-Demo`. | Broker-published statement and runtime account server. The exact offset displayed by this connected terminal was not read directly. |
| MT5 terminal/chart timezone | Not directly observable here. MT5 `terminal_info()` returned build and terminal path, but no timezone field; Computer Use was unavailable in the unattended session. | Unverified. |
| Tick timestamp timezone | Raw MT5 `tick.time` converted using Unix epoch semantics is about two hours ahead of contemporaneous UTC. It matches the published broker offset, but that does not prove whether the API value is UTC, broker wall time encoded as an epoch, or otherwise adjusted. | Direct MT5 runtime plus broker documentation; likely broker-offset representation, medium confidence. |
| M5 bar timestamp timezone | Raw `rate['time']` likewise converts to a value about two hours ahead of UTC. The connector renders that value as UTC with a `Z` suffix. Its actual source timezone remains unverified. | Direct MT5 runtime and source inspection; likely the same offset as ticks, medium confidence. |
| UTC conversion in connector | Both tick and bar epoch values are converted with `datetime.fromtimestamp(..., timezone.utc)`. This is correct for a true UTC Unix epoch, but would mislabel broker wall time if the MT5 value carries the server's UTC+2 wall clock instead. The connector does not apply or infer a broker offset. | Direct source inspection; high confidence. |

## Same-bar and live API evidence

The observer uses the local UTC clock for `timestamp` and preserves the
connector's bar timestamp separately as `bar_timestamp`. The two recorded rows
show:

| Signal bar | Observer UTC timestamp | MT5-reported bar label | MT5-reported bar close | Difference from expected close |
|---|---|---|---|---:|
| 2026-11-12 06:35 label | 04:44:47.966331Z | 06:35:00Z | 06:40:00Z | +01:55:12 |
| 2026-11-12 06:40 label | 04:49:28.728585Z | 06:40:00Z | 06:45:00Z | +01:55:31 |

Those expected-close differences are consistent with a stable two-hour offset
minus the normal few-minute observation delay. They do not prove the chart's
displayed time or establish the API contract for this server.

A separate live sample at `2026-11-12T04:51:36.679998Z` returned:

- MT5 EURUSD tick epoch: `1794466295`, which UTC epoch conversion renders as
  `2026-11-12T06:51:35Z` (about **+01:59:58** versus the UTC sample).
- MT5 latest completed M5 bar epoch: `1794465900`, which UTC epoch conversion
  renders as `2026-11-12T06:45:00Z`.
- That same bar's OHLC close was `1.10816`. This sample was later than the
  logged breakout row, so it is supporting evidence of the persistent offset,
  not a simultaneous chart screenshot for that earlier bar.

## Root-cause assessment

**Likely mechanism (medium confidence):** MT5's returned times are aligned to
the IC Markets server's GMT+2 clock on this November date, and the connector
then formats the values as UTC. The result is a timestamp label about two
hours later than the corresponding UTC time. This matches both the live tick
and bar observations and the broker's published server-time convention.

**Not conclusively established:** We do not have the MT5 chart display for the
same completed bar. Additionally, MetaQuotes' Python API examples instruct
callers to use UTC datetimes for rate queries and demonstrate epoch-to-date
conversion, describing terminal rate times as UTC. The runtime observation
conflicts with that expectation. The available facts cannot distinguish a
broker/server-time representation, a terminal/server configuration issue, or
another time-source discrepancy with certainty.

The observed offset is not evidence that the connector accidentally applied
the Windows UTC+08:00 timezone: `datetime.fromtimestamp(..., timezone.utc)`
explicitly requests UTC and bypasses local timezone conversion. Nor does an
exact +2-hour observed difference alone establish a DST error. IC Markets
documents a +2/+3 seasonal server clock, and the November sample matches +2,
but the connected chart/server clock was not directly verified.

## Conversion rules until verified

1. Keep raw MT5 epoch values and the original broker/chart timestamps as
   evidence.
2. Treat the connector's `...Z` timestamps as **unverified**, despite their
   UTC formatting. Do not use them to schedule a next-bar entry.
3. Do not hard-code a two- or three-hour correction and do not infer a
   historical offset from the current date. The broker documents seasonal
   GMT+2/GMT+3, so any eventual conversion must be date-aware and confirmed
   against the actual terminal/server convention.
4. The observer's `timestamp` is generated from the computer's UTC clock;
   `bar_timestamp` comes from the MT5 API. They represent different sources
   and must not be conflated.
5. Before time-sensitive demo execution, compare one completed bar's displayed
   MT5 chart time, raw MT5 API epoch/time, Windows local time, and UTC clock
   contemporaneously. Confirm the conversion rule with IC Markets or the
   terminal's documented timestamp semantics, then test it on both a winter
   and daylight-saving date if history is used.

## Sources

- [IC Markets Forex Trading Hours](https://www.icmarkets.com/global/en/trading-hours):
  states that IC server time and charts are GMT+2 or GMT+3 during daylight
  saving; it also notes the account trading system is the authoritative
  schedule source.
- [MetaQuotes Python `copy_rates_range` documentation](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py):
  example creates UTC `datetime` inputs and says this avoids applying a local
  timezone offset.
- [MetaQuotes Python `copy_rates_from_pos` documentation](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesfrompos_py):
  documents bar indexing and sample epoch conversion, but does not state on
  that page that this broker's returned epoch is server-local or UTC.
- [MetaQuotes `MqlTick` structure](https://www.mql5.com/en/docs/constants/structures/mqltick):
  defines `time` as the time of the last price update; the page does not
  identify this connected broker's displayed chart timezone.

## Confidence and demo-readiness decision

- **Local timezone and connector conversion behavior:** High confidence.
- **Observed MT5-vs-UTC offset near +2 hours:** High confidence for the captured
  samples.
- **Broker-server clock as the likely cause:** Medium confidence; strongly
  consistent with IC Markets' published GMT+2/GMT+3 convention.
- **Exact chart/API timezone relationship and seasonal conversion:** Not
  verified.
- **Can signal timing be trusted for demo execution now?** No. The observer's
  timestamp and MT5 bar timestamp are not aligned, and the corresponding
  terminal chart display has not been compared.

**TIMESTAMP_ALIGNMENT_UNRESOLVED**
