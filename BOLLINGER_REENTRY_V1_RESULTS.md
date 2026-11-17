# Candidate 7: Bollinger Re-entry

The [fixed specification](strategies/bollinger_reentry_v1.md) uses 20-close
bands, re-entry after an extreme close, 10/20-pip risk and the shared
next-open execution assumptions.

| Metric | 2025 | 2026 Jan–Oct |
|---|---:|---:|
| Trades | 2,060 | 1,232 |
| Win rate | 29.61% | 32.39% |
| Profit factor | 0.8237 | 0.9521 |
| Expectancy / average trade, pips | -1.2659 | -0.3249 |
| Net pips | -2,607.7 | -400.3 |
| Average R | -0.1266 | -0.0325 |
| Max closed-trade drawdown, pips | 2,739.0 | 870.9 |
| Average hold, minutes | 133.86 | 203.21 |
| Trades per active data day | 6.6026 | 4.7568 |
| Long trades / net pips | 999 / -982.8 | 626 / -601.8 |
| Short trades / net pips | 1,061 / -1,624.9 | 606 / +201.5 |

Both runs fail profit factor and expectancy thresholds. The positive 2026
short subset is descriptive and is not an independent validation of a
short-only rule. For sources, comparison and modeling limitations see
[comparison](CANDIDATE_RESEARCH_SUMMARY.md). Historical signal prefixes
matched full runs in both datasets and unit tests cover both directions.

Reproduce for each year using:

```powershell
python -m candidate_strategies.backtest_research_candidate --strategy bollinger_reentry_v1 --input data\eurusd_m5_2025.csv --output-dir backtests\bollinger_reentry_v1\2025
python -m candidate_strategies.backtest_research_candidate --strategy bollinger_reentry_v1 --input data\eurusd_m5_2026_01_10.csv --output-dir backtests\bollinger_reentry_v1\2026
```

**NOT_VIABLE_AFTER_BACKTEST**
