# Demo Execution Readiness — Trade #1

> **Status update:** This UTC-gated assessment is historical. The project
> subsequently adopted the explicit-offset broker-time contract described in
> [BROKER_TIME_CONTRACT.md](./BROKER_TIME_CONTRACT.md). That migration
> supersedes the requirement to prove UTC conversion; it does not authorize
> an order or bypass the remaining demo execution checklist.

## Conclusion

**BLOCKED_PENDING_TIMESTAMP_EVIDENCE**

The accumulated evidence is **not sufficient to begin Demo Trade #1**. The
MT5 API tick and bar epochs repeatedly convert to times about two hours ahead
of the contemporaneous UTC clock. The connector renders those epochs with a
`Z` suffix, while the observer separately records local UTC. The available
reports do not contain a visual MT5 chart timestamp for the same completed
bar, so it remains unknown whether the API epoch represents UTC, broker
server/chart time, or another offset.

The broker's published GMT+2/GMT+3 server-time convention makes a broker-time
offset plausible, but does not prove the actual chart/API relationship for
this terminal. Applying a guessed offset could shift the signal-close and
next-bar entry times; using the current `Z` value as UTC could also make a
closed bar appear to be in the future. Either interpretation can invalidate
V1's next-M5-bar timing. The project's execution checklist and broker setup
requirements require timestamp conversion to UTC to be verified before
execution.

## Evidence reviewed

- [Timestamp verification report](./TIMESTAMP_VERIFICATION_REPORT.md) records
  the repeated approximately +02:00 API-vs-UTC discrepancy and explicitly
  leaves the chart timezone and conversion unresolved.
- [Final timestamp verification](./TIMESTAMP_FINAL_VERIFICATION.md) adds a
  contemporaneous raw API epoch, OHLC, Windows local clock, and UTC clock.
  It explicitly records that no screenshot or human-read chart label for the
  same bar was captured.
- [Signal observation report](./SIGNAL_OBSERVATION_REPORT.md) contains one
  raw LONG breakout in a two-bar sample, but both observed rows have
  approximately two-hour timestamp anomalies. This is a raw signal
  observation, not verified evidence that its next-bar execution window was
  correctly identified.
- [Broker integration options](./BROKER_INTEGRATION_OPTIONS.md) requires
  identifying the signal candle timestamp convention and verifying UTC
  conversion before the first order; it states that the repository is not
  ready to place broker orders until required checks are complete.
- [Demo gate status](./DEMO_GATE_STATUS.md) remains **0 / 100** and
  **BLOCKED**. The operational trade log currently contains no completed
  positions.

## Required evidence to clear this blocker

Using one **same completed EURUSD M5 bar**, capture and retain:

1. A screenshot showing the MT5 chart's timestamp label and that bar's OHLC.
2. The raw MT5 Python `rate['time']` epoch and OHLC for that identical bar.
3. Windows local time and timezone, and a contemporaneous UTC clock reading.
4. The resulting calculations showing whether chart time equals API time,
   UTC, or broker server time, with the date-appropriate GMT+2/GMT+3
   convention confirmed by the broker or authoritative terminal evidence.
5. A verified conversion rule, including how it behaves across the broker's
   daylight-saving transition if historical bars are used.

Do not hard-code a two- or three-hour correction based only on the current
observations. After alignment is demonstrated, re-run the per-signal timing
checks in the [demo execution checklist](./DEMO_EXECUTION_CHECKLIST.md) and
update the timestamp verification decision before considering execution.

## Scope and safeguards

This decision does not change frozen V1, introduce filters, authorize
execution, or alter the demo counter. No trade should be inferred from the
observed LONG row while the signal timestamp and next-bar timing remain
unverified. Do not enter late to compensate for the discrepancy. No V2 work
is authorized.
