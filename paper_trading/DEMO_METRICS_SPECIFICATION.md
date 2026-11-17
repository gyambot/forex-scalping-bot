# Breakout Scalping V1 — Demo Metrics Specification

## Reporting scope

- Engineering validation trades are kept in a separate validation log and
  excluded from the formal study's trade count and performance metrics.
  Their isolated metrics are execution-test evidence, not study performance.
- Collection period: the first 100 **eligible, completed V1 demo positions**.
- Historical backtest/validation trades, signals without fills, rejected or
  cancelled orders, and open positions do not count.
- Use only records with `completed=true`, reconciled broker execution, and a
  unique `trade_id`. Report non-compliant positions separately; never hide
  them. State the eligible completed-trade count and data-quality exclusions
  with each report.
- Require `rule_compliant=true` for the 100-trade gate. Record and report
  deviations, but exclude them from the eligible gate count and primary V1
  metrics; show them separately.
- Resolve all commissions, financing, and other transaction costs before a
  record is gate-eligible. A position with pending costs may appear in a
  provisional operational report but must not advance the 100-trade count or
  enter finalized net metrics until reconciled.
- Report cumulative results after each completed trade and provide a final
  summary at 100. Do not stop early or selectively omit losing trades.
- Preserve net P&L after actual transaction costs. Do not use the historical
  backtest's fixed spread as a demo spread observation.

## Metric definitions

| Metric | Definition |
|---|---|
| Trade count | Number of unique eligible positions fully closed in the reporting period. A partial exit remains part of its open position and is not counted until flat. |
| Net profit | Sum of `pnl_pips` over eligible completed positions. Also record account-currency realized net P&L from broker statements and the account currency/conversion basis. |
| Win rate | Winning completed positions (`pnl_pips > 0`) divided by all eligible completed positions, multiplied by 100. Zero-P&L trades remain in the denominator and are not wins. |
| Profit factor | Sum of positive net `pnl_pips` divided by the absolute sum of negative net `pnl_pips`. If there are no losing trades, report `N/A (no losses)`, not an invented finite value. |
| Expectancy | Arithmetic mean of net `pnl_pips` per eligible completed trade. Also report mean `pnl_r` so results are comparable in risk units. |
| Maximum drawdown | Largest peak-to-subsequent-trough decline in cumulative net realized P&L, calculated in trade-close order from the 100-trade sequence. Report pips and account currency. State that this is realized, closed-trade drawdown and does not include intratrade equity drawdown unless separately captured. |
| Average hold time | Arithmetic mean of elapsed `hold_minutes` from first entry fill until the position is fully flat. |
| Average winner | Mean net `pnl_pips` for winning completed positions only. Report winner count; if none, report `N/A`. |
| Average loser | Mean net `pnl_pips` for losing completed positions only (a negative number). Report loser count; if none, report `N/A`. |
| Average trade | Mean net `pnl_pips` across all completed positions, including breakeven positions. This equals expectancy in pips. |
| Trades per demo day | Eligible completed positions divided by distinct broker-time calendar dates on which demo collection was active. State the active-day count; do not divide by all calendar days unless that is explicitly the chosen denominator. |
| Average spread | Arithmetic mean of observed entry and exit spreads separately, in pips, with observation counts and missing-data count. Do not substitute assumed/model spread for missing observations. |

## Calculation conventions

1. Use unrounded source values for calculations; round only displayed results
   (normally four decimals for pips/R and two for percentages).
2. P&L is net of commissions, financing, and other known charges. If a cost is
   pending, mark the record incomplete for final metrics and explain any
   provisional report.
3. `pnl_r` is net P&L in pips divided by the original V1 stop distance of 10
   pips. Report a different realized risk denominator only as a separate
   clearly labeled supplementary metric, not as a replacement.
4. Sort by actual final exit broker timestamp, with `trade_id` as a stable tie-breaker.
   Define cumulative P&L from zero and running peak as the maximum cumulative
   value reached, including the zero starting point. Drawdown is running peak
   minus cumulative P&L.
5. Position size does not change pips or R, but does affect account-currency
   P&L. Use actual broker conversion/statement figures for account-currency
   values.
6. Provide the reporting interval, strategy version, account alias, completed
   trade count, excluded/incomplete count, missing-cost/spread count, and any
   rule deviations alongside all metrics.

## Gate count

The gate count is the number of unique rows satisfying all of:

- `strategy_version = Breakout Scalping V1`
- `account_type = DEMO` and demo account alias is identified
- `completed = true`
- `rule_compliant = true`
- Position is fully closed and broker-reconciled
- Commissions, financing, and other transaction costs are resolved
- Required capture fields are present and valid
- `trade_id` is unique

Do not count historical trades or multiple partial fills/exits as multiple
trades. Show the count as `N / 100`; V2 eligibility remains blocked below 100.
