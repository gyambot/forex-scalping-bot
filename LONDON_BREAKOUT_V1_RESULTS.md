# London Session Breakout V1: Historical Results

## Results

| Metric | 2025 | 2026 Jan–Oct |
|---|---:|---:|
| EURUSD M5 bars | 73,683 | 60,551 |
| Trade count | 738 | 600 |
| Win rate | 25.75% | 19.00% |
| Profit factor | 0.7486 | 0.5388 |
| Expectancy / average trade | -0.8312 pips | -1.1443 pips |
| Net profit | -613.4288 pips | -686.5716 pips |
| Average R | -0.2277 R | -0.4301 R |
| Maximum closed-trade drawdown | 623.0431 pips | 686.5716 pips |
| Average hold | 19.23 minutes | 14.78 minutes |
| Trades per active data day | 2.37 | 2.32 |

| Period / direction | Trades | Win rate | Profit factor | Expectancy | Net pips | Average R | Max drawdown |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2025 long | 405 | 28.15% | 0.8652 | -0.4348 | -176.0788 | -0.1556 | 215.0500 |
| 2025 short | 333 | 22.82% | 0.6143 | -1.3134 | -437.3500 | -0.3153 | 463.5715 |
| 2026 long | 253 | 18.97% | 0.4934 | -1.2757 | -322.7638 | -0.4308 | 327.0210 |
| 2026 short | 347 | 19.02% | 0.5727 | -1.0484 | -363.8078 | -0.4296 | 369.5791 |

Directional drawdown is calculated separately for each direction, not
additive to the combined drawdown. Both periods have negative expectancy
and profit factor below one under the modeled assumptions.

## Assumptions and limitations

The [strategy specification](strategies/london_breakout_v1.md) defines
the exact rules: London 07:00–11:00 at signal-bar close with daylight saving,
EMA50/200, previous 12 completed bars, and 1/2 times simple ATR14 sampled
at signal close for the stop/target. Entry is next available open, which can
be outside the session after a gap. Per-trade R uses the actual initial ATR
distance. One-pip fixed spread is modeled, but not commission, slippage,
financing, equity, position sizing or broker tick rounding.

OHLC cannot determine intrabar order; stop-first is assumed. Gap losses can
exceed 1R, and hold time counts observed bars rather than elapsed time. The
data have gaps and excluded source dates; see [data provenance](data/README.md).
Maximum drawdown is closed-trade pips, not equity or percentage drawdown.
CAGR is not supported without an equity and compounding model.

This is a fixed exploratory candidate, not an optimized strategy or a
prospective validation. Because the session, range length, trend filter and
ATR risk differ from Breakout Scalping V1 simultaneously, these results
cannot establish that the session restriction alone improves expectancy.
The candidate does not change V1, demo execution or the study gate.

## Verification and reproduction

The complete `tests` suite passed 38 tests, including four candidate tests
for winter/summer and offset session boundaries, both breakout directions,
warm-up, prefix causality, next-open entry and ATR-risk gap handling.
The actual 2025 signal prefixes at 1,000, 10,000 and 30,000 bars matched
the full run. Each recorded trade in both periods was checked for an
in-session signal close and its own entry-to-stop R. A repeat 2025 run
produced byte-identical trade and metrics files.

```powershell
python -m candidate_strategies.backtest_london_breakout_v1 --input data\eurusd_m5_2025.csv --output-dir backtests\london_breakout_v1\2025
python -m candidate_strategies.backtest_london_breakout_v1 --input data\eurusd_m5_2026_01_10.csv --output-dir backtests\london_breakout_v1\2026
```

The output directories contain trade CSVs, directional metrics, input hashes
and data ranges. Python must have the `Europe/London` IANA timezone data.

**NOT_VIABLE_AFTER_BACKTEST**
