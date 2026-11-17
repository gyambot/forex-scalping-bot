# Breakout Scalping V1 — Demo Execution Checklist

Use before each demo session and before each signal. A failed safety or data
check means **pause**: do not improvise a strategy rule. Record the incident
and resume only after the issue is resolved.

## Session preflight

- [ ] Account/server is explicitly identified as **DEMO**, not live.
- [ ] Broker and platform are connected; quote/order status is current.
- [ ] If the execution terminal depends on a VPS, the VPS is connected,
      responsive, synchronized, and has no pending restart/update.
- [ ] EURUSD (or the broker-confirmed EURUSD symbol mapping) is available and
      tradable.
- [ ] M5 chart/feed is selected; the configured broker offset matches the
      terminal's displayed broker clock.
- [ ] Recent M5 candles are complete, in order, and not stale or duplicated.
- [ ] Bid and ask are visible; current spread is captured for the signal record.
- [ ] Order-entry route and attached stop/target behavior are available and
      understood; no rejected or orphaned order remains.
- [ ] Demo balance/currency, contract size, pip size, minimum/step volume, and
      approved demo size match the documented setup.
- [ ] One-position limit is clear; no V1 position is currently open.
- [ ] Trade log is writable and backed up; unique trade ID is ready.
- [ ] Clock synchronization, logging, and broker-history export are available.
- [ ] No planned data/platform maintenance, account reset, or unresolved
      incident affects this session.

## Per-signal checks

- [ ] Current M5 bar has closed; signal time is recorded in broker time with
      an explicit offset.
- [ ] Signal is a strict close above the prior 20 completed-bar high or below
      the prior 20 completed-bar low; the signal bar is excluded from that
      range.
- [ ] Direction and signal values are recorded; no discretionary filter or
      alternate signal has been applied.
- [ ] No V1 position is active; a pending prior order has been reconciled.
- [ ] Next M5 bar entry is available. If missed, do not enter late and label it
      as the original entry; record the missed/late event separately.
- [ ] Actual spread/quotes are recorded. This is execution evidence, not a new
      V1 strategy filter.
- [ ] Intended stop and target match frozen V1 distances from actual entry;
      broker accepts both protective orders.
- [ ] Actual fill, timestamp, volume, broker order/position reference, and
      attached protection are confirmed immediately after entry.

## Position monitoring and close

- [ ] Do not add, hedge, trail, widen, tighten, or manually alter the V1
      position for strategy reasons.
- [ ] Monitor order/connection state sufficiently to detect disconnects,
      rejected protection, or an uncertain position.
- [ ] On closure, confirm the broker position is flat and capture actual exit
      time, price, reason, costs, and statement/order reference.
- [ ] Reconcile actual fills and costs with the capture record; preserve any
      discrepancy rather than silently editing it away.
- [ ] Mark `completed=true` only when the position is fully closed and the
      record is complete and reconciled.

## Session close

- [ ] Confirm no open or pending position/order remains.
- [ ] Reconcile broker history against all session records, including
      rejected, missed, cancelled, and partial orders.
- [ ] Save the raw broker export and a copy of the updated trade log.
- [ ] Check unique trade IDs and completed-trade count; count only eligible
      completed demo positions toward 100.
- [ ] Record connectivity, quote, order, and rule-compliance incidents.
- [ ] Produce or update metrics only from validated, completed records; never
      mix historical trades into the demo gate count.

## Incident stop conditions

Pause new activity and reconcile immediately if:

- Account identity is uncertain or not demo.
- Quotes/bars are stale, out of sequence, or the configured broker offset is
  missing or inconsistent with the terminal clock.
- Connection is lost or order/position state is unknown.
- Stop/target is rejected, missing, or inconsistent with the frozen rule.
- A duplicate position or unintended live order may exist.
- Trade logging is unavailable or actual fills/costs cannot be captured.

Document the time, affected order/trade IDs, observed facts, resolution, and
whether any position remained open. Do not count an unverified or incomplete
position toward the 100-trade gate.
