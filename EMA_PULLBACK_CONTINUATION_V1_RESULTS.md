# EMA Pullback Continuation V1 Results

## Historical results

| Metric | 2025 | 2026 Jan–Oct |
|---|---:|---:|
| EURUSD M5 bars | 73,683 | 60,551 |
| Trade count | 3,319 | 2,819 |
| Win rate | 22.15% | 20.01% |
| Net profit | -3,468.8078 pips | -2,831.2720 pips |
| Profit factor | 0.6521 | 0.5746 |
| Expectancy / average trade | -1.0451 pips | -1.0044 pips |
| Average R | -0.3381 R | -0.4015 R |
| Maximum closed-trade drawdown | 3,478.2864 pips | 2,845.7720 pips |
| Average hold | 22.19 minutes | 21.78 minutes |
| Trades per active data day | 10.64 | 10.88 |

Both periods show negative expectancy and profit factor below one under the
chosen execution model. In 2025 long/short counts were 1,653/1,666 and net
P&L was -2,158.8711/-1,309.9367 pips. In 2026 the counts were 1,210/1,609
and net P&L was -1,169.5221/-1,661.7499 pips. These breakdowns are
descriptive, not evidence that a different parameter choice would succeed.

## Assumptions

The complete fixed rules are in
[ema_pullback_continuation_v1.md](strategies/ema_pullback_continuation_v1.md).
The interpretation uses same-candle EMA50 retracement and bullish/bearish
confirmation with EMA50/EMA200 trend direction. The stop and target are
respectively 1 and 2 times simple ATR14 sampled at signal close. Entry is at
the next available M5 open with a fixed one-pip spread; the existing OHLC
execution conventions are reused. Per-trade R is based on that trade's own
initial ATR distance. No parameter sweep was performed.

## Limitations

The fixed spread and absence of commission, slippage, financing and broker
constraints do not represent actual execution costs. OHLC cannot determine
intrabar order; the model uses stop-first. Gaps can produce losses greater
than 1R and next-available-bar entries can occur after missing data or
weekends. Hold time counts observed bars, not actual elapsed time. Maximum
drawdown is closed-trade cumulative pips, not percentage or equity drawdown.
CAGR is not modeled because there is no equity, position sizing or
compounding model. See [data provenance](data/README.md) for missing data
and source limitations.

This is a research candidate outside the current one-family charter, not
Breakout Scalping V1 or V2. The 2026 run is a separate historical period,
not prospective validation. Negative results reject this specified
prototype for demo evaluation; they do not prove all EMA pullback methods
fail.

## Verification and reproduction

`python -m unittest discover -s tests` passed 34 tests, including four
candidate tests for long/short signals, warm-up, causal prefixes, next-open
entry and variable ATR risk including gap exits. Historical prefixes of
1,000, 10,000 and 30,000 bars matched the full signal series; every output
trade's R was checked against its own entry-to-stop distance.

```powershell
python -m candidate_strategies.backtest_ema_pullback_continuation_v1 --input data\eurusd_m5_2025.csv --output-dir backtests\ema_pullback_continuation_v1\2025
python -m candidate_strategies.backtest_ema_pullback_continuation_v1 --input data\eurusd_m5_2026_01_10.csv --output-dir backtests\ema_pullback_continuation_v1\2026
```

Each output directory contains the trade CSV, data hash and metrics JSON.

**NOT_VIABLE_AFTER_BACKTEST**
