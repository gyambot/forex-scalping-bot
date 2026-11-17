# EMA Pullback Continuation V1

Research-only candidate, separate from Breakout Scalping V1 and its study
gate. This strategy is outside the present one-family project charter; this
backtest does not authorize deployment, replace V1, or create V2.

## Signal assumptions

Use EURUSD M5 bid OHLC with strictly ordered explicit-offset bar-open
timestamps. At each completed bar, EMA50 and EMA200 are calculated from
closes, seeded with the first close and recursively updated with alpha
`2/(period+1)`. Require at least 200 bars; the first eligible index is 199.

Interpret a retracement and confirmation as occurring on the same candle:

- **Long:** EMA50 > EMA200, the candle low is strictly below the current
  EMA50, the candle close is strictly above EMA50, and close > open.
- **Short:** EMA50 < EMA200, the candle high is strictly above the current
  EMA50, the candle close is strictly below EMA50, and close < open.

All comparisons are strict; doji and equality produce no signal. This
same-candle rule is a chosen interpretation, not a claim that other
multi-candle retracements are equivalent.

## ATR and execution

ATR14 is the simple average of the latest 14 true ranges, including the
signal bar. True range is the maximum of high-low and the absolute distance
of each extreme from the preceding close; for the first bar, use its own
close. A nonpositive ATR produces no signal. Capture ATR at signal close,
not the entry bar, and hold it fixed: stop is 1 ATR from entry and target is
2 ATR from entry, in the direction of the trade. A stop or target at a
nonpositive price is an error.

Use the existing V1 OHLC execution conventions: one open position, ignore
signals while open, and allow a new signal on a closing bar. Enter next
available bar at bid open plus one pip for long, bid open for short. Long
exits use bid; short exits use bid plus one pip. Stop takes precedence when
both levels are touched; adverse stop gaps fill at the opening price and
favorable target gaps at target. Final positions close at the last close;
the final bar's signal cannot be filled. Position prices are not rounded to
broker ticks; there are no commission, slippage, financing or partial fills.

Pip P&L uses the existing backtest calculation. Each trade's R is its signed
unrounded price movement divided by its own initial ATR risk, not the
existing V1 helper's fixed 10-pip denominator. This is normalized P&L, not
an account return; no position-size or equity model is assumed.

Bar windows count observed bars even across data gaps. The existing helper
uses the next observed timestamp as the exit timestamp and counts five
minutes per held bar; hold time and intrabar ordering are therefore
approximations, not a tick-level simulation.
