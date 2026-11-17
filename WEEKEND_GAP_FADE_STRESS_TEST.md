# Weekend Gap Fade: Execution Stress Test

## Decision rule and result

**Four of six scenarios have pooled profit factor strictly greater than
1.10**, so the requested majority rule passes. The 2025-only results pass
just two of six scenarios; the 2026-only results pass six of six. Pooling
therefore masks materially weaker performance in 2025.

The user did not specify how to combine the historical periods, so the
decision uses the chronological pooled trade list across both previously
tested datasets. Each period is run independently, with positions closed
at its own end; the combined drawdown continues the cumulative trade
sequence across the boundary. This choice is disclosed rather than
presenting either year as independently meeting the majority rule.

## Results

Profit factor (PF) is gross winning pips divided by gross losing pips.
Expectancy is average net pips per trade. Drawdown is the maximum drawdown
in cumulative closed-trade pips, not mark-to-market equity or percentage
drawdown. The 2026 period ends on October 30.

### Combined 2025 and January–October 2026

| Scenario | Spread | Adverse entry slippage | Trades | PF | Expectancy, pips | Net pips | Max drawdown, pips | PF > 1.10 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| A | 1 pip | 0 | 58 | 1.6250 | +3.4483 | +200.0 | 60.0 | Yes |
| B | 2 pips | 0 | 58 | 1.5152 | +2.9310 | +170.0 | 60.0 | Yes |
| C | 3 pips | 0 | 58 | 1.4118 | +2.4138 | +140.0 | 60.0 | Yes |
| D | 5 pips | 0 | 58 | 0.8258 | -1.2362 | -71.7 | 161.7 | No |
| E | 2 pips | 1 pip | 58 | 1.4118 | +2.4138 | +140.0 | 60.0 | Yes |
| F | 3 pips | 1 pip | 58 | 1.0510 | +0.3345 | +19.4 | 100.6 | No |

### Separate periods

| Scenario | Period | Trades | PF | Expectancy, pips | Net pips | Max drawdown, pips |
|---|---|---:|---:|---:|---:|---:|
| A | 2025 | 27 | 1.3750 | +2.2222 | +60.0 | 50.0 |
| A | 2026 | 31 | 1.8750 | +4.5161 | +140.0 | 40.0 |
| B | 2025 | 27 | 1.1765 | +1.1111 | +30.0 | 50.0 |
| B | 2026 | 31 | 1.8750 | +4.5161 | +140.0 | 40.0 |
| C | 2025 | 27 | 1.0000 | 0.0000 | 0.0 | 50.0 |
| C | 2026 | 31 | 1.8750 | +4.5161 | +140.0 | 40.0 |
| D | 2025 | 27 | 0.3477 | -5.5593 | -150.1 | 150.1 |
| D | 2026 | 31 | 1.4317 | +2.5290 | +78.4 | 60.0 |
| E | 2025 | 27 | 1.0000 | 0.0000 | 0.0 | 50.0 |
| E | 2026 | 31 | 1.8750 | +4.5161 | +140.0 | 40.0 |
| F | 2025 | 27 | 0.5714 | -3.3333 | -90.0 | 90.0 |
| F | 2026 | 31 | 1.6413 | +3.5290 | +109.4 | 60.0 |

## Execution assumptions

The specified entry slippage amount was not supplied; E and F use a
fixed **one pip adverse** slippage per entry, not a measured distribution.
All scenarios rerun the original fixed signals, using next-available-bar
entry and one position. Buy entry is bid open plus scenario spread and
slippage; sell entry is bid open minus slippage. The 10-pip stop and
20-pip target are placed from the actual simulated entry, matching the
original risk convention. Long exits use bid; short exits use bid plus
the scenario spread. A scenario's fixed spread applies on every bar,
including exit, not only at reopening.

The existing OHLC helper determines exits, including stop-first on an
ambiguous bar and adverse gap fills. No exit slippage, commissions,
financing, variable spread, liquidity limits or position sizing are
modeled. Wider spread/slippage alter entry and exit paths and may change
whether a stop or target is reached; these are full reruns, not a
post-hoc deduction from original P&L. For short exits the isolated runner
adjusts bid OHLC before invoking the existing fixed-spread helper so
that its computed ask equals the scenario ask.

## Limitations

There are only 58 trades, selected after multiple candidate trials. This
is neither an independently validated edge nor evidence that a broker
will provide these spreads or fills. Scenario D loses money overall; F
misses the PF threshold and has only +19.4 pips against 100.6 pips
closed-trade drawdown. Conditions could be substantially worse than any
fixed scenario. One 2026 winning signal uses a stale Friday reference due
to an excluded source date, as documented in the
[original candidate report](WEEKEND_GAP_FADE_V1_RESULTS.md).

The decision is **only the requested historical screen**, not an
authorization to trade or a finding that the existing demo executor is
compatible. Validate weekend timestamps, broker bid/ask spreads,
slippage, order availability and demo risk controls before any separately
authorized demo validation; no order has been placed.

## Reproducibility and checks

```powershell
python -m candidate_strategies.stress_weekend_gap_fade --input-2025 data\eurusd_m5_2025.csv --input-2026 data\eurusd_m5_2026_01_10.csv --output-dir backtests\weekend_gap_fade_stress
```

The output contains the input SHA-256 hashes, per-period and pooled
metrics, and twelve scenario trade CSVs. Scenario A reproduced every
field in the original 2025 and 2026 trade exports. A repeat run produced
byte-identical metrics and all twelve trade CSVs. Four new tests cover
baseline equivalence, long and short spread/slippage effects, adverse
gaps and stop priority; the full suite passed 48 tests. Source-data gaps
are described in [data provenance](data/README.md).

**READY_FOR_DEMO_VALIDATION**
