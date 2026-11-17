# Weekend Gap Fade: Real-World Validation Readiness

## Current evidence

The [historical candidate report](WEEKEND_GAP_FADE_V1_RESULTS.md) reports
27 trades in 2025 (PF 1.375, +2.22 pips/trade) and 31 in January–October
2026 (PF 1.875, +4.52 pips/trade). The
[execution stress test](WEEKEND_GAP_FADE_STRESS_TEST.md) reran the strategy
with different fixed spreads and one-pip adverse entry slippage in two
scenarios. Four of six scenarios had pooled PF > 1.10, but only two passed
in 2025 alone. These histories were used to select the candidate; neither
is a new prospective test. There is no verified live broker reopening
spread or fill evidence in these results.

## Spread realism: existing stress results

The following are full reruns with **zero entry slippage** and fixed spread
throughout each position, not estimates of actual broker conditions.

| Fixed spread | Pooled trades | Pooled PF | Pooled expectancy, pips | Pooled net pips | 2025 net pips | 2026 net pips |
|---:|---:|---:|---:|---:|---:|---:|
| 1 pip | 58 | 1.6250 | +3.4483 | +200.0 | +60.0 | +140.0 |
| 2 pips | 58 | 1.5152 | +2.9310 | +170.0 | +30.0 | +140.0 |
| 3 pips | 58 | 1.4118 | +2.4138 | +140.0 | 0.0 | +140.0 |
| 5 pips | 58 | 0.8258 | -1.2362 | -71.7 | -150.1 | +78.4 |

With one pip adverse entry slippage, the 2-pip spread scenario has pooled
PF 1.4118 and +140.0 pips; the 3-pip scenario has PF 1.0510 and +19.4
pips. In 2025 those scenarios produced 0 and -90 pips respectively.

### Break-even estimates and limits

Here **break-even** means zero net pips / PF 1.0, not the PF > 1.10
historical screening threshold.

- **Spread, zero slippage, pooled:** the tested 3-pip point is positive and
  the 5-pip point negative. Thus profitability changes somewhere between
  those sampled assumptions; an exact break-even spread is **not identified**.
  Exit paths can change discontinuously, so linear interpolation and a
  monotonic threshold cannot be assumed. The 2025-only tested point at
  3 pips is exactly zero; 2026 remains positive at 5 pips.
- **Adverse entry slippage:** with fixed spread 2 or 3 pips, the pooled
  result is positive at the largest tested slippage, 1 pip; no losing
  pooled slippage scenario was tested at either spread. A pooled
  break-even slippage threshold is therefore **not determined or bounded
  above** by these results. For 2025 only, 2-pip spread plus 1 pip is
  exactly zero; at 3-pip spread, 0 slippage is already zero and 1 pip
  loses. These are sample-specific observations, not broker limits.

Do not treat a break-even point as safe: the PF > 1.10 requirement is
stricter, and fixed spreads omit commissions, exit slippage, financing
and spread spikes.

## Missing evidence and risk factors

- First observable and theoretical-entry broker bid/ask quotes, timestamps,
  spreads, quote delays, raw data completeness and broker weekend schedule.
- Actual execution slippage, order rejections, liquidity, stop behavior,
  commission and financing. No-order observation cannot establish fills.
- Broker-versus-HistData gap definitions and stale or missing Friday data.
  One historical 2026 winner used an unusually stale Friday reference.
- Intrabar order, exit-side ask, position sizing, real equity drawdown and
  risk of price gaps. One-pip fixed spread is particularly uncertain at
  reopening.
- Candidate-specific demo executor integration, safety, restart and
  reconciliation, explicitly authorized testing, account isolation and
  owner-approved risk limits. The existing executor and gate are unchanged
  and have not been established as suitable for this strategy.
- Small samples, multiple candidate selection, dependence across weekends
  and an unknown prospective expectancy. Ten weekends may produce fewer
  than ten signals and do not by themselves prove profitability.

## Ten-observation schedule

Each row is a scheduled Friday UTC and its expected Sunday UTC; actual
broker reopening may be Monday or delayed. Holidays, missed observations
and unavailable data remain in the denominator, not silently replaced.
Christmas and New Year schedules require particular care.

| # | Friday UTC | Expected Sunday UTC |
|---:|---|---|
| 1 | 2026-11-20 | 2026-11-22 |
| 2 | 2026-11-27 | 2026-11-29 |
| 3 | 2026-12-04 | 2026-12-06 |
| 4 | 2026-12-11 | 2026-12-13 |
| 5 | 2026-12-18 | 2026-12-20 |
| 6 | 2026-12-25 | 2026-12-27 |
| 7 | 2027-01-01 | 2027-01-03 |
| 8 | 2027-01-08 | 2027-01-10 |
| 9 | 2027-01-15 | 2027-01-17 |
| 10 | 2027-01-22 | 2027-01-24 |

## Recommended next step

Start the read-only, no-order [observation program](WEEKEND_GAP_FADE_VALIDATION_PLAN.md)
and record all ten planned weekends in the
[log](WEEKEND_GAP_FADE_VALIDATION_LOG.csv) using the
[guide](WEEKEND_GAP_FADE_OBSERVATION_GUIDE.md). At the end, report observed
spread and quote movement distributions, complete/no-signal/missing counts,
and hypothetical outcomes with uncertainty. If evidence remains insufficient,
extend observation on a documented prospective schedule rather than claiming
an edge.

Automated demo execution requires the measurable data, independent signal
reconciliation, broker and risk-control checks listed in the plan, plus
separate authorization. This readiness decision authorizes neither a
demo order nor live trading.

**READY_FOR_MANUAL_WEEKEND_OBSERVATION**
