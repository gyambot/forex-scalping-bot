# Live V1 Signal Observation Report

- Observations logged: 2 completed bars
- Observation window (broker clock): 2026-11-12T06:44:47.966331+02:00 to 2026-11-12T06:49:28.728585+02:00
- MT5-reported bar timestamp range: 2026-11-12T06:35:00+02:00 to 2026-11-12T06:40:00+02:00
- Observed LONG signals: 1
- Observed SHORT signals: 0
- LONG:SHORT ratio: 1:0
- Signal frequency: 1/2 observed bars (50.00%)
- Bars without a signal: 1

## Periods without signals

Each period below is a contiguous run of logged M5 bars. Gaps in observation are not treated as no-signal periods.

- 2026-11-12T06:35:00+02:00 to 2026-11-12T06:35:00+02:00: 1 completed bars

## Logging anomalies

- row 1: bar close time differs from observation clock by -288 seconds under the configured broker-time contract
- row 2: bar close time differs from observation clock by -269 seconds under the configured broker-time contract

## Interpretation limits

- This is signal observation only, not trade-performance analysis.
- The sample is too small to assess signal frequency as stable or representative.
- MT5 bars are requested at position 1 or older, so the forming bar is excluded. API wall-clock fields are retained and tagged with the configured broker offset. Differences over 120 seconds from the expected bar close are reported as anomalies.
- Signal observations do not count toward the completed-demo-trade gate. Demo trades remain 0 / 100 and V2 remains blocked.
