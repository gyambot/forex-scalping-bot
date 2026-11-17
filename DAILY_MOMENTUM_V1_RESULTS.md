# Candidate 8: Daily-return Momentum

The [fixed specification](strategies/daily_momentum_v1.md) uses the sign
of the previous 24 elapsed hours at 08:00 London, with 10/20-pip risk and
the shared next-open execution assumptions. An exact prior observation is
required; this is a short-horizon adaptation of a public momentum concept,
not the published study's strategy.

| Metric | 2025 | 2026 Jan–Oct |
|---|---:|---:|
| Trades | 205 | 167 |
| Win rate | 29.76% | 27.54% |
| Profit factor | 0.8472 | 0.7603 |
| Expectancy / average trade, pips | -1.0732 | -1.7365 |
| Net pips | -220 | -290 |
| Average R | -0.1073 | -0.1737 |
| Maximum closed-trade drawdown, pips | 350 | 330 |
| Average hold, minutes | 102.78 | 173.74 |
| Trades per active data day | 0.6571 | 0.6448 |
| Long trades / net pips | 102 / +30 | 76 / -130 |
| Short trades / net pips | 103 / -250 | 91 / -160 |

Both periods fail profit factor and expectancy thresholds. See the
[comparison](CANDIDATE_RESEARCH_SUMMARY.md) for common limitations.
Historical signal prefixes matched full runs in both datasets; tests cover
both directions, exact elapsed time and daylight saving.

```powershell
python -m candidate_strategies.backtest_research_candidate --strategy daily_momentum_v1 --input data\eurusd_m5_2025.csv --output-dir backtests\daily_momentum_v1\2025
python -m candidate_strategies.backtest_research_candidate --strategy daily_momentum_v1 --input data\eurusd_m5_2026_01_10.csv --output-dir backtests\daily_momentum_v1\2026
```

**NOT_VIABLE_AFTER_BACKTEST**
