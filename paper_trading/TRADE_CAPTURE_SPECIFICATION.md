# Breakout Scalping V1 — Demo Trade Capture Specification

## Record unit and eligibility

Store one row per **fully closed broker position**, not per signal, order
request, partial fill, or exit fragment. If the broker reports partial fills
or exits, aggregate them using quantity-weighted prices and total costs, while
retaining every raw broker execution reference. Mark `completed=true` only
after the account is flat and the record is reconciled.

Assign a unique, immutable `trade_id` before submitting an entry (for example,
`V1-DEMO-000001`). Never reuse an ID. Missed signals, rejected orders,
cancelled orders, and unfilled requests must be recorded in an incident/order
log, not counted as completed trades.

All timestamps must be ISO-8601 with an explicit offset. For MT5 demo records,
store the broker wall-clock values directly with the configured broker offset;
do not convert them to UTC. Preserve the raw broker export and record the
configured offset with the evidence. UTC timestamps remain acceptable only
when they are the actual source clock for non-MT5 historical data.

The offline V1 runner stores the signal bar's timestamp label in its
`signal_time` field, then uses that bar's close to evaluate the signal. Do not
copy that label as the signal-close time: the signal becomes known at the
following M5 boundary. Capture the bar label separately as
`signal_bar_open_time_broker` and record the completed-bar time as
`signal_time_broker`. Preserve the explicit broker offset on both values.

## Required fields

| Field | Type / format | Definition |
|---|---|---|
| `trade_id` | String, unique | Stable V1 demo position identifier; never reuse an ID. |
| `strategy_version` | String | Must be `Breakout Scalping V1`. |
| `account_type` | String | Must be `DEMO`; live-account records are rejected by the recorder and never count toward the gate. |
| `account_alias` | String | Non-sensitive identifier showing which demo account produced the trade. Never store credentials. |
| `broker` | String | Broker/platform name. |
| `symbol` | String | Broker's exact EURUSD symbol, including any documented suffix. |
| `timeframe` | String | Must be `M5`. |
| `signal_bar_open_time_broker` | ISO-8601 with explicit broker offset | Timestamp label of the M5 signal bar, retained to identify the exact bar. |
| `signal_time_broker` | ISO-8601 with explicit broker offset | Time the signal bar completed and its close became available, before the next-bar entry. |
| `entry_time_broker` | ISO-8601 with explicit broker offset | Actual first fill time; retain intended next-bar time separately in notes if different. |
| `exit_time_broker` | ISO-8601 with explicit broker offset | Time the broker position became fully flat. |
| `direction` | `long` / `short` | Position direction. |
| `signal_close` | Decimal price | Completed signal-bar close. |
| `prior_20_high` | Decimal price | Highest high of the 20 completed bars preceding the signal bar. |
| `prior_20_low` | Decimal price | Lowest low of the 20 completed bars preceding the signal bar. |
| `intended_entry` | Decimal price | Reference next-M5-bar-open price used for comparison; preserve whether it is bid or ask in the execution record. |
| `actual_entry` | Decimal price | Quantity-weighted average broker fill price for the complete entry. |
| `stop_price` | Decimal price | Initial V1 stop set from actual entry; preserve the originally accepted level. |
| `target_price` | Decimal price | Initial V1 target set from actual entry; preserve the originally accepted level. |
| `actual_exit` | Decimal price | Quantity-weighted average price for all fills that fully closed the position. |
| `entry_spread_pips` | Nonnegative decimal or `unavailable: reason` | Observed ask minus bid at entry, divided by 0.0001. Never substitute the backtest assumption. |
| `exit_spread_pips` | Nonnegative decimal or `unavailable: reason` | Observed ask minus bid at final exit, divided by 0.0001. |
| `gross_pnl_pips` | Decimal | Realized directional price P&L before commission, financing, and other fees, normalized to pips and quantity-weighted for partial fills. |
| `commission_pips` | Decimal | Total commission converted to pips using the realized trade P&L conversion basis; record currency/amount and conversion evidence in notes if conversion is unavailable. |
| `financing_pips` | Decimal | Swap/financing and other overnight charges converted to pips; zero only when confirmed none. |
| `slippage_pips` | Signed decimal | Difference between intended and actual execution, using a consistent adverse-positive convention documented in the notes. |
| `pnl_pips` | Decimal | **Net realized** P&L after commission, financing, and other fees. Use one consistent account-currency conversion method and record it. |
| `pnl_r` | Decimal | Net `pnl_pips` divided by the initial planned stop distance in pips (V1 is 10 pips); do not recompute risk from a later altered stop. |
| `hold_minutes` | Nonnegative decimal | Actual elapsed minutes from first entry fill to final flat time; preserve exact timestamps. |
| `exit_reason` | String | Broker-confirmed reason such as stop, target, manual/operational close, or other; an unplanned exit is a compliance deviation. |
| `order_reference` | String | Broker order/position/execution IDs; include references for partial fills and closes. |
| `completed` | Boolean | `true` only when fully flat, all required values are complete or explicitly marked unavailable with reason, and broker history is reconciled. |
| `rule_compliant` | Boolean | `true` only if signal, entry, single-position, stop/target, and management followed frozen V1. Explain any deviation in notes. |
| `notes` | Text | Data issues, execution discrepancies, costs/conversions, operational incidents, and evidence file references. Never credentials. |

Use decimal prices at the precision provided by the broker; do not round away
execution differences. EURUSD pip conversion uses 0.0001, consistent with the
frozen V1 specification.

## CSV mapping and current seed

[`DEMO_TRADING_LOG_SEED.csv`](./DEMO_TRADING_LOG_SEED.csv) preserves the
original incomplete blank header. The operational
[`DEMO_TRADING_LOG.csv`](./DEMO_TRADING_LOG.csv) uses the complete schema
below. The mandatory trade ID must not be hidden in free-text notes.

Recommended column order:

```csv
trade_id,strategy_version,account_type,account_alias,broker,symbol,timeframe,signal_bar_open_time_broker,signal_time_broker,entry_time_broker,exit_time_broker,direction,signal_close,prior_20_high,prior_20_low,intended_entry,actual_entry,stop_price,target_price,actual_exit,entry_spread_pips,exit_spread_pips,gross_pnl_pips,commission_pips,financing_pips,slippage_pips,pnl_pips,pnl_r,hold_minutes,exit_reason,order_reference,completed,rule_compliant,notes
```

Keep the raw broker export immutable. Corrections to the normalized log must
be traceable to the original value, corrected value, time, and reason.
