# Liquidity Sweep + Market Structure Shift V1 Results

## Results

| Metric | 2025 | 2026 Jan–Oct |
|---|---:|---:|
| EURUSD M5 bars | 73,683 | 60,551 |
| Trade count | 1,034 | 672 |
| Win rate | 30.66% | 28.27% |
| Net profit | -921.8 pips | -1,170.6 pips |
| Profit factor | 0.8731 | 0.7637 |
| Expectancy / average trade | -0.8915 pips | -1.7420 pips |
| Average R | -0.0891 R | -0.1742 R |
| Maximum closed-trade drawdown | 1,021.8 pips | 1,194.3 pips |
| Average hold | 140.98 minutes | 196.18 minutes |
| Trades per active data day | 3.31 | 2.59 |

2025 long/short counts were 497/537, with -291.6/-630.2 pips respectively.
2026 long/short counts were 319/353, with -861.6/-309.0 pips respectively.
These are descriptive breakdowns, not additional optimized hypotheses.

## Assumptions

The [candidate specification](strategies/liquidity_sweep_mss_v1.md) defines
the full reproducible rules. In brief: strict confirmed five-bar pivots;
one-pip sweep and close back through the swept pivot; break of the most
recent opposite pivot by a later close within 12 observed bars; one
position; entry at the next available M5 open; 10-pip stop, 20-pip target,
and fixed one-pip spread. No parameter sweep was performed.

## Interpretation and limitations

Both periods show negative expectancy and profit factor below one under
these fixed assumptions. The runs provide historical evidence, not proof
that every liquidity-sweep strategy is unprofitable. No broker execution,
slippage, commission, financing, account equity or compounding is modeled.
Maximum drawdown is in closed-trade pips, not a percentage or an intratrade
equity drawdown. Gap losses can exceed 1R; CAGR is not supported.

OHLC data cannot establish exact intrabar order; the model conservatively
uses stop-first if both levels are touched. Setup lifetimes and hold times
count observed bars and can span market closures or missing data. Input
provenance and gaps are documented in [data/README.md](data/README.md).
The candidate is outside the current one-family charter, is not V2, and
does not modify V1, its demo executor, or the study gate.

Five candidate tests cover both directions, reclaim and close confirmation,
inclusive sweep threshold, expiry and causal prefixes, and next-open
stop-priority execution. The complete `tests` suite passed 30 tests.
Historical signal prefixes of 1,000, 10,000 and 30,000 bars matched their
full-run counterparts. This does not substitute for broker validation.

## Reproduce

```powershell
python -m candidate_strategies.backtest_liquidity_sweep_mss_v1 --input data\eurusd_m5_2025.csv --output-dir backtests\liquidity_sweep_mss_v1\2025
python -m candidate_strategies.backtest_liquidity_sweep_mss_v1 --input data\eurusd_m5_2026_01_10.csv --output-dir backtests\liquidity_sweep_mss_v1\2026
```

Each output directory contains trade records, sweep and pivot evidence, input
hash and computed metrics. The 2026 period is a separate historical run,
not a claim of prospective out-of-sample validation.

**NOT_VIABLE_AFTER_BACKTEST**
