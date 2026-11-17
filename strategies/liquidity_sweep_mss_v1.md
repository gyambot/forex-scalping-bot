# Liquidity Sweep + Market Structure Shift V1

Research-only candidate, separate from Breakout Scalping V1 and its demo gate.
This alternative is outside the current one-family charter; this backtest is
not authorization to deploy, replace V1, or create V2. The following choices
are fixed research assumptions, not optimized parameters.

## Input and confirmed pivots

Use EURUSD M5 bid OHLC, ordered by explicit-offset bar-open timestamp. A
five-bar pivot at index `p` is a high strictly above the two preceding and
two following highs, or a low strictly below the corresponding lows. Ties
do not qualify; a bar can be both. Confirm at the close of `p+2` and update
the latest high and low **after** evaluating that bar's sweep and break.
Thus a sweep can only use pivots already confirmed before its own bar.

## Setup and signal

Both a latest confirmed high and low must exist. One pip is `0.0001`.

- **Long sweep:** a bar's low is at least one pip below the latest confirmed
  pivot low and its close is strictly above that low. At that close, freeze
  that low and the latest confirmed pivot high as the structure-break level.
- **Short sweep:** a bar's high is at least one pip above the latest
  confirmed pivot high and its close is strictly below that high. Freeze that
  high and the latest confirmed pivot low as the break level.
- A long (short) signal occurs at the first **later** bar close strictly
  above (below) the frozen structure high (low). Wick-only breaks do not
  qualify. Breaks on the sweep bar cannot trigger an entry.
- Each setup is valid through the next 12 observed bars, inclusive. A new
  same-direction sweep replaces the prior setup after existing breaks are
  evaluated. Long and short setups can coexist. If the same bar sweeps both
  sides, discard both setups and create neither; if both structure breaks
  occur on the same bar, discard both signals. A break consumes its setup
  even if a trade is already open. After a break is evaluated, a new sweep
  on that bar can arm a later setup.
- Signals are determined independently of position state; a signal emitted
  while a position is open is ignored. A position that closes during a bar
  permits a new signal at that bar's close.

These are observed-bar counts, not continuous elapsed time; gaps can span
weekends or missing data.

## Execution and risk

Use existing V1 backtest execution conventions without modifying V1:
one active position; enter on the next available bar's open at bid plus
1 pip for long, bid for short; 10-pip initial stop and 20-pip target from
entry. Long exits use bid, short exits bid plus 1 pip. Stop takes precedence
if both levels are hit in one OHLC bar; adverse stop gaps fill at the open
and favorable target gaps at target. A remaining open position is closed
at the final close, with spread for shorts. A final-bar signal with no next
bar cannot enter. There is no modeled commission, slippage, financing,
partial fill, equity or compounding.

All strategy rules use completed bars only; pivot and sweep/structure
timestamps are preserved in candidate trade outputs for audit. The OHLC
model cannot establish intrabar event order or real broker fills. Gap losses
can exceed the initial 1R risk and realized reward/risk need not equal 2:1.
