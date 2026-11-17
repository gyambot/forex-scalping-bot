# EURUSD M5 Candidate Research Comparison

## Scope and ranking

Fixed research candidates were tested on the same HistData-derived 2025 and
January–October 2026 bid OHLC inputs; these periods are not independent
prospective validations. Candidate 6 uses documented assumptions because
no approved ORB specification was located. Research stopped at candidate
9 because it met the stated historical screen; candidate 10 was not run.

Ranking below uses the **lower of the two period profit factors**, descending,
as a transparent descriptive convention. It does not account for sample
size, statistical uncertainty, multiple testing, realistic costs or equity
risk. Only candidate 9 meets PF >= 1.10 and positive expectancy in both
periods; its closed-trade pip drawdowns are also below net pips in each.

| Rank | Candidate / type | Lower period PF | Decision |
|---:|---|---:|---|
| 1 | [9: Weekend gap fade](WEEKEND_GAP_FADE_V1_RESULTS.md) | 1.3750 | READY_FOR_DEMO_EVALUATION, with major caveats |
| 2 | [6: London opening range](OPENING_RANGE_BREAKOUT_V1_RESULTS.md) | 0.9489 | NOT_VIABLE_AFTER_BACKTEST |
| 3 | [7: Bollinger re-entry](BOLLINGER_REENTRY_V1_RESULTS.md) | 0.8237 | NOT_VIABLE_AFTER_BACKTEST |
| 4 | [2: Trendline stochastic](TRENDLINE_STOCHASTIC_V1_RESULTS.md) | 0.7893 | NOT_VIABLE_AFTER_BACKTEST |
| 5 | [3: Liquidity sweep/MSS](LIQUIDITY_SWEEP_MSS_V1_RESULTS.md) | 0.7637 | NOT_VIABLE_AFTER_BACKTEST |
| 6 | [8: Daily-return momentum](DAILY_MOMENTUM_V1_RESULTS.md) | 0.7603 | NOT_VIABLE_AFTER_BACKTEST |
| 7 | [4: EMA pullback](EMA_PULLBACK_CONTINUATION_V1_RESULTS.md) | 0.5746 | NOT_VIABLE_AFTER_BACKTEST |
| 8 | [5: London breakout](LONDON_BREAKOUT_V1_RESULTS.md) | 0.5388 | NOT_VIABLE_AFTER_BACKTEST |

## Comparable results

PF is gross profit divided by gross loss; expectancy and drawdown are pips
per trade and closed-trade cumulative pips respectively. R is per-trade
initial risk (10 pips except ATR-based candidates 4 and 5). Directional
entries show trade count and net pips; they are not separately validated
rules.

| Candidate | Period | Trades | Win % | PF | Expectancy pips | Max DD pips | Avg R | Net pips | Long N / pips | Short N / pips |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 2 Trendline | 2025 | 1,300 | 28.46 | 0.7893 | -1.5166 | 2,025.5 | -0.1517 | -1,971.6 | 695 / -789.9 | 605 / -1,181.7 |
| 2 Trendline | 2026 | 795 | 30.19 | 0.8390 | -1.1587 | 1,165.8 | -0.1159 | -921.2 | 381 / -765.4 | 414 / -155.8 |
| 3 Sweep/MSS | 2025 | 1,034 | 30.66 | 0.8731 | -0.8915 | 1,021.8 | -0.0891 | -921.8 | 497 / -291.6 | 537 / -630.2 |
| 3 Sweep/MSS | 2026 | 672 | 28.27 | 0.7637 | -1.7420 | 1,194.3 | -0.1742 | -1,170.6 | 319 / -861.6 | 353 / -309.0 |
| 4 EMA pullback | 2025 | 3,319 | 22.15 | 0.6521 | -1.0451 | 3,478.2864 | -0.3381 | -3,468.8078 | 1,653 / -2,158.8711 | 1,666 / -1,309.9367 |
| 4 EMA pullback | 2026 | 2,819 | 20.01 | 0.5746 | -1.0044 | 2,845.7720 | -0.4015 | -2,831.2720 | 1,210 / -1,169.5221 | 1,609 / -1,661.7499 |
| 5 London breakout | 2025 | 738 | 25.75 | 0.7486 | -0.8312 | 623.0431 | -0.2277 | -613.4288 | 405 / -176.0788 | 333 / -437.3500 |
| 5 London breakout | 2026 | 600 | 19.00 | 0.5388 | -1.1443 | 686.5716 | -0.4301 | -686.5716 | 253 / -322.7638 | 347 / -363.8078 |
| 6 Opening range | 2025 | 251 | 32.27 | 0.9529 | -0.3187 | 150 | -0.0319 | -80 | 133 / -40 | 118 / -40 |
| 6 Opening range | 2026 | 202 | 32.18 | 0.9489 | -0.3465 | 390 | -0.0347 | -70 | 104 / -80 | 98 / +10 |
| 7 Bollinger re-entry | 2025 | 2,060 | 29.61 | 0.8237 | -1.2659 | 2,739 | -0.1266 | -2,607.7 | 999 / -982.8 | 1,061 / -1,624.9 |
| 7 Bollinger re-entry | 2026 | 1,232 | 32.39 | 0.9521 | -0.3249 | 870.9 | -0.0325 | -400.3 | 626 / -601.8 | 606 / +201.5 |
| 8 Daily momentum | 2025 | 205 | 29.76 | 0.8472 | -1.0732 | 350 | -0.1073 | -220 | 102 / +30 | 103 / -250 |
| 8 Daily momentum | 2026 | 167 | 27.54 | 0.7603 | -1.7365 | 330 | -0.1737 | -290 | 76 / -130 | 91 / -160 |
| 9 Weekend gap fade | 2025 | 27 | 40.74 | 1.3750 | +2.2222 | 50 | +0.2222 | +60 | 13 / +80 | 14 / -20 |
| 9 Weekend gap fade | 2026 | 31 | 48.39 | 1.8750 | +4.5161 | 40 | +0.4516 | +140 | 18 / +120 | 13 / +20 |

