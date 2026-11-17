# Trendline and Stochastic Research Candidate

## Status and source

The referenced transcript was not available in the chat or workspace.
Consequently, its strategy rules, exact wording and discretionary elements
cannot be identified or exhaustively analyzed. The user describes a candidate
involving trendlines, stochastic confirmation and 2:1 risk/reward. Everything
else below is a possible objective interpretation, **not** a rule verified
from the transcript. The example phrases below are supplied in the request,
not quotations verified against the missing transcript.

This is a research candidate only. Breakout Scalping V1 remains unchanged
and is the baseline. This alternative strategy is outside the current
one-strategy-family charter unless it is used strictly as a breakout filter
or the owner separately changes the project mandate. Researching this
candidate does not authorize implementation, replace V1, or create V2.

## Potential subjectivity and objective choices

The following are candidate questions to check against the transcript, not a
complete inventory of its language.

| Possible subjective phrase or choice | Why subjective | Objective alternatives to choose and freeze |
|---|---|---|
| "Major swing point" | Importance and choice of high or low vary by observer. | Fixed `L`-left/`R`-right pivot; fixed fractal; or ZigZag with a specified reversal threshold and confirmation rule. Do not treat a provisional ZigZag endpoint as final. |
| Trend direction | A visual trend can depend on the selected history. | Two successive confirmed higher highs **and** higher lows for uptrend, reversed for downtrend; or price relative to a precisely specified moving average. Define mixed and insufficient-history states. |
| "Obvious trend line" | Anchor points and qualifying touches are not unique. | Choose the latest two confirmed relevant pivots deterministically; or rank all eligible pairs by specified lookback, minimum touches, breach tolerance and tie-breakers. |
| "Trend line zone" | Width and whether a touch includes a wick are unspecified. | A fixed `5`-pip band; `k` times ATR; or a percentage of line price. These are examples, not selected values. Specify both sides of the line, the price source and evaluation time. |
| "Close well above" or below | "Well" has no measurable threshold. | A close at least `5` pips or `0.25 × ATR` beyond the line/zone, or the entire candle body beyond it. Specify strict versus inclusive comparisons. |
| Stochastic confirmation | Timeframe, smoothing, threshold and timing of a cross may differ. | Freeze lookback, K/D smoothing periods and methods, threshold, cross direction and whether the cross must occur on the breakout bar or within a fixed number of bars. |
| Stop placement | A visual swing or line leaves the distance and buffer ambiguous. | Fixed pip distance, confirmed pivot plus a fixed buffer, or an explicitly defined ATR multiple. Decide when the stop is fixed and how gaps are handled. |
| "2:1" reward/risk | Gross price distance and net P&L after spread/costs differ; risk basis may be unclear. | Define initial price risk `R` from actual simulated entry to initial stop and target at `entry + 2R` for long or `entry - 2R` for short. Separately specify cost treatment and stop-gap losses; realized reward/risk is not guaranteed to be 2:1. |

## Candidate rule areas

### Trend definition

Unknown in the source. Candidate pivot-based uptrend: the two most recent
confirmed swing highs increase and the two most recent confirmed swing lows
increase; reverse both inequalities for a downtrend. Mixed trends produce no
defined direction if that choice is selected. Equal pivots, window length,
and transitions need explicit rules.

### Swing-point definition options

- **Pivot:** at index `i`, a high is strictly greater than the `L` prior and
  `R` subsequent highs; a low is strictly less than the corresponding lows.
  The pivot becomes available only at close of bar `i + R`, avoiding lookahead.
  Specify whether equal values invalidate the pivot and what happens when
  a bar qualifies as both a high and a low.
- **Fractal:** a fixed symmetric pivot, for example two bars on each side;
  confirmation and tie rules still need to be fixed.
- **ZigZag:** a confirmed reversal of at least a fixed pip, percentage or ATR
  threshold; define the reference extreme, reversal confirmation, minimum
  separation and endpoint replacement. Do not backdate signal availability.

