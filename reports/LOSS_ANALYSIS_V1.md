# Breakout Scalping V1 — Loss Analysis

**Scope:** Historical losing trades only, with winning trades retained as
denominators for comparative rates. V1 was not changed and no parameters were
optimized. This is a diagnostic of the existing runs, not a strategy version
or a claim about demo/live performance.

## Data and method

- Baseline: 2025 EURUSD M5 bid bars and trades in
  [`backtests/2025_histdata_v1/`](../backtests/2025_histdata_v1/).
- Temporal validation: January-October 2026 EURUSD M5 bid bars and trades in
  [`validation/2026_histdata_v1/`](../validation/2026_histdata_v1/).
- A loss is a trade with `pnl_pips < 0`. Session, hour, and weekday use the
  logged entry timestamp in UTC; for V1 this is the next-bar entry aligned to
  the signal-bar close.
- Session definitions match the existing weekly review: Asia-Pacific 00-06,
  London 07-11, New York 12-20, Late 21-23 UTC. The narrower 21:00-22:59
  finding below comes from inspecting the two component hour bins, not from a
  changed V1 rule.
- Breakout distance is the signal-bar close beyond the prior 20-bar channel
  edge, in pips. Volatility is the simple average M5 high-low range of the
  prior 20 bars, in pips; it is a descriptive proxy, not ATR.
- Volatility and breakout-distance tertiles use common cutoffs pooled across
  both historical samples. These are descriptive groupings, not tuned
  thresholds. Drawdowns are based on the ordered, realized trade P&L series.

The 2026 data is a later time period but comes from the same provider as the
2025 baseline. Both datasets have documented gaps and exclusions. Spread is
the backtest's fixed 1-pip assumption; neither historical file supports actual
spread analysis.

## 1. Where does V1 lose most often?

Across the samples, **71.42% of 2025 trades (1,614/2,260)** and **71.32% of
2026 trades (975/1,367)** lost. Most losing trades reached the stop:

| Sample | Stop-loss exits | Stop-loss gap exits | Losses |
|---|---:|---:|---:|
| 2025 | 1,606 | 8 | 1,614 |
| 2026 | 956 | 19 | 975 |

By absolute losing-trade count, New York (12:00-20:59 UTC) leads because it
also has the most trades: **741 losses in 2025** and **487 in 2026**. By
loss-rate rather than count, the weakest repeated time window is **21:00-22:59
UTC**:

| Entry time (UTC) | 2025 losses / trades | Loss rate | 2026 losses / trades | Loss rate |
|---|---:|---:|---:|---:|
| 21:00-21:59 | 34 / 41 | 82.9% | 22 / 24 | 91.7% |
| 22:00-22:59 | 27 / 34 | 79.4% | 34 / 45 | 75.6% |
| **Combined 21:00-22:59** | **61 / 75** | **81.3%** | **56 / 69** | **81.2%** |
| 23:00-23:59 | 52 / 65 | 80.0% | 19 / 28 | 67.9% |

The combined 21:00-22:59 window contains only 3.3% of 2025 trades and 5.0% of
2026 trades, but its loss rate is about 10 percentage points above each
sample's overall rate.

## 2. Where does V1 lose most money?

In **total realized losing pips**, New York is largest in both samples, mainly
because it has the most entries. The 21:00-22:59 window is more damaging
**per trade**:

| Sample / window | Losing trades | Sum of losing P&L | Net P&L, all trades in window | Net P&L per trade |
|---|---:|---:|---:|---:|
| 2025 New York, 12:00-20:59 | 741 / 1,040 | -7,426.4 pips | -1,462.5 pips | -1.41 pips |
| 2025 21:00-22:59 | 61 / 75 | -618.8 pips | -338.8 pips | -4.52 pips |
| 2026 New York, 12:00-20:59 | 487 / 678 | -5,110.3 pips | -1,307.9 pips | -1.93 pips |
| 2026 21:00-22:59 | 56 / 69 | -560.0 pips | -300.0 pips | -4.35 pips |

The distinction matters: New York accounts for the most total loss, while the
small 21:00-22:59 UTC window has the more consistently poor per-trade result.
These are historical outcomes under a fixed spread assumption.

## 3. Characteristics recurring in both samples

### Session and time of day

All four broad UTC sessions were net negative in both samples; there is no
historical session with a positive aggregate net result across both periods.
The specific 21:00 and 22:00 UTC hour bins both show high loss rates in both
samples. By contrast, the 23:00 hour is less consistent: its loss rate falls
to 67.9% in 2026. This is why the strongest repeated time-of-day observation
is limited to 21:00-22:59, not the whole 21:00-23:59 “Late” bucket.

