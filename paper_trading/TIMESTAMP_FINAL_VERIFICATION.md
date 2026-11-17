# MT5 Terminal Clock — Final Verification

> **Status update:** This report remains the evidence record for the earlier
> UTC-alignment investigation. Its same-bar visual comparison was not
> completed in that session. The project later adopted an explicit-offset
> broker-time contract; see [BROKER_TIME_CONTRACT.md](./BROKER_TIME_CONTRACT.md).
> The historical UTC conclusion no longer blocks the contract migration, but
> this note does not authorize demo orders.

## Result

The requested visual comparison could not be completed because Computer Use
is disabled in this unattended session. The MT5 desktop chart and its clock
were not visible. No chart timestamp or screenshot is fabricated. A fresh API
sample again shows tick/bar epoch values about two hours ahead of Windows
local-derived UTC. This supports a persistent offset in the returned values,
but does not prove whether the chart displays those same values or establish a
safe conversion.

Do not use the reported API bar timestamps to time demo entries until the
visual same-bar comparison is completed and the time basis is confirmed.

## Contemporaneous sample

Captured from the connected `ICMarketsSC-Demo` terminal on 2026-11-12. Local
time and UTC were sampled immediately before/after the API calls.

| Source | Reading |
|---|---|
| Windows local time before API read | `2026-11-12T12:54:02.940408+08:00` |
| UTC before API read | `2026-11-12T04:54:02.940445+00:00` |
| Windows local time after API read | `2026-11-12T12:54:02.940895+08:00` |
| UTC after API read | `2026-11-12T04:54:02.940894+00:00` |
| Windows timezone | `Taipei Standard Time`, UTC+08:00 |
| MT5 account server | `ICMarketsSC-Demo` |
| MT5 terminal build | `6306` |
| MT5 EURUSD tick epoch | `1794466443` |
| Tick epoch rendered as UTC | `2026-11-12T06:54:03Z` |
| Difference from UTC sample midpoint | approximately `+02:00:01` |
| MT5 latest completed M5 bar epoch | `1794465900` |
| Bar epoch rendered as UTC | `2026-11-12T06:45:00Z` |
| Same bar OHLC | Open `1.10791`, high `1.10818`, low `1.10789`, close `1.10816` |
| MT5 chart timestamp for this same bar | **Not captured; chart unavailable in this session** |

The sampled bar has an MT5 epoch corresponding to a nominal 06:45 UTC open
and 06:50 UTC close if the epoch is true UTC. At the contemporaneous UTC sample
of approximately 04:54, that nominal close would be about 1 hour 56 minutes
in the future. If the broker/server wall time is UTC+2, the displayed server
bar label would instead be 08:45, closing at 08:50 server time, which is
consistent with local UTC+2. This is a plausible explanation, not visual
confirmation.

The earlier observer log provides separate supporting samples: bar labels
`06:35Z` and `06:40Z` were observed by the local UTC clock at
`04:44:47Z` and `04:49:28Z`. The row at `06:40Z` was a raw LONG signal with
close `1.10791` and channel level `1.10784`. It is not the same bar as the
fresh sample above and must not be presented as a same-bar chart comparison.

## Fresh API and clock sample

Captured at 2026-11-12 12:56:07 local time on the same connected terminal:

| Source | Reading |
|---|---|
| Windows local before | `2026-11-12T12:56:07.822563+08:00` |
| UTC before | `2026-11-12T04:56:07.822600+00:00` |
| Windows local after | `2026-11-12T12:56:07.822674+08:00` |
| UTC after | `2026-11-12T04:56:07.822673+00:00` |
| Raw completed-bar epoch | `1794466200` |
| Epoch rendered as UTC | `2026-11-12T06:50:00Z` |
| Same completed bar OHLC | Open `1.10816`, high `1.10822`, low `1.10799`, close `1.10800` |
| Raw tick epoch | `1794466567` |
| Tick epoch rendered as UTC | `2026-11-12T06:56:07Z` |
| Tick epoch minus UTC sample midpoint | `+7199.177 seconds` |
| Chart timestamp for this same OHLC bar | **Not captured; chart unavailable** |

