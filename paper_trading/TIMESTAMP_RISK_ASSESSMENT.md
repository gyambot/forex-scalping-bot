# Timestamp Risk Assessment — Breakout Scalping V1

> **Status update:** The assessment below records the prior UTC-timing
> decision. The project subsequently migrated the live data contract to
> explicit-offset broker time; see
> [BROKER_TIME_CONTRACT.md](./BROKER_TIME_CONTRACT.md). V1 price rules are
> unchanged.

## Conclusion

**BLOCKER_REMAINS**

The observed approximately +2-hour timestamp difference does not, by itself,
change the arithmetic of V1's breakout comparison or its price distances.
However, the available evidence does not establish that the difference is
only a uniform relabeling, that chart bars and API bars have matching
timestamps for the same OHLC, or that a live signal is acted on at the
correct next M5 bar. The unresolved timing affects execution readiness, so
the timestamp blocker cannot be removed or accepted as a known residual risk
on the current evidence.

## Assessment

### 1. Does V1 require absolute UTC accuracy?

For the **price-only breakout calculation**, not inherently: the rule compares
a completed bar's close against the high and low of the preceding 20 completed
bars. A constant shift of every timestamp, with unchanged OHLC values and
bar order, would not change that comparison.

For the **specified data and live workflow**, UTC accuracy still matters.
V1's specification requires chronological, unique M5 bars on five-minute
boundaries with ISO-8601 UTC timestamps. It schedules entry at the next M5
bar open. Correctly identifying when a bar closed and which next bar is
eligible therefore requires a verified relationship between API timestamps,
actual bar completion, and wall-clock time. An unverified timestamp cannot
be treated as harmless merely because signal arithmetic uses prices.

### 2. Does V1 only require completed-bar sequencing?

Signal computation requires the correct sequence of completed bars, the
correct 20-bar lookback excluding the signal bar, and the signal bar's close.
It does not use a time-of-day filter. But live execution timing requires more
than ordering alone: it must know that the bar is complete and identify the
next M5 entry opportunity without acting early or late.

### 3. Are MT5 chart bars and MT5 API bars internally consistent?

**Not established.** The API observations show bar epochs roughly two hours
ahead of the contemporaneous UTC clock, and tick epochs show a similar
offset. The reports have no visual chart timestamp and OHLC comparison for
the same completed bar. Thus they do not prove that the API and chart show
the same bar labels or that their OHLC and boundaries align.

The existing samples also do not establish whether the same mapping holds
across the broker's GMT+2/GMT+3 seasonal change. A chart/API same-bar match
and authoritative time-basis evidence remain outstanding.

### 4. Would a +2-hour offset change breakout detection?

If it is **only a constant timestamp relabeling** and all bar OHLC values,
bar boundaries, ordering, and completion status are unchanged, then **no**:
the strict close-above-prior-high / close-below-prior-low test produces the
same raw breakout result.

That condition has not been verified for this terminal. If the timestamp
misinterpretation causes the observer to select a forming bar, miss a
completed bar, use a different 20-bar window, or associate a signal with the
wrong M5 boundary, the signal result or the time at which it is recognized
can differ. The current evidence cannot rule those cases out.

### 5. Would a +2-hour offset change stop or target placement?

A timestamp shift alone does not change V1's price distances: the stop and
target are 10 and 20 pips from the actual entry price, respectively. If the
same entry fill is used, these relative distances are unchanged by how its
timestamp is labeled.

But V1 enters at the **next M5 bar open**. If the time discrepancy causes
entry at the wrong bar or after the intended opportunity, the actual entry
price can differ; the corresponding absolute stop and target prices then
differ as well. This does not alter V1's fixed distances, but it can alter
the trade that is entered and its outcome. No order has been placed, and the
current timestamp evidence does not verify next-bar timing.

## Evidence basis and disposition

- [Timestamp verification report](./TIMESTAMP_VERIFICATION_REPORT.md) records
  the approximately +2-hour API-vs-UTC discrepancy and says the API/chart
  time basis is unresolved.
- [Final timestamp verification](./TIMESTAMP_FINAL_VERIFICATION.md) records
  contemporaneous raw epochs, OHLC, and local/UTC readings, but no visual
  chart timestamp for the same bar.
- [Blocker resolution plan](./TIMESTAMP_BLOCKER_RESOLUTION_PLAN.md) defines
  the missing same-bar chart/API/clock comparison and broker/API time-basis
  confirmation; those have not been collected.
- [Demo execution readiness](./DEMO_EXECUTION_READINESS.md) keeps Trade #1
  blocked pending that evidence.
- The frozen [V1 specification](../strategies/breakout_scalping_v1.md)
  defines a 20-completed-bar breakout, next-M5-open entry, and fixed
  10/20-pip stop/target distances.

Therefore the offset is **not shown to alter pure price-based detection under
a uniform-relabeling assumption**, but that assumption and live bar timing
are not verified. Keep timestamp-dependent demo execution blocked until the
same-bar API/chart mapping and correct completed-bar/next-bar timing are
demonstrated. This assessment changes no strategy rules and authorizes no
trades.

BLOCKER_REMAINS