The frozen Breakout Scalping V1 reference has a 2025 historical run:
2,260 trades, 28.58% wins, PF 0.7982, -1.4431 pips/trade,
-0.1443 R, -3,261.4 pips and 3,285.3-pip drawdown. Its long/short
counts and net pips were 1,178/-945.8 and 1,082/-2,315.6. No comparable
2026 baseline output was located. It is not replaced or promoted.

## Failure analysis: evidence versus hypotheses

- **Stops and targets:** with a fixed 10-pip loss and 20-pip win the
  idealized break-even win rate is 33.33%, before gap losses and other
  costs. Candidates 2, 3, 6, 7 and 8 have total win rates below that
  level in both periods; candidate 6 is close at 32.27%/32.18%.
  This identifies an outcome imbalance, not whether stops were too tight,
  targets too distant, or entries lacked edge. OHLC cannot resolve the
  counterfactual without separate tests.
- **Overtrading / costs:** candidate 4 took 3,319 and 2,819 trades,
  at about 10.64 and 10.88 per active data day, accumulating
  -3,468.8 and -2,831.3 pips. Candidate 9 made only 27 and 31 trades.
  Frequency magnifies a negative per-trade expectancy; it does not prove
  that a frequency cap would turn it positive. A fixed spread is already
  included, but its effect is not isolated by a controlled cost experiment.
- **Regime, trend filter and volatility:** candidate 4 and candidate 5
  both use EMA50/EMA200 and ATR, yet have negative expectancy in both
  periods; this combination did not protect these implementations. There
  is no matched no-filter or volatility-stratified test, so the filter
  itself, a specific regime, or ATR placement cannot be isolated as cause.
- **Breakout vs reversal:** trendline candidate 2 is dominated by
  breakout trades (1,289 of 1,300 in 2025; 781 of 795 in 2026) and
  lost in both periods. Bollinger re-entry candidate 7 also lost in both.
  This does not establish a universal breakout or reversal bias.
  Candidate 9's positive gap-fade sample is small and not directly
  comparable to the much more frequent strategies.
- **Timing / session:** London ORB candidate 6 lost less per trade than
  the EMA-based London candidate 5, but rules and stops differ, so this
  is not evidence that opening-range timing or a session filter caused
  improvement. Likewise, once-daily momentum lost in both periods.
  No controlled session or entry-timing ablation was run.
- **Direction and changing conditions:** gap-fade shorts lost 20 pips
  in 2025 and gained 20 in 2026; 2026 Bollinger shorts gained 201.5
  pips while longs lost 601.8. Directional subsets and differing
  performance across periods are descriptive, not proof of regime
  causality or a basis for a newly optimized direction filter.

## Limitations, evidence, and operations

Data hashes, coverage and trade exports are in each candidate's
`backtests\<strategy>\<period>` directory; source gaps and exclusions are
documented in [data provenance](data/README.md). Historical execution
uses fixed one-pip spread and stop-first OHLC ordering, no commission,
slippage, financing or equity sizing. Next-available entries can cross gaps,
and hold durations count observed bars. Drawdown is not marked-to-market
equity drawdown. Weekend spreads and fills are especially uncertain.

All candidates 6–9 were checked for actual historical signal-prefix
causality at three lengths in both datasets, and all their trade signals
and R values were checked. The complete suite passed 44 tests, and a
candidate 9 2026 rerun was byte-identical. See individual reports for
reproduction commands, public source links and special caveats.

The new research mandate permits isolated strategies outside the original
one-family charter, but does not change the charter file, V1, the demo
executor, reconciliation, metrics engine or the gate. "Ready" here is a
historical-screen outcome only. Candidate 9 needs the broker-data, cost and
safety checks described in its report before any authorized demo use; no
live or demo order has been placed.