This bar is different from the one in the preceding sample. It cannot be
compared against that sample's hypothetical chart label. The API bar epoch
converts to 06:50Z; if treated as true UTC its nominal M5 close is 06:55Z,
nearly two hours ahead of the actual UTC sample. That is consistent with—but
does not prove—a +2-hour broker/server wall-time interpretation.

## Visual evidence

No visual evidence was captured. Specifically, there is no verified screenshot
or human-read chart label for either sampled completed bar. Therefore this
report cannot determine whether the connected terminal chart currently
displays GMT+2 or GMT+3, or whether the API timestamp exactly matches the
chart label.

IC Markets' published trading-hours page states that its server time and
charts are GMT+2, or GMT+3 during daylight saving. November 12 is consistent
with the broker's standard-time GMT+2 schedule, but that public statement does
not substitute for reading the connected chart clock. The precise terminal
display in this account remains unverified.

## Interpretation of the API and connector

- The MT5 Python connector obtains ticks via `symbol_info_tick()` and M5 bars
  via `copy_rates_from_pos(..., start_pos=1, ...)`. Position 1 or older
  excludes the forming bar.
- `mt5_price_feed.py` converts tick and bar epoch values with
  `datetime.fromtimestamp(epoch, timezone.utc)` and labels them with `Z`.
  This is correct only if those values are true UTC Unix epochs.
- `signal_observer.py` separately records its `timestamp` from the computer's
  UTC clock and stores the converted API bar time in `bar_timestamp`.
- The observed API-to-UTC delta of approximately +2 hours in both ticks and
  bars is not caused by converting through the Windows Taipei timezone:
  conversion explicitly passes `timezone.utc`.
- MetaQuotes' Python `copy_rates_range` example uses timezone-aware UTC input
  datetimes to avoid local-time offset effects. That documentation supports
  UTC handling for query arguments, but does not resolve why this server's
  returned epochs convert to a time two hours ahead of the actual UTC sample.
- IC Markets documents GMT+2/GMT+3 server/chart time. The runtime offset is
  consistent with broker server time being represented or interpreted as a
  UTC epoch. It does not by itself prove a DST shift or prove API broker-time
  semantics.

## Exact comparison required to resolve

When an attended session is available, capture one screenshot of the MT5
EURUSD M5 chart that shows the **same bar's** time label and OHLC values. At
the same moment, record:

1. The chart's displayed bar label/time and the terminal clock.
2. Raw API `rate['time']` epoch and its OHLC; do not rely only on the
   connector's `Z` string.
3. Windows local time and timezone.
4. UTC time sampled from the same computer.
5. The broker-confirmed timezone and seasonal/DST convention for
   `ICMarketsSC-Demo`.

Compare chart OHLC to the API OHLC to identify the same bar, then compare its
chart label to the API epoch and UTC. Do not apply a guessed `-2h` or `-3h`
correction. Keep the raw values and screenshot as evidence, and verify the
rule for both GMT+2 and GMT+3 dates before using historical timestamps across
the DST boundary.

## Sources and confidence

- Runtime Windows clock/timezone and MT5 API sample above: high confidence
  for those observed values.
- Connector's UTC conversion behavior: high confidence from source inspection.
- IC Markets published server/chart timezone convention:
  [Forex Trading Hours](https://www.icmarkets.com/global/en/trading-hours).
- MetaQuotes time input guidance:
  [Python `copy_rates_range`](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py).
- MetaQuotes tick structure:
  [MqlTick](https://www.mql5.com/en/docs/constants/structures/mqltick).
- API representing broker wall time as a UTC-like epoch: plausible, medium
  confidence only.
- Actual MT5 chart time for this bar, API-to-chart mapping, and DST behavior:
  unverified.

No strategy rules, signal logic, orders, or trades were changed or created.

TIMESTAMP_ALIGNMENT_UNRESOLVED
