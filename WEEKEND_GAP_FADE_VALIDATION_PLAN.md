# Weekend Gap Fade: Manual Validation Plan

## Purpose and boundaries

Observe ten consecutive weekend reopenings without placing orders, arming an
executor, changing the strategy, or modifying existing trading infrastructure.
The objective is to measure data availability, spread and quote-to-reference
price movement, and to reconstruct hypothetical outcomes—not to claim that
ten observations establish an edge. A quoted price is not proof of an
executable fill. No actual execution slippage can be measured without orders.

The frozen rules are in [the candidate specification](strategies/weekend_gap_fade_v1.md);
the [stress test](WEEKEND_GAP_FADE_STRESS_TEST.md) describes the historical
execution model. Broker candles and quotes may differ from HistData.

## Observation schedule and denominators

Begin with the Friday 2026-11-20 close and its Sunday/Monday reopening.
Observe ten consecutive scheduled weekends, including no-signal weekends
and holidays; see the dated schedule in
[demo readiness](WEEKEND_GAP_FADE_DEMO_READINESS.md). For each, enter one row
in [the observation log](WEEKEND_GAP_FADE_VALIDATION_LOG.csv), even if data
are unavailable. Count planned weekends, observed weekends, complete
observations, signal weekends, no-signal weekends and unknowns separately.
Do not silently replace missed weekends. If fewer than ten are usable,
report the actual count and any extension separately; never change the
original schedule after seeing results.

## Prespecified capture process

1. Select the same EURUSD broker symbol, quote source and demo account
   environment for all ten observations. Record broker/server identity,
   symbol suffix, pip size (0.0001), chart time convention, platform and
   broker session schedule. Record broker timestamps with explicit verified
   UTC offset and UTC equivalents; do not assume server wall time is UTC.
2. Before market close capture the last observed Friday UTC M5 bid bar and
   its close and open timestamp. After reopening, capture the first observed
   M5 bid bar and its open and open timestamp. Preserve the Friday-to-reopen
   history and record any missing or stale candles and their timestamps.
   The frozen rule requires Friday UTC to Sunday or Monday UTC and at least
   36 elapsed hours between the two bar **open timestamps**. Gaps caused by
   missing data can satisfy this condition; flag them rather than silently
   substituting a later Friday close.
3. Capture the first observable post-reopening bid and ask, server timestamp
   if available and local capture time, source, spread and quote freshness.
   It may not be the broker's true first quote: record that distinction and
   the monitoring start time. Preserve available timestamped tick history;
   a screenshot alone cannot prove no earlier quote existed.
4. Compute signed gap `(reopening bid M5 open - last Friday bid M5 close) /
   0.0001`. Positive means up; negative means down. If the UTC day and
   elapsed-time conditions hold and absolute gap is at least 5 pips, the
   signal is short for an up gap or long for a down gap. Otherwise no
   signal; missing data means **unknown**, never no-signal. The signal is
   available only when the first reopening M5 bar has completed.
5. On a signal, record the next available M5 bar's open timestamp as the
   historical model's theoretical entry time and its bid open as the
   reference. If that bar is delayed, record the delay. The historical
   reference entry is bid open + 1 pip for long, bid open for short.
   Capture a timestamped first valid observed bid/ask at or after that
   entry time and its age/delay. No future quote may be recorded as if it
   had been available at the theoretical entry time. If none is available,
   mark the observable-price and quote movement as unknown.
6. For the no-order quote comparison, long uses observed ask and short uses
   observed bid. With `ref_bid` the theoretical entry bar's bid open,
   calculate signed adverse **quote movement**, not fill slippage:
   long = `(observed ask - (ref_bid + observed spread)) / 0.0001`;
   short = `(ref_bid - observed bid) / 0.0001`. The observed bid/ask
   spread is from the same quote. Negative values are favorable. This
   intentionally separates spread from movement; it may reflect observation
   delay and cannot establish broker execution slippage or order fill.
7. Record two separate hypothetical paths for each signal: (a) the
   historical 1-pip-spread reference, and (b) an observed-quote proxy using
   the captured ask for long or bid for short as simulated entry. For each,
   compute stop and target 10 and 20 pips from its own simulated entry.
   Track the reference path with existing stop-first OHLC conventions;
   track the proxy from recorded bid ticks for long and ask ticks for
   short, with timestamps and continuity. This is hypothetical, not a
   fill. Record each path's stop, target, time, outcome and pips separately.
   If a path is still open, say `pending`; if its quote record is missing,
   ambiguous, or cannot establish exit order, say `unknown`, not a win.
   On actual quote gaps, do not assume a stop filled at its level.
8. Apply the original one-position rule to each hypothetical path
   independently. A later signal while that path is open is logged as
   blocked, not another entered trade. Continue tracking open hypothetical
   positions after the ten observation weekends until resolved or explicitly
   reported as pending; never fabricate a final outcome.

## Records and quality

Use the requested CSV as an index, not as the only evidence. Store a
timestamped evidence packet per weekend with raw M5/tick exports when
available, screenshots, UTC conversion evidence, the calculated reference
and proxy paths, missing intervals and operator notes. The guide defines
the field encoding and screenshot workflow. Preserve originals and record
capture time and source. Do not copy credentials, account numbers or
unnecessary personal information into evidence.

Report median, range and maximum observed spreads, quote delays and signed
quote movement, including all available observations and denominators.
Report first-observable and theoretical-entry spreads separately; do not
assume one equals the other. Compare the observed distributions against
stress assumptions, including the proportion of available entry quotes
above 1, 2, 3 and 5 pips. Missingness is a result, not a zero.
Report reference and proxy outcomes separately, with pending and unknown
counts, and avoid interpreting a small signal sample as proof of expectancy.

## Evidence needed before an automated-demo decision

- Ten scheduled observations accounted for, with observed/complete/unknown
  counts and raw timestamped evidence; unresolved missing observations
  remain explicit. Ten is the requested collection horizon, not a
  statistically justified profitability threshold.
- Reconstruct each available signal and the next-bar entry independently,
  including no-signal and blocked cases; reconcile disagreements to source
  records without retroactively changing rules.
- Measure first-observable and entry bid/ask spreads and quote-delay
  distributions. Actual fill slippage remains unmeasured; obtain separately
  authorized order-based evidence later if needed, not during this program.
- Independently verify broker history, UTC conversions, tradability, order
  constraints, minimum stop distance, rejection behavior and costs.
  Published schedules or quotes alone cannot establish actual fill behavior.
- Establish and test candidate-specific demo execution, position sizing,
  max loss and exposure, stop protection, rejection handling, restart and
  reconciliation, and a manual kill switch under separately authorized
  non-order tests. Demonstrate that no real account can be used. The existing
  executor and gate are unchanged and have not been verified for this
  candidate.
- Compare results and uncertainty to a risk limit approved in advance by the
  owner. Quote observations do not set a numerical loss limit or authorize
  deployment. A small or missing sample cannot substantiate positive
  expectancy; use independently collected additional data if the evidence
  cannot resolve the decision.

Success here means reliable observation records, not strategy promotion.
