# Trendline Stochastic V1: Historical Results

## Decision

**NOT_VIABLE_AFTER_BACKTEST**

Under the fixed assumptions tested, both historical periods have negative
expectancy and profit factor below 1. This is not a recommendation to
deploy, nor proof that every trendline/stochastic strategy fails.

## Scope and assumptions

The transcript was unavailable. The prototype is an objective interpretation
chosen for evidence collection, not a verified reproduction of the source.
The complete frozen assumptions are in
[trendline_stochastic_v1.md](strategies/trendline_stochastic_v1.md):
EMA200 trend direction; confirmed 5-bar pivots; latest-two-pivot lines;
0.25 × simple ATR14 zones; stochastic 14,3,3; four bounce and breakout
setups; one position; 10-pip stop, 20-pip target; next-available-M5-open
entry and modeled 1-pip spread. No parameter sweep was conducted.

## Results

| Metric | 2025 | 2026 Jan–Oct |
|---|---:|---:|
| EURUSD M5 bars | 73,683 | 60,551 |
| Trade count | 1,300 | 795 |
| Win rate | 28.46% | 30.19% |
| Net profit | -1,971.6 pips | -921.2 pips |
| Profit factor | 0.7893 | 0.8390 |
| Expectancy / average trade | -1.5166 pips | -1.1587 pips |
| Average R multiple | -0.1517 R | -0.1159 R |
| Maximum closed-trade drawdown | 2,025.5 pips | 1,165.8 pips |
| Average hold | 150.57 minutes | 233.18 minutes |
| Trades per active data day | 4.17 | 3.07 |
| CAGR | Not supported | Not supported |

CAGR cannot be computed without an account equity, position sizing and
compounding model. R uses the fixed initial 10-pip risk; gap losses can
exceed 1R. Drawdown is closed-trade cumulative pips, not equity or percentage
drawdown.

Breakouts produced 1,289 trades and -1,951.6 pips in 2025, and 781 trades
and -901.2 pips in 2026. Bounces produced only 11 and 14 trades respectively,
each totaling -20 pips. The low bounce counts do not support a reliable
standalone conclusion about that setup.

## Strengths and weaknesses

- Both periods produced a substantial number of total trades; signals and
  their assumptions are deterministic and can be inspected.
- Both periods lost money in the simplified model; the reported 2:1 gross
  target did not compensate for the observed win rate and stop-gap losses.
- Results are dominated by breakout trades. The two setup types have
  different sample sizes and should not be treated as equally evidenced.
- This is a fixed exploratory candidate, not an independently validated or
  optimized strategy. The two periods are separate historical runs, not a
  claim of prospective out-of-sample performance.

## Limitations and verification

HistData bid data contain missing buckets and gaps, detailed in
[data provenance](data/README.md). Bar-index trendlines and next-available-bar
entry cross gaps. Exit order within a bar is unknowable from OHLC; the runner
assumes stop-first, and hold time counts observed bars rather than elapsed
wall time. Fixed spread, zero commission, zero slippage and no financing are
optimistic simplifications; no live/demo broker acceptance or execution is
established. The strategy is outside the present one-family project charter
and does not change V1 or the demo gate.

The candidate tests verify all four setup classifications, close-based
prefix causality, next-open entry, long/short stop priority and final-bar
signal handling. Actual-data prefixes at 1,000, 10,000 and 30,000 bars
matched the corresponding full-run signals. `python -m unittest discover -s
tests` passed 25 tests, including the existing V1 backtest regressions.

## Reproduce

```powershell
python -m candidate_strategies.backtest_trendline_stochastic_v1 --input data\eurusd_m5_2025.csv --output-dir backtests\trendline_stochastic_v1\2025
python -m candidate_strategies.backtest_trendline_stochastic_v1 --input data\eurusd_m5_2026_01_10.csv --output-dir backtests\trendline_stochastic_v1\2026
```

Trade records and metrics are in the corresponding output directories. Input
SHA-256 hashes and bar ranges are recorded in each `metrics.json`.
