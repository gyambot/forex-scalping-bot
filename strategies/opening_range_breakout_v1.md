# Opening Range Breakout V1 — research candidate

No approved ORB specification was located. The following is an explicit,
fixed interpretation for evidence collection, not a claim of prior approval.
It is isolated from Breakout Scalping V1 and the demo executor.

- EURUSD bid OHLC M5. Convert explicit-offset timestamps to Europe/London,
  including IANA daylight-saving changes.
- Opening range is the twelve complete, consecutive bars opening from 07:00
  through 07:55 London. Skip days with any missing range bar.
- From 08:00 until 11:00 London, bar-open time, the first completed candle
  closing strictly above the range high signals long; strictly below the
  range low signals short. At most one signal per London date.
- Enter at next available bar open, even across a gap. Stop 10 pips, target
  20 pips from entry; one position. One-pip fixed spread, stop-first OHLC
  priority, adverse gap fills and final close follow the existing historical
  execution model. Signals while a position is open are not entered.
- No commission, slippage, financing or sizing. Nominal bar close is the
  decision time; missing data can delay the next-available entry.

The fixed range, time window and risk levels are assumptions, not fitted
parameters. This is exploratory; it does not change the baseline or gate.