### Trendline construction options

Candidate A joins the two latest confirmed swing lows for a rising support
line or confirmed highs for a falling resistance line. Candidate B ranks
eligible pivot pairs by a fixed lookback, minimum separation and number of
validated touches, with deterministic tie-breakers. In both cases specify
whether x is bar index or elapsed time, the slope/intercept, line lifetime,
breaches between anchors, gaps, re-anchoring and zone/touch definitions.
Use only pivots confirmed by the decision bar.

### Stochastic configuration

The source settings and signal are unknown. A configurable formulation is
`raw K = 100 × (close - lowest low) / (highest high - lowest low)` over a
specified lookback. Specify whether the current completed bar is included,
how raw K is smoothed into K and D, smoothing types and lengths, warm-up,
rounding and zero-range behavior. A candidate bullish cross is
`K_previous <= D_previous` and `K_current > D_current`; a bearish cross
reverses the inequalities. Thresholds, signal window and whether confirmation
is a cross, level, or other condition remain unresolved.

### Entries

- **Long:** the transcript's trend direction, line type, interaction or
  breakout, and stochastic confirmation are unknown. Possible definitions
  must specify the ordered conditions, allowed signal window, trade timing
  and whether a touch, break or retest is required.
- **Short:** the corresponding trend, line type, direction, confirmation and
  ordering are unknown; a symmetric inverse is only one possible hypothesis.
- Define order type, decision bar, earliest fill time, bid/ask treatment,
  expiry, gap and conflicting-signal behavior. Do not use the completed
  decision bar's close as an executable price without an explicit simulation
  assumption.

### Stops, targets and exits

The requested 2:1 ratio alone does not determine the stop, entry or exit.
Choose an initial stop definition and buffer; set the target from its
positive price risk as described above if gross 2R is intended. Specify what
happens for zero or negative risk, minimum stop distance, stop/target gaps,
simultaneous intrabar touches, reversals, timeouts, final-bar liquidation
and whether protection can move. Include spread, commission, slippage and
financing in the execution model rather than silently treating gross 2R as
realized net return.

### Required parameters and unresolved ambiguities

Instrument, timeframe and data basis; swing method, lookback, confirmation and
ties; trend definition and history; line anchor selection, ranking, lifetime,
touch and breach rules; zone width and ATR formula if used; stochastic
lookback, smoothing, thresholds and confirmation window; entry trigger,
order type and timing; stop source and buffer; target basis; position sizing,
maximum simultaneous positions, costs and execution model; setup expiration;
gap and same-bar sequencing; warm-up and missing-data rules all require
decisions. Transcript-specific rules and language remain unknown until the
source is provided.

## Feasibility with the current framework

- **Fully automated?** In principle yes, once the missing choices are fixed
  and a deterministic, causal implementation is written. That is a
  feasibility statement, not validation of the strategy.
- **Objectively backtestable?** In principle yes, with recorded assumptions
  and suitable OHLC data. The current `scripts/backtest.py` is specifically
  V1: M5 timestamp validation, breakout signal, 10-pip stop, fixed spread,
  single position and exit logic are embedded in the runner. Its OHLC
  loader, output conventions and metrics may inform a separate candidate
  runner, but arbitrary trendline signals and variable-risk stops are not
  currently plug-in features. In particular its P&L in R uses the fixed
  V1 stop; reusing that calculation unchanged for variable risk would be
  incorrect. Intrabar order cannot be recovered from OHLC alone.
- **Same signals across independent implementations?** Not yet. Reproducible
  signals require fixed parameter values, exact formulas, timing, tie and
  warm-up conventions, precision and missing-data rules, and shared
  input/output test vectors. Confirmed pivots must not be used before their
  confirmation bars.

No candidate backtest or trading code is introduced by this document.
Provide the transcript before attributing rules to it or choosing among the
alternatives.

**INSUFFICIENTLY_DEFINED**
