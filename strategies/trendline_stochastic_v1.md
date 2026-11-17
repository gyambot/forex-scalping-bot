# Trendline Stochastic V1: Research Prototype

This is a separate research candidate, not Breakout Scalping V1, V2, or a
replacement for the baseline. The transcript was unavailable; all rules below
are explicitly chosen assumptions, not a reconstruction of its wording.
They are fixed for this run, not optimized.

## Input and indicators

EURUSD M5 bid OHLC, chronological explicit-offset bar-open timestamps. All
signals are decided at completed-bar close. Bar indices count observed bars,
including across data gaps. EMA200 is seeded with the first close and
recursively updated using alpha `2/201`; no signal before bar index 199.
ATR14 is the simple mean of the last 14 true ranges; true range is the
maximum of high-low and the absolute distances from prior close, with the
first bar's own close used as its prior close. The zone width is `0.25 ×
ATR14`, evaluated at the decision bar close.

Stochastic is 14,3,3: raw %K uses current and prior 13 bars' high/low,
slow %K is a 3-value simple mean of raw %K, %D a 3-value simple mean of
slow %K. On a zero high-low range, reset both smoothing windows and require
them to refill. A bullish cross is prior K <= D and current K > D; bearish
is prior K >= D and current K < D. Warm-up must be complete.

## Pivots and trendlines

A 5-bar pivot high (low) must be strictly higher (lower) than both preceding
and both following bars; ties fail. A pivot is available only at the close
of its second following bar. Keep the two most recent confirmed pivot highs
and lows independently. Join each pair by bar index and extend indefinitely;
support uses lows and resistance uses highs. Require positive slope for
support and negative slope for resistance. Do not rank or filter by touches.
Line value at decision index `i` is `y2 + (y2-y1)/(x2-x1)*(i-x2)`.
EMA direction uses decision close > EMA for long and < EMA for short;
equality yields no trade. No line exists until two pivots are confirmed.

## Four setups

All conditions apply to the same decision bar. A breakout takes priority over
a bounce; long precedes short in each class. One signal maximum per bar.
`line_previous` is the current line evaluated at index `i-1`, including when
a new line was confirmed on the current bar; the current ATR zone is used for
both comparisons.

- **Bounce long:** close > EMA; support slopes up; low is inside
  `[support-zone, support+zone]`; close > support+zone; bullish stochastic
  cross and current K < 20.
- **Bounce short:** close < EMA; resistance slopes down; high is inside
  `[resistance-zone, resistance+zone]`; close < resistance-zone; bearish
  cross and current K > 80.
- **Breakout long:** close > EMA; resistance slopes down; previous close <=
  `line_previous+zone`; current close > resistance+zone; K > D.
- **Breakout short:** close < EMA; support slopes up; previous close >=
  `line_previous-zone`; current close < support-zone; K < D.

## Execution and risk

One position at a time; while open, signals are ignored. Enter at the next
available bar's open, including after a data gap: long at bid open plus
1 pip, short at bid open. Initial stop 10 pips from entry; target 20 pips
from entry (gross 2R), with pip = 0.0001. Existing V1 execution helpers
are reused without modification: long exits on bid, short exits on bid plus
1 pip; stop wins if both touched in one bar; adverse stop gaps fill at
open, favorable target gaps at target. An open final position is closed at
the final close with the modeled spread for short. No commission, slippage,
financing, equity, compounding or partial fills are modeled. Hold duration
is an estimate in observed M5 bars, not actual elapsed gap time. CAGR is
not defined in this normalized pip/R model.

The line, filter, stop, and threshold assumptions are not validated against
the absent transcript. Real fills and spread variation may differ, and
historical results are not permission to trade.
