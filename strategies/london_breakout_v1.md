# London Session Breakout V1: Research Candidate

This isolated candidate does not change Breakout Scalping V1 or the demo
gate. It adds multiple specified changes relative to V1 and is not an
approved V2 or a single-hypothesis promotion test.

## Signals and session

Use EURUSD M5 bid OHLC with strictly ordered explicit-offset source bar-open
timestamps. The session is 07:00 inclusive to 11:00 exclusive in
`Europe/London`, using IANA daylight-saving transitions. Evaluate at the
completed signal candle's **nominal close**, five elapsed minutes after its
open. Convert the source's explicit offset to a real instant before conversion
to London; do not relabel UTC data as broker time. The existing broker-time
parser validates explicit offsets; MT5 broker-wall-time labels rely on the
operator-configured offset and its unverified epoch convention. These
historical files carry UTC source timestamps. Windows requires the IANA
timezone database to be available to Python.

EMA50 and EMA200 use close, seeded by the first close and updated recursively
with alpha `2/(period+1)`. Require 200 bars; first eligible index is 199.
At each completed bar, exclude the current bar and take the highest high and
lowest low of the preceding 12 observed candles. Long requires session active,
EMA50 > EMA200 and close strictly above that high. Short requires session
active, EMA50 < EMA200 and close strictly below that low. Equality gives no
signal. Observed-bar windows can cross weekends and missing data.

## ATR and execution

ATR14 is the simple mean of the last 14 true ranges, including the signal
bar. True range is max(high-low, abs(high-previous close),
abs(low-previous close)); the first bar uses its own close as previous close.
Reject nonpositive ATR. Freeze ATR at signal close; the initial stop is 1 ATR
from actual simulated entry and target is 2 ATR from entry.

Use the existing historical execution conventions: one position; ignore
signals while open, but allow a signal at the close of an exit bar. Enter
at the next **available** bar open, even across a gap or outside the session,
long at bid plus 1 pip, short at bid. Long exits use bid; short exits bid plus
1 pip. Stop takes priority when both levels are touched; adverse stop gaps
fill at open, favorable target gaps at target. An open final position closes
at final close; no entry for a final-bar signal. Pip = 0.0001. Per-trade R is
signed actual price movement divided by that trade's initial ATR, not the
V1 fixed-stop denominator.

No equity sizing, commission, slippage, financing, partial fills or broker
tick rounding are modeled. Exit timestamps and five-minute-per-observed-bar
hold times follow the existing helper and are approximations across gaps.
