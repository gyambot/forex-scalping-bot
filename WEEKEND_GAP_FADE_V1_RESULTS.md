# Candidate 9: Weekend Gap Fade

[Specification and public source](strategies/weekend_gap_fade_v1.md).
The candidate fades a qualifying Friday-to-Sunday/Monday reopening gap after
the first observed M5 bar, enters next available open, and uses a 10-pip
stop and 20-pip target. This is a fixed exploratory implementation.

| Metric | 2025 | 2026 Jan–Oct |
|---|---:|---:|
| Trades | 27 | 31 |
| Win rate | 40.74% | 48.39% |
| Profit factor | 1.3750 | 1.8750 |
| Expectancy / average trade, pips | +2.2222 | +4.5161 |
| Net pips | +60 | +140 |
| Average R | +0.2222 | +0.4516 |
| Maximum closed-trade drawdown, pips | 50 | 40 |
| Average hold, minutes | 188.15 | 263.23 |
| Trades per active data day | 0.0865 | 0.1197 |
| Long trades / net pips | 13 / +80 | 18 / +120 |
| Short trades / net pips | 14 / -20 | 13 / +20 |

Both periods meet the numeric PF and expectancy criteria. For this
exploratory comparison, "acceptable relative to returns" is interpreted as
closed-trade pip drawdown no greater than net pips in each period: 50/60
and 40/140. This is not an equity-risk or forward-drawdown limit.

## Important uncertainty

Only 58 trades in total, with just 13–18 in each direction per period, are
insufficient to establish a durable edge. The 2025 short subset lost 20 pips.
The selection follows several candidate trials on the same histories, so
these are not independent out-of-sample results.
For context, the pooled 26 wins in 58 trades give an approximate 95%
Wilson win-rate interval of 32.75%–57.55%, under independent-trade
assumptions and without correcting for candidate selection. It includes
the idealized 33.33% break-even win rate for 2:1 payoffs; it is not a
confidence interval for profitability under actual execution costs.

The fixed one-pip spread may seriously understate executable costs at weekend
reopening. Bid OHLC cannot establish actual ask, broker fills, liquidity or
intrabar order. No commissions, slippage, financing or sizing are included.
One 2026 trade uses a stale Friday reference: 2026-10-09 04:55 UTC to
2026-10-11 22:00 UTC, because a source date was excluded. That trade
contributed +20 pips. As a *descriptive sensitivity only*, removing it from
the recorded trades leaves 30 trades, +120 pips, PF 1.75, and +4.0
pips/trade; this is not a new backtest or a revised rule.

Both data sets' signal prefixes matched their full runs at 1,000, 10,000 and
30,000 bars; every trade's signal and actual R were checked. A 2026 rerun
produced byte-identical metrics and trade files. The full test suite passed
44 tests. See [comparison](CANDIDATE_RESEARCH_SUMMARY.md) for common caveats.

## Demo evaluation planning — not authorization to trade

Before any demo execution, independently validate the timestamp and weekend
gap inputs against broker history, measure actual reopening bid/ask spreads
and order availability, specify acceptable slippage and risk, and assess
the sample's uncertainty on genuinely new data. The existing demo executor,
reconciliation and study gate are unchanged and are not demonstrated to
support this candidate. No demo order was submitted. Passing this historical
screen does not promote the strategy, satisfy the existing gate, or establish
broker safety.

```powershell
python -m candidate_strategies.backtest_research_candidate --strategy weekend_gap_fade_v1 --input data\eurusd_m5_2025.csv --output-dir backtests\weekend_gap_fade_v1\2025
python -m candidate_strategies.backtest_research_candidate --strategy weekend_gap_fade_v1 --input data\eurusd_m5_2026_01_10.csv --output-dir backtests\weekend_gap_fade_v1\2026
```

**READY_FOR_DEMO_EVALUATION**
