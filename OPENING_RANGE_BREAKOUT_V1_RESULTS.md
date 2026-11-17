# Candidate 6: Opening Range Breakout

No approved ORB specification was found. This is the explicitly assumed
[fixed interpretation](strategies/opening_range_breakout_v1.md), not a claim
that previously approved rules were followed.

| Metric | 2025 | 2026 Jan–Oct |
|---|---:|---:|
| Trades | 251 | 202 |
| Win rate | 32.27% | 32.18% |
| Profit factor | 0.9529 | 0.9489 |
| Expectancy / average trade, pips | -0.3187 | -0.3465 |
| Net pips | -80 | -70 |
| Average R | -0.0319 | -0.0347 |
| Maximum closed-trade drawdown, pips | 150 | 390 |
| Average hold, minutes | 119.44 | 205.20 |
| Trades per active data day | 0.8045 | 0.7799 |
| Long trades / net pips | 133 / -40 | 104 / -80 |
| Short trades / net pips | 118 / -40 | 98 / +10 |

London 07:00–08:00 complete opening range, first close breakout during
08:00–11:00 by bar-open time, 10/20-pip stop/target. A range missing a
bar is skipped. Timezone conversion is DST-aware. Next-available-open
entry and stop-first OHLC execution use the existing conventions. Historical
prefixes at 1,000, 10,000 and 30,000 bars matched full-run signals on both
datasets; tests cover both directions, DST and missing range bars.

In both periods profit factor is below 1.10 and expectancy is negative.
This tests one fixed interpretation, not all ORB strategies. See the
[comparison](CANDIDATE_RESEARCH_SUMMARY.md) for costs and limitations.

```powershell
python -m candidate_strategies.backtest_opening_range_breakout_v1 --input data\eurusd_m5_2025.csv --output-dir backtests\opening_range_breakout_v1\2025
python -m candidate_strategies.backtest_opening_range_breakout_v1 --input data\eurusd_m5_2026_01_10.csv --output-dir backtests\opening_range_breakout_v1\2026
```

**NOT_VIABLE_AFTER_BACKTEST**
