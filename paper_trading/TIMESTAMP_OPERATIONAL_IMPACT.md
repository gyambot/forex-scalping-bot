# Timestamp Operational Impact Review

> **Status update:** This review records the pre-migration operational
> conclusion. The project later replaced the UTC requirement with the
> explicit-offset broker-time contract documented in
> [BROKER_TIME_CONTRACT.md](./BROKER_TIME_CONTRACT.md). The code migration
> resolves the UTC-format dependency; it does not guarantee every manual
> entry is next-bar compliant or authorize trading.

## Conclusion

**DEMO_EXECUTION_BLOCKED**

The timestamp discrepancy does **not** enter V1's price-only breakout
calculation. If the same completed OHLC bars are evaluated in the same order,
the raw breakout signal, stop/target distances, and calculated outcome for a
fixed fill are unchanged by a uniform timestamp relabeling.

However, V1 also requires entry at the next M5 bar open. The current live
pipeline reports a raw candidate but does not determine or enforce that the
human entry occurred at that next bar. The timestamp discrepancy leaves that
timing unverified, and the capture validator does not independently prove
next-bar execution. Therefore a broker trade could be recorded, but the
current project cannot reliably establish that it is an eligible,
rule-compliant V1 demo trade. It must not be counted as evidence toward the
100-trade gate until this is verifiable.

## What calculations use timestamps?

### Price calculations and bar sequence

- `scripts/backtest.py` validates input timestamps as UTC, chronological,
  unique, and on M5 boundaries. Its breakout function itself reads only the
  signal bar close and the preceding 20 bars' highs/lows.
- The live engine validates chronological UTC bar labels, then invokes that
  same breakout function. It returns a raw signal candidate; it does not
  evaluate active-position eligibility or place an entry.
- Backtest entry selection uses the next item in the ordered bar sequence.
  Stop and target levels are calculated from the actual simulated entry price
  using the fixed 10-pip and 20-pip distances.
- The backtest outcome is evaluated from subsequent bar prices. Its hold
  duration is `bars_held * 5`, not a subtraction of bar timestamps.

Thus, for identical OHLC and sequence, a timestamp relabeling alone does not
change the price-only breakout, stop/target distance, or simulated price
outcome.

### Live observation and trade recording

- `signal_observer.py` deduplicates on the signal timestamp and checks that
  the bar timestamp is increasing. It also compares the expected bar close
  against its UTC observation clock and reports a timing anomaly beyond its
  tolerance. This is diagnostic: the observer still logs the signal and
  does not block a human from acting.
- The live engine's `get_live_v1_signal()` obtains the latest 21 completed
  bars and evaluates the latest one. It does not schedule or verify an entry
  at the next M5 open.
- `manual_trade_capture.py` validates timestamp ordering, the signal-bar
  label/close relationship, elapsed hold minutes, price levels, and a
  supplied `rule_compliant` value. It checks that entry is not before the
  signal close, but does not prove that entry occurred at the next M5 open.
- `generate_demo_metrics.py` sorts eligible trades by recorded exit time.
  Win/loss, net P&L, expectancy, profit factor, and drawdown are calculated
  from captured P&L values in that order. Trade count is based on records
  passing the gate eligibility predicate.

## Impact by requested measure

| Item | Effect of timestamp discrepancy alone | Operational risk in the current workflow |
|---|---|---|
| Breakout detection | No change if OHLC values and completed-bar sequence are the same. | Wrong/stale bar selection or timing can cause the human to act on a different signal opportunity; the live code does not verify next-bar eligibility. |
| Stop placement | No change to the 10-pip distance from actual entry. | If entry occurs on a different bar or at a different price, the absolute stop price changes with that actual fill; it remains a V1-compliant distance only if correctly set from that fill. |
| Target placement | No change to the 20-pip distance from actual entry. | Same dependency on correct entry timing and fill as the stop. |
| Win/loss outcome | A timestamp relabeling does not change the broker's realized trade result or a fixed-fill OHLC simulation. | Entering late or on the wrong bar can change the fill and subsequent price path, so the trade's realized outcome may differ from the intended V1 trade. |
| Trade count | No direct arithmetic effect on a fixed set of eligible records. | A trade entered outside the required next-bar timing may be noncompliant and excluded from the gate; current capture validation cannot independently establish this eligibility. |
| Expectancy | No change for the same eligible trades and same recorded P&L values. | Different or noncompliant entries change the captured P&L sample; they can alter expectancy or be excluded. |
| Profit factor | No change for the same eligible trades and same P&L values. | Different or noncompliant entries can change wins/losses and thus profit factor or eligibility. |
| Reporting/session labels | Recorded timestamps and reporting periods can be mislabeled; the backtest also groups active data days by timestamp date. | This is not the only concern: next-bar scheduling is itself part of V1's execution rule. |

## What would be incorrect if trades were collected today?

The system could store a broker trade and compute its observed P&L. It could
not, based on the current implementation alone, establish all of the
following:

1. The signal was acted on at the V1 next-M5-bar opening opportunity rather
   than after it had passed.
2. The recorded signal-close, entry, and exit timestamps unambiguously
   represent the required event times in the capture schema, whose fields
   are explicitly UTC.
3. The `rule_compliant` value reflects independently checked timing rather
   than a manual assertion.
4. The resulting record should count as a valid V1 demo trade for gate
   metrics.

The observer's anomaly is reported, not fail-closed. The manual capture's
timestamp checks are useful consistency checks but do not establish actual
next-bar entry. Consequently, resulting trade count, expectancy, and profit
factor could be correct as **descriptions of the trades actually made**, but
not trustworthy as V1-compliant evidence if timing deviations are
unrecognized.

## Disposition

The issue is not merely cosmetic reporting or session labeling. Absolute UTC
is not part of the breakout comparison, but the project requires next-bar
execution, and the current live/manual workflow cannot verify that rule
against the observed timestamps. This prevents safely collecting
**gate-eligible V1 evidence** today, even though it does not prevent
recording a broker trade as an operational incident or descriptive result.

Keep demo execution blocked until the next-bar timing for the live signal can
be verified and trade records can be assigned eligibility on that basis.
This review does not modify V1, alter timestamps, or authorize trades.