### Day of week

Losses occur on every active weekday in both datasets. Thursday has the
largest or near-largest weekday loss count (339 in 2025; 208 in 2026), but the
loss rates on Monday-Friday are broadly similar: 69.7%-72.4% in 2025 and
66.5%-73.5% in 2026. Sunday loss rates are higher (81.8%, 27/33 in 2025;
81.0%, 34/42 in 2026), but the sample is small and those trades cluster near
the weekly market reopen. The weekday evidence is weaker and less actionable
than the repeated two-hour UTC pattern.

### Volatility regime

Using the pooled prior-20-bar average-range tertiles (low ≤3.365 pips,
middle >3.365 to 5.105 pips, high >5.105 pips):

| Sample | Low-range losses / trades | Middle-range losses / trades | High-range losses / trades |
|---|---:|---:|---:|
| 2025 | 419 / 603 (69.5%) | 551 / 751 (73.4%) | 644 / 906 (71.1%) |
| 2026 | 425 / 606 (70.1%) | 318 / 461 (69.0%) | 232 / 300 (77.3%) |

The high-range group is worse than the low-range group in both periods, but
the middle-range group is worst in 2025 and best in 2026. This does **not**
establish a stable monotonic volatility weakness or justify an ATR/volatility
filter.

### Breakout distance

Losing trades' median breakout distance was 2.1 pips in 2025 and 1.8 pips in
2026. Winning trades had the same or nearly the same medians (2.0 and 1.8
pips). Using pooled distance tertiles (≤1.2, >1.2 to 3.1, >3.1 pips), the
highest-distance group has a slightly higher loss rate than the lowest in
2026 (74.2% vs 70.9%), but not in 2025 (71.5% vs 72.4%). Breakout distance
does not repeat strongly enough to be the leading weakness.

### Consecutive breakout attempts and loss clusters

Losses cluster because the overall loss probability is high: 2025 had 122
losing streaks of at least five trades (867 losses in those streaks), with a
maximum streak of 25; 2026 had 73 such streaks (512 losses), maximum 15.
However, the next trade immediately after a loss was not more likely to lose
than the already-high overall rate: 313/443 (70.7%) in 2025 and 246/356
(69.1%) in 2026. Only 6 and 7 of those immediate next trades, respectively,
were in the same direction as the prior losing trade. The data therefore
shows clustered losses, but not a repeated same-direction re-entry effect.

### Trade duration

Losses are often relatively quick, although the exact path is limited by M5
OHLC simulation:

| Sample | Losing trades closed within 15 min | Within 60 min | Loss rate for trades held >180 min |
|---|---:|---:|---:|
| 2025 | 407 / 1,614 (25.2%) | 967 / 1,614 (59.9%) | 56.7% |
| 2026 | 192 / 975 (19.7%) | 494 / 975 (50.7%) | 54.4% |

The ≤15-minute loss rate among **all** trades is 84.6% in 2025 and 91.9% in
2026; it declines for longer hold-time groups in both samples. This is
consistent with failed/quickly rejected entries, but duration is only known
after entry and is not itself a pre-trade filter hypothesis.

### Drawdown clusters

Each sample has one long, dominant unrecovered drawdown excursion:

- **2025:** from the early January equity peak to a 3,285.3-pip trough on
  2025-12-31; 2,234 subsequent trades were in that peak-to-trough interval,
  including 1,598 losses.
- **2026:** from the 2026-01-25 peak to a 2,415.6-pip trough on 2026-10-29;
  1,276 subsequent trades were in that interval, including 922 losses.

These are persistent cumulative losses rather than one isolated catastrophic
trade. They do not identify a single volatility or weekday cause.

## 4. Strongest evidence-based candidate hypothesis for a future V2

**Candidate to consider only after the project’s 100-completed-demo-trade
gate:** a single fixed UTC entry-time exclusion for **21:00-22:59 UTC** may
reduce exposure to the weakest repeated hours.

This is the strongest candidate in this diagnostic because the interval had
nearly identical loss rates in the two samples (81.3% and 81.2%), negative
net P&L (-338.8 and -300.0 pips), and a worse per-trade result than New York
(-4.52/-4.35 vs -1.41/-1.93 pips). It is only a hypothesis. The samples share
a provider, include data gaps, and do not capture real variable spreads or
execution. These observations cannot prove that a time filter will improve
performance or that the time window caused the losses.

**No V2 is designed here. V1 remains unchanged.** Do not implement or promote
this candidate now. If the future evidence gate is satisfied, it would need to
be tested as exactly one change against a new untouched validation period and
then demo results, with the existing V1 retained as the comparison baseline.
