# Weekly Review — Breakout Scalping V1

> Historical backtest breakdown, not live or demo performance. Fixed UTC session
> buckets and OHLC volatility are descriptive only; they do not authorize a
> strategy change. Actual variable spread is unavailable in bid-bar data.

- Data period: 2025-01-01 to 2025-12-31
- Completed trades reviewed: 2260
- Session buckets: Asia-Pacific 00-06 UTC; London 07-11 UTC; New York 12-20 UTC; Late 21-23 UTC (fixed UTC, no DST shift).
- Spread: V1 models a constant 1.0 pip; this report cannot measure historical or demo spread variation.
- Volatility proxy: mean M5 high-low range in pips per ISO week; not a strategy filter.
- Drawdown: trade-close cumulative P&L drawdown from the prior cumulative peak, in pips.

## Weekly reviews

### 2024-12-30 to 2025-01-05 (ISO 2025-W01)

- Completed trades: 17; net P&L: -50.00 pips; expectancy: -2.94 pips / -0.29 R.
- Required metrics: profit factor 0.62; win rate 23.53%; average trade -2.94 pips; average hold 112.06 min; trades/day 4.25; maximum trade-close drawdown this week 60.00 pips.
- Best session by net P&L: Asia-Pacific (00-06 UTC), -10.00 pips across 1 trades.
- Worst session by net P&L: London (07-11 UTC), -30.00 pips across 6 trades.
- Largest winners: short 20.00 pips (entry 2025-01-02T10:35:00+00:00); short 20.00 pips (entry 2025-01-02T14:50:00+00:00); short 20.00 pips (entry 2025-01-02T16:00:00+00:00)
- Largest losers: long -10.00 pips (entry 2025-01-02T01:45:00+00:00); short -10.00 pips (entry 2025-01-02T08:30:00+00:00); short -10.00 pips (entry 2025-01-02T10:50:00+00:00)
- Drawdown event: 60.00 pips from running peak 2025-01-02T16:05:00+00:00 to trough 2025-01-05T23:00:00+00:00.
- Volatility analysis: average M5 range 3.72 pips, below the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-01-06 to 2025-01-12 (ISO 2025-W02)

- Completed trades: 36; net P&L: -60.00 pips; expectancy: -1.67 pips / -0.17 R.
- Required metrics: profit factor 0.77; win rate 27.78%; average trade -1.67 pips; average hold 123.33 min; trades/day 6.00; maximum trade-close drawdown this week 130.00 pips.
- Best session by net P&L: Asia-Pacific (00-06 UTC), 40.00 pips across 2 trades.
- Worst session by net P&L: New York (12-20 UTC), -120.00 pips across 15 trades.
- Largest winners: long 20.00 pips (entry 2025-01-06T01:20:00+00:00); long 20.00 pips (entry 2025-01-06T08:05:00+00:00); long 20.00 pips (entry 2025-01-06T11:15:00+00:00)
- Largest losers: long -10.00 pips (entry 2025-01-05T23:50:00+00:00); long -10.00 pips (entry 2025-01-06T09:10:00+00:00); short -10.00 pips (entry 2025-01-06T10:50:00+00:00)
- Drawdown event: 130.00 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-01-10T19:40:00+00:00.
- Volatility analysis: average M5 range 4.08 pips, above the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-01-13 to 2025-01-19 (ISO 2025-W03)

- Completed trades: 44; net P&L: -170.00 pips; expectancy: -3.86 pips / -0.39 R.
- Required metrics: profit factor 0.51; win rate 20.45%; average trade -3.86 pips; average hold 94.09 min; trades/day 7.33; maximum trade-close drawdown this week 300.00 pips.
- Best session by net P&L: Late (21-23 UTC), 30.00 pips across 3 trades.
- Worst session by net P&L: London (07-11 UTC), -110.00 pips across 11 trades.
- Largest winners: short 20.00 pips (entry 2025-01-13T03:10:00+00:00); long 20.00 pips (entry 2025-01-13T16:35:00+00:00); long 20.00 pips (entry 2025-01-13T21:50:00+00:00)
- Largest losers: short -10.00 pips (entry 2025-01-13T00:50:00+00:00); short -10.00 pips (entry 2025-01-13T04:35:00+00:00); long -10.00 pips (entry 2025-01-13T06:05:00+00:00)
- Drawdown event: 300.00 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-01-17T18:25:00+00:00.
- Volatility analysis: average M5 range 4.11 pips, above the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-01-20 to 2025-01-26 (ISO 2025-W04)

- Completed trades: 48; net P&L: 30.00 pips; expectancy: 0.62 pips / 0.06 R.
- Required metrics: profit factor 1.10; win rate 35.42%; average trade 0.62 pips; average hold 114.27 min; trades/day 8.00; maximum trade-close drawdown this week 330.00 pips.
- Best session by net P&L: New York (12-20 UTC), 70.00 pips across 20 trades.
- Worst session by net P&L: Late (21-23 UTC), -60.00 pips across 6 trades.
- Largest winners: long 20.00 pips (entry 2025-01-20T02:00:00+00:00); long 20.00 pips (entry 2025-01-20T06:55:00+00:00); short 20.00 pips (entry 2025-01-20T17:15:00+00:00)
- Largest losers: short -10.00 pips (entry 2025-01-17T19:20:00+00:00); long -10.00 pips (entry 2025-01-20T00:15:00+00:00); long -10.00 pips (entry 2025-01-20T13:35:00+00:00)
- Drawdown event: 330.00 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-01-23T13:50:00+00:00.
- Volatility analysis: average M5 range 4.47 pips, above the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-01-27 to 2025-02-02 (ISO 2025-W05)

- Completed trades: 55; net P&L: -130.00 pips; expectancy: -2.36 pips / -0.24 R.
- Required metrics: profit factor 0.68; win rate 25.45%; average trade -2.36 pips; average hold 91.27 min; trades/day 9.17; maximum trade-close drawdown this week 400.00 pips.
- Best session by net P&L: London (07-11 UTC), 0.00 pips across 15 trades.
- Worst session by net P&L: New York (12-20 UTC), -70.00 pips across 22 trades.
- Largest winners: short 20.00 pips (entry 2025-01-26T22:05:00+00:00); long 20.00 pips (entry 2025-01-27T08:15:00+00:00); long 20.00 pips (entry 2025-01-27T10:05:00+00:00)
- Largest losers: short -10.00 pips (entry 2025-01-27T05:10:00+00:00); long -10.00 pips (entry 2025-01-27T07:45:00+00:00); long -10.00 pips (entry 2025-01-27T09:15:00+00:00)
- Drawdown event: 400.00 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-01-31T15:50:00+00:00.
- Volatility analysis: average M5 range 4.47 pips, above the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-02-03 to 2025-02-09 (ISO 2025-W06)

- Completed trades: 46; net P&L: -100.00 pips; expectancy: -2.17 pips / -0.22 R.
- Required metrics: profit factor 0.71; win rate 26.09%; average trade -2.17 pips; average hold 99.13 min; trades/day 7.67; maximum trade-close drawdown this week 500.00 pips.
- Best session by net P&L: Asia-Pacific (00-06 UTC), 0.00 pips across 12 trades.
- Worst session by net P&L: New York (12-20 UTC), -70.00 pips across 19 trades.
- Largest winners: long 20.00 pips (entry 2025-02-03T11:50:00+00:00); long 20.00 pips (entry 2025-02-03T21:20:00+00:00); short 20.00 pips (entry 2025-02-04T00:00:00+00:00)
- Largest losers: short -10.00 pips (entry 2025-02-03T00:25:00+00:00); short -10.00 pips (entry 2025-02-03T02:55:00+00:00); long -10.00 pips (entry 2025-02-03T05:55:00+00:00)
- Drawdown event: 500.00 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-02-09T22:15:00+00:00.
- Volatility analysis: average M5 range 4.73 pips, above the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-02-10 to 2025-02-16 (ISO 2025-W07)

- Completed trades: 37; net P&L: 50.00 pips; expectancy: 1.35 pips / 0.14 R.
- Required metrics: profit factor 1.22; win rate 37.84%; average trade 1.35 pips; average hold 156.35 min; trades/day 6.17; maximum trade-close drawdown this week 520.00 pips.
- Best session by net P&L: New York (12-20 UTC), 90.00 pips across 21 trades.
- Worst session by net P&L: Late (21-23 UTC), -40.00 pips across 4 trades.
- Largest winners: long 20.00 pips (entry 2025-02-10T03:35:00+00:00); short 20.00 pips (entry 2025-02-10T12:00:00+00:00); long 20.00 pips (entry 2025-02-11T06:30:00+00:00)
- Largest losers: long -10.00 pips (entry 2025-02-09T23:55:00+00:00); short -10.00 pips (entry 2025-02-10T01:45:00+00:00); long -10.00 pips (entry 2025-02-10T09:15:00+00:00)
- Drawdown event: 520.00 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-02-10T03:35:00+00:00.
- Volatility analysis: average M5 range 3.66 pips, below the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-02-17 to 2025-02-23 (ISO 2025-W08)

- Completed trades: 29; net P&L: -80.00 pips; expectancy: -2.76 pips / -0.28 R.
- Required metrics: profit factor 0.64; win rate 24.14%; average trade -2.76 pips; average hold 232.07 min; trades/day 4.83; maximum trade-close drawdown this week 530.00 pips.
- Best session by net P&L: Asia-Pacific (00-06 UTC), 0.00 pips across 6 trades.
- Worst session by net P&L: New York (12-20 UTC), -60.00 pips across 15 trades.
- Largest winners: short 20.00 pips (entry 2025-02-17T03:25:00+00:00); short 20.00 pips (entry 2025-02-18T01:15:00+00:00); short 20.00 pips (entry 2025-02-19T08:55:00+00:00)
- Largest losers: short -10.00 pips (entry 2025-02-14T19:50:00+00:00); long -10.00 pips (entry 2025-02-17T01:55:00+00:00); short -10.00 pips (entry 2025-02-17T08:30:00+00:00)
- Drawdown event: 530.00 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-02-23T22:45:00+00:00.
- Volatility analysis: average M5 range 3.08 pips, below the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-02-24 to 2025-03-02 (ISO 2025-W09)

- Completed trades: 38; net P&L: -95.10 pips; expectancy: -2.50 pips / -0.25 R.
- Required metrics: profit factor 0.68; win rate 26.32%; average trade -2.50 pips; average hold 146.58 min; trades/day 6.33; maximum trade-close drawdown this week 625.10 pips.
- Best session by net P&L: London (07-11 UTC), 10.00 pips across 8 trades.
- Worst session by net P&L: New York (12-20 UTC), -55.10 pips across 19 trades.
- Largest winners: long 20.00 pips (entry 2025-02-23T22:45:00+00:00); long 20.00 pips (entry 2025-02-24T00:25:00+00:00); short 20.00 pips (entry 2025-02-24T07:40:00+00:00)
- Largest losers: short -25.10 pips (entry 2025-02-28T18:20:00+00:00); long -10.00 pips (entry 2025-02-24T01:45:00+00:00); short -10.00 pips (entry 2025-02-24T06:45:00+00:00)
- Drawdown event: 625.10 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-03-02T22:05:00+00:00.
- Volatility analysis: average M5 range 3.64 pips, below the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-03-03 to 2025-03-09 (ISO 2025-W10)

- Completed trades: 67; net P&L: -70.00 pips; expectancy: -1.04 pips / -0.10 R.
- Required metrics: profit factor 0.85; win rate 29.85%; average trade -1.04 pips; average hold 70.75 min; trades/day 11.17; maximum trade-close drawdown this week 695.10 pips.
- Best session by net P&L: New York (12-20 UTC), 30.00 pips across 27 trades.
- Worst session by net P&L: Late (21-23 UTC), -70.00 pips across 7 trades.
- Largest winners: long 20.00 pips (entry 2025-03-03T09:10:00+00:00); long 20.00 pips (entry 2025-03-03T10:05:00+00:00); long 20.00 pips (entry 2025-03-03T12:05:00+00:00)
- Largest losers: long -10.00 pips (entry 2025-03-02T22:05:00+00:00); short -10.00 pips (entry 2025-03-03T08:40:00+00:00); long -10.00 pips (entry 2025-03-03T15:30:00+00:00)
- Drawdown event: 695.10 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-03-09T22:20:00+00:00.
- Volatility analysis: average M5 range 5.73 pips, above the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-03-10 to 2025-03-16 (ISO 2025-W11)

- Completed trades: 49; net P&L: -40.00 pips; expectancy: -0.82 pips / -0.08 R.
- Required metrics: profit factor 0.88; win rate 30.61%; average trade -0.82 pips; average hold 104.29 min; trades/day 8.17; maximum trade-close drawdown this week 775.10 pips.
- Best session by net P&L: London (07-11 UTC), 30.00 pips across 15 trades.
- Worst session by net P&L: New York (12-20 UTC), -40.00 pips across 22 trades.
- Largest winners: short 20.00 pips (entry 2025-03-10T02:10:00+00:00); long 20.00 pips (entry 2025-03-10T09:25:00+00:00); long 20.00 pips (entry 2025-03-10T20:00:00+00:00)
- Largest losers: long -10.00 pips (entry 2025-03-09T23:15:00+00:00); short -10.00 pips (entry 2025-03-10T05:05:00+00:00); long -10.00 pips (entry 2025-03-10T06:10:00+00:00)
- Drawdown event: 775.10 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-03-12T12:35:00+00:00.
- Volatility analysis: average M5 range 4.70 pips, above the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-03-17 to 2025-03-23 (ISO 2025-W12)

- Completed trades: 41; net P&L: -80.00 pips; expectancy: -1.95 pips / -0.20 R.
- Required metrics: profit factor 0.73; win rate 26.83%; average trade -1.95 pips; average hold 139.63 min; trades/day 6.83; maximum trade-close drawdown this week 815.10 pips.
- Best session by net P&L: Asia-Pacific (00-06 UTC), 0.00 pips across 9 trades.
- Worst session by net P&L: New York (12-20 UTC), -40.00 pips across 16 trades.
- Largest winners: long 20.00 pips (entry 2025-03-17T09:40:00+00:00); long 20.00 pips (entry 2025-03-18T06:55:00+00:00); short 20.00 pips (entry 2025-03-18T11:40:00+00:00)
- Largest losers: short -10.00 pips (entry 2025-03-16T21:05:00+00:00); long -10.00 pips (entry 2025-03-17T01:45:00+00:00); short -10.00 pips (entry 2025-03-17T03:25:00+00:00)
- Drawdown event: 815.10 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-03-21T12:55:00+00:00.
- Volatility analysis: average M5 range 3.86 pips, above the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-03-24 to 2025-03-30 (ISO 2025-W13)

- Completed trades: 37; net P&L: -10.00 pips; expectancy: -0.27 pips / -0.03 R.
- Required metrics: profit factor 0.96; win rate 32.43%; average trade -0.27 pips; average hold 152.84 min; trades/day 6.17; maximum trade-close drawdown this week 835.10 pips.
- Best session by net P&L: New York (12-20 UTC), 30.00 pips across 18 trades.
- Worst session by net P&L: London (07-11 UTC), -30.00 pips across 12 trades.
- Largest winners: long 20.00 pips (entry 2025-03-23T22:05:00+00:00); short 20.00 pips (entry 2025-03-24T11:55:00+00:00); short 20.00 pips (entry 2025-03-24T13:50:00+00:00)
- Largest losers: long -10.00 pips (entry 2025-03-24T06:45:00+00:00); long -10.00 pips (entry 2025-03-24T08:25:00+00:00); short -10.00 pips (entry 2025-03-24T09:20:00+00:00)
- Drawdown event: 835.10 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-03-24T11:35:00+00:00.
- Volatility analysis: average M5 range 3.87 pips, above the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-03-31 to 2025-04-06 (ISO 2025-W14)

- Completed trades: 65; net P&L: -20.00 pips; expectancy: -0.31 pips / -0.03 R.
- Required metrics: profit factor 0.95; win rate 32.31%; average trade -0.31 pips; average hold 62.62 min; trades/day 10.83; maximum trade-close drawdown this week 1,045.10 pips.
- Best session by net P&L: New York (12-20 UTC), 50.00 pips across 22 trades.
- Worst session by net P&L: Late (21-23 UTC), -50.00 pips across 8 trades.
- Largest winners: long 20.00 pips (entry 2025-04-02T13:30:00+00:00); long 20.00 pips (entry 2025-04-02T15:45:00+00:00); long 20.00 pips (entry 2025-04-03T00:05:00+00:00)
- Largest losers: short -10.00 pips (entry 2025-03-30T22:40:00+00:00); long -10.00 pips (entry 2025-03-31T01:15:00+00:00); short -10.00 pips (entry 2025-03-31T09:20:00+00:00)
- Drawdown event: 1,045.10 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-04-02T11:35:00+00:00.
- Volatility analysis: average M5 range 6.83 pips, above the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-04-07 to 2025-04-13 (ISO 2025-W15)

- Completed trades: 116; net P&L: 40.00 pips; expectancy: 0.34 pips / 0.03 R.
- Required metrics: profit factor 1.05; win rate 34.48%; average trade 0.34 pips; average hold 23.71 min; trades/day 19.33; maximum trade-close drawdown this week 925.10 pips.
- Best session by net P&L: London (07-11 UTC), 80.00 pips across 31 trades.
- Worst session by net P&L: New York (12-20 UTC), -110.00 pips across 44 trades.
- Largest winners: long 20.00 pips (entry 2025-04-06T23:20:00+00:00); short 20.00 pips (entry 2025-04-07T03:25:00+00:00); long 20.00 pips (entry 2025-04-07T05:15:00+00:00)
- Largest losers: long -10.00 pips (entry 2025-04-07T00:15:00+00:00); short -10.00 pips (entry 2025-04-07T01:05:00+00:00); long -10.00 pips (entry 2025-04-07T02:50:00+00:00)
- Drawdown event: 925.10 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-04-08T15:55:00+00:00.
- Volatility analysis: average M5 range 10.57 pips, above the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-04-14 to 2025-04-20 (ISO 2025-W16)

- Completed trades: 66; net P&L: -180.00 pips; expectancy: -2.73 pips / -0.27 R.
- Required metrics: profit factor 0.64; win rate 24.24%; average trade -2.73 pips; average hold 58.03 min; trades/day 11.00; maximum trade-close drawdown this week 985.10 pips.
- Best session by net P&L: Asia-Pacific (00-06 UTC), 10.00 pips across 20 trades.
- Worst session by net P&L: New York (12-20 UTC), -100.00 pips across 25 trades.
- Largest winners: long 20.00 pips (entry 2025-04-14T02:15:00+00:00); long 20.00 pips (entry 2025-04-14T07:10:00+00:00); short 20.00 pips (entry 2025-04-14T13:15:00+00:00)
- Largest losers: long -10.00 pips (entry 2025-04-14T01:10:00+00:00); long -10.00 pips (entry 2025-04-14T02:40:00+00:00); short -10.00 pips (entry 2025-04-14T04:00:00+00:00)
- Drawdown event: 985.10 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-04-20T23:30:00+00:00.
- Volatility analysis: average M5 range 6.41 pips, above the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-04-21 to 2025-04-27 (ISO 2025-W17)

- Completed trades: 71; net P&L: -140.00 pips; expectancy: -1.97 pips / -0.20 R.
- Required metrics: profit factor 0.73; win rate 26.76%; average trade -1.97 pips; average hold 48.87 min; trades/day 11.83; maximum trade-close drawdown this week 1,125.10 pips.
- Best session by net P&L: Asia-Pacific (00-06 UTC), 30.00 pips across 21 trades.
- Worst session by net P&L: New York (12-20 UTC), -160.00 pips across 25 trades.
- Largest winners: long 20.00 pips (entry 2025-04-21T00:05:00+00:00); long 20.00 pips (entry 2025-04-21T03:20:00+00:00); long 20.00 pips (entry 2025-04-21T08:45:00+00:00)
- Largest losers: long -10.00 pips (entry 2025-04-21T01:10:00+00:00); long -10.00 pips (entry 2025-04-21T03:30:00+00:00); long -10.00 pips (entry 2025-04-21T06:35:00+00:00)
- Drawdown event: 1,125.10 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-04-25T15:00:00+00:00.
- Volatility analysis: average M5 range 6.53 pips, above the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-04-28 to 2025-05-04 (ISO 2025-W18)

- Completed trades: 61; net P&L: -190.00 pips; expectancy: -3.11 pips / -0.31 R.
- Required metrics: profit factor 0.60; win rate 22.95%; average trade -3.11 pips; average hold 70.49 min; trades/day 10.17; maximum trade-close drawdown this week 1,365.10 pips.
- Best session by net P&L: Asia-Pacific (00-06 UTC), -20.00 pips across 14 trades.
- Worst session by net P&L: New York (12-20 UTC), -100.00 pips across 31 trades.
- Largest winners: short 20.00 pips (entry 2025-04-28T07:40:00+00:00); long 20.00 pips (entry 2025-04-28T15:35:00+00:00); short 20.00 pips (entry 2025-04-29T00:10:00+00:00)
- Largest losers: short -10.00 pips (entry 2025-04-25T21:00:00+00:00); long -10.00 pips (entry 2025-04-28T05:55:00+00:00); short -10.00 pips (entry 2025-04-28T08:00:00+00:00)
- Drawdown event: 1,365.10 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-05-02T02:50:00+00:00.
- Volatility analysis: average M5 range 5.40 pips, above the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-05-05 to 2025-05-11 (ISO 2025-W19)

- Completed trades: 68; net P&L: -200.00 pips; expectancy: -2.94 pips / -0.29 R.
- Required metrics: profit factor 0.62; win rate 23.53%; average trade -2.94 pips; average hold 58.16 min; trades/day 11.33; maximum trade-close drawdown this week 1,545.10 pips.
- Best session by net P&L: Asia-Pacific (00-06 UTC), -20.00 pips across 17 trades.
- Worst session by net P&L: London (07-11 UTC), -80.00 pips across 14 trades.
- Largest winners: long 20.00 pips (entry 2025-05-05T00:35:00+00:00); long 20.00 pips (entry 2025-05-05T10:05:00+00:00); short 20.00 pips (entry 2025-05-05T16:35:00+00:00)
- Largest losers: long -10.00 pips (entry 2025-05-04T23:40:00+00:00); long -10.00 pips (entry 2025-05-05T02:25:00+00:00); long -10.00 pips (entry 2025-05-05T03:25:00+00:00)
- Drawdown event: 1,545.10 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-05-09T06:35:00+00:00.
- Volatility analysis: average M5 range 5.33 pips, above the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-05-12 to 2025-05-18 (ISO 2025-W20)

- Completed trades: 61; net P&L: -160.00 pips; expectancy: -2.62 pips / -0.26 R.
- Required metrics: profit factor 0.65; win rate 24.59%; average trade -2.62 pips; average hold 73.20 min; trades/day 10.17; maximum trade-close drawdown this week 1,725.10 pips.
- Best session by net P&L: Late (21-23 UTC), 0.00 pips across 3 trades.
- Worst session by net P&L: London (07-11 UTC), -80.00 pips across 20 trades.
- Largest winners: short 20.00 pips (entry 2025-05-12T08:15:00+00:00); short 20.00 pips (entry 2025-05-12T11:10:00+00:00); short 20.00 pips (entry 2025-05-12T16:45:00+00:00)
- Largest losers: long -10.00 pips (entry 2025-05-12T00:15:00+00:00); short -10.00 pips (entry 2025-05-12T02:30:00+00:00); short -10.00 pips (entry 2025-05-12T06:15:00+00:00)
- Drawdown event: 1,725.10 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-05-16T14:50:00+00:00.
- Volatility analysis: average M5 range 5.24 pips, above the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-05-19 to 2025-05-25 (ISO 2025-W21)

- Completed trades: 60; net P&L: 90.00 pips; expectancy: 1.50 pips / 0.15 R.
- Required metrics: profit factor 1.24; win rate 38.33%; average trade 1.50 pips; average hold 81.17 min; trades/day 10.00; maximum trade-close drawdown this week 1,685.10 pips.
- Best session by net P&L: London (07-11 UTC), 90.00 pips across 18 trades.
- Worst session by net P&L: Asia-Pacific (00-06 UTC), -30.00 pips across 15 trades.
- Largest winners: long 20.00 pips (entry 2025-05-18T22:05:00+00:00); long 20.00 pips (entry 2025-05-19T07:10:00+00:00); long 20.00 pips (entry 2025-05-19T07:35:00+00:00)
- Largest losers: long -10.00 pips (entry 2025-05-19T01:55:00+00:00); short -10.00 pips (entry 2025-05-19T02:35:00+00:00); long -10.00 pips (entry 2025-05-19T05:30:00+00:00)
- Drawdown event: 1,685.10 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-05-19T06:50:00+00:00.
- Volatility analysis: average M5 range 4.93 pips, above the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-05-26 to 2025-06-01 (ISO 2025-W22)

- Completed trades: 46; net P&L: -10.00 pips; expectancy: -0.22 pips / -0.02 R.
- Required metrics: profit factor 0.97; win rate 32.61%; average trade -0.22 pips; average hold 110.22 min; trades/day 7.67; maximum trade-close drawdown this week 1,595.10 pips.
- Best session by net P&L: New York (12-20 UTC), 50.00 pips across 16 trades.
- Worst session by net P&L: London (07-11 UTC), -30.00 pips across 12 trades.
- Largest winners: long 20.00 pips (entry 2025-05-23T21:10:00+00:00); long 20.00 pips (entry 2025-05-26T01:25:00+00:00); short 20.00 pips (entry 2025-05-26T08:15:00+00:00)
- Largest losers: long -10.00 pips (entry 2025-05-26T02:55:00+00:00); short -10.00 pips (entry 2025-05-26T05:35:00+00:00); short -10.00 pips (entry 2025-05-26T06:35:00+00:00)
- Drawdown event: 1,595.10 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-05-30T15:15:00+00:00.
- Volatility analysis: average M5 range 4.56 pips, above the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-06-02 to 2025-06-08 (ISO 2025-W23)

- Completed trades: 48; net P&L: -150.10 pips; expectancy: -3.13 pips / -0.31 R.
- Required metrics: profit factor 0.59; win rate 22.92%; average trade -3.13 pips; average hold 103.65 min; trades/day 8.00; maximum trade-close drawdown this week 1,745.20 pips.
- Best session by net P&L: London (07-11 UTC), -40.00 pips across 10 trades.
- Worst session by net P&L: Asia-Pacific (00-06 UTC), -60.10 pips across 15 trades.
- Largest winners: long 20.00 pips (entry 2025-05-30T16:00:00+00:00); long 20.00 pips (entry 2025-06-02T06:40:00+00:00); long 20.00 pips (entry 2025-06-02T07:35:00+00:00)
- Largest losers: long -10.10 pips (entry 2025-06-05T00:25:00+00:00); long -10.00 pips (entry 2025-06-02T01:20:00+00:00); short -10.00 pips (entry 2025-06-02T04:00:00+00:00)
- Drawdown event: 1,745.20 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-06-06T21:55:00+00:00.
- Volatility analysis: average M5 range 4.34 pips, above the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-06-09 to 2025-06-15 (ISO 2025-W24)

- Completed trades: 46; net P&L: 20.00 pips; expectancy: 0.43 pips / 0.04 R.
- Required metrics: profit factor 1.07; win rate 34.78%; average trade 0.43 pips; average hold 117.17 min; trades/day 7.67; maximum trade-close drawdown this week 1,765.20 pips.
- Best session by net P&L: London (07-11 UTC), 70.00 pips across 14 trades.
- Worst session by net P&L: Asia-Pacific (00-06 UTC), -40.00 pips across 16 trades.
- Largest winners: long 20.00 pips (entry 2025-06-09T02:25:00+00:00); short 20.00 pips (entry 2025-06-09T11:25:00+00:00); long 20.00 pips (entry 2025-06-09T16:05:00+00:00)
- Largest losers: long -10.00 pips (entry 2025-06-08T23:10:00+00:00); short -10.00 pips (entry 2025-06-09T02:00:00+00:00); long -10.00 pips (entry 2025-06-09T09:40:00+00:00)
- Drawdown event: 1,765.20 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-06-09T02:15:00+00:00.
- Volatility analysis: average M5 range 4.72 pips, above the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-06-16 to 2025-06-22 (ISO 2025-W25)

- Completed trades: 42; net P&L: -60.00 pips; expectancy: -1.43 pips / -0.14 R.
- Required metrics: profit factor 0.80; win rate 28.57%; average trade -1.43 pips; average hold 140.83 min; trades/day 7.00; maximum trade-close drawdown this week 1,795.20 pips.
- Best session by net P&L: Asia-Pacific (00-06 UTC), 20.00 pips across 7 trades.
- Worst session by net P&L: London (07-11 UTC), -50.00 pips across 8 trades.
- Largest winners: short 20.00 pips (entry 2025-06-13T18:20:00+00:00); long 20.00 pips (entry 2025-06-16T05:35:00+00:00); long 20.00 pips (entry 2025-06-16T07:55:00+00:00)
- Largest losers: long -10.00 pips (entry 2025-06-16T06:30:00+00:00); long -10.00 pips (entry 2025-06-16T14:10:00+00:00); long -10.00 pips (entry 2025-06-16T15:05:00+00:00)
- Drawdown event: 1,795.20 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-06-20T20:55:00+00:00.
- Volatility analysis: average M5 range 4.54 pips, above the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-06-23 to 2025-06-29 (ISO 2025-W26)

- Completed trades: 56; net P&L: 10.00 pips; expectancy: 0.18 pips / 0.02 R.
- Required metrics: profit factor 1.03; win rate 33.93%; average trade 0.18 pips; average hold 86.16 min; trades/day 9.33; maximum trade-close drawdown this week 1,805.20 pips.
- Best session by net P&L: New York (12-20 UTC), 30.00 pips across 27 trades.
- Worst session by net P&L: Asia-Pacific (00-06 UTC), -50.00 pips across 14 trades.
- Largest winners: long 20.00 pips (entry 2025-06-23T03:00:00+00:00); short 20.00 pips (entry 2025-06-23T08:15:00+00:00); long 20.00 pips (entry 2025-06-23T14:40:00+00:00)
- Largest losers: long -10.00 pips (entry 2025-06-23T00:20:00+00:00); short -10.00 pips (entry 2025-06-23T02:20:00+00:00); long -10.00 pips (entry 2025-06-23T06:50:00+00:00)
- Drawdown event: 1,805.20 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-06-23T02:50:00+00:00.
- Volatility analysis: average M5 range 4.77 pips, above the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-06-30 to 2025-07-06 (ISO 2025-W27)

- Completed trades: 44; net P&L: -110.00 pips; expectancy: -2.50 pips / -0.25 R.
- Required metrics: profit factor 0.67; win rate 25.00%; average trade -2.50 pips; average hold 107.84 min; trades/day 7.33; maximum trade-close drawdown this week 1,885.20 pips.
- Best session by net P&L: New York (12-20 UTC), 0.00 pips across 18 trades.
- Worst session by net P&L: Asia-Pacific (00-06 UTC), -60.00 pips across 15 trades.
- Largest winners: long 20.00 pips (entry 2025-06-30T05:50:00+00:00); long 20.00 pips (entry 2025-06-30T15:15:00+00:00); long 20.00 pips (entry 2025-06-30T19:20:00+00:00)
- Largest losers: long -10.00 pips (entry 2025-06-30T00:05:00+00:00); short -10.00 pips (entry 2025-06-30T01:40:00+00:00); long -10.00 pips (entry 2025-06-30T02:35:00+00:00)
- Drawdown event: 1,885.20 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-07-04T14:55:00+00:00.
- Volatility analysis: average M5 range 3.94 pips, above the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-07-07 to 2025-07-13 (ISO 2025-W28)

- Completed trades: 37; net P&L: -70.00 pips; expectancy: -1.89 pips / -0.19 R.
- Required metrics: profit factor 0.74; win rate 27.03%; average trade -1.89 pips; average hold 170.54 min; trades/day 6.17; maximum trade-close drawdown this week 1,965.20 pips.
- Best session by net P&L: Late (21-23 UTC), 30.00 pips across 3 trades.
- Worst session by net P&L: New York (12-20 UTC), -70.00 pips across 19 trades.
- Largest winners: short 20.00 pips (entry 2025-07-07T02:45:00+00:00); short 20.00 pips (entry 2025-07-07T08:10:00+00:00); long 20.00 pips (entry 2025-07-07T23:05:00+00:00)
- Largest losers: long -10.00 pips (entry 2025-07-04T14:55:00+00:00); short -10.00 pips (entry 2025-07-07T09:55:00+00:00); long -10.00 pips (entry 2025-07-07T14:30:00+00:00)
- Drawdown event: 1,965.20 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-07-11T17:10:00+00:00.
- Volatility analysis: average M5 range 3.71 pips, below the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-07-14 to 2025-07-20 (ISO 2025-W29)

- Completed trades: 41; net P&L: -50.00 pips; expectancy: -1.22 pips / -0.12 R.
- Required metrics: profit factor 0.83; win rate 29.27%; average trade -1.22 pips; average hold 146.71 min; trades/day 6.83; maximum trade-close drawdown this week 2,085.20 pips.
- Best session by net P&L: New York (12-20 UTC), 30.00 pips across 24 trades.
- Worst session by net P&L: Asia-Pacific (00-06 UTC), -70.00 pips across 7 trades.
- Largest winners: short 20.00 pips (entry 2025-07-15T14:35:00+00:00); short 20.00 pips (entry 2025-07-15T15:25:00+00:00); short 20.00 pips (entry 2025-07-16T14:20:00+00:00)
- Largest losers: long -10.00 pips (entry 2025-07-14T01:00:00+00:00); short -10.00 pips (entry 2025-07-14T03:45:00+00:00); short -10.00 pips (entry 2025-07-14T06:00:00+00:00)
- Drawdown event: 2,085.20 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-07-16T13:35:00+00:00.
- Volatility analysis: average M5 range 3.83 pips, above the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-07-21 to 2025-07-27 (ISO 2025-W30)

- Completed trades: 37; net P&L: -40.00 pips; expectancy: -1.08 pips / -0.11 R.
- Required metrics: profit factor 0.85; win rate 29.73%; average trade -1.08 pips; average hold 160.14 min; trades/day 6.17; maximum trade-close drawdown this week 2,065.20 pips.
- Best session by net P&L: London (07-11 UTC), 20.00 pips across 7 trades.
- Worst session by net P&L: Late (21-23 UTC), -20.00 pips across 2 trades.
- Largest winners: long 20.00 pips (entry 2025-07-21T06:35:00+00:00); long 20.00 pips (entry 2025-07-21T12:10:00+00:00); long 20.00 pips (entry 2025-07-21T15:05:00+00:00)
- Largest losers: long -10.00 pips (entry 2025-07-21T01:05:00+00:00); short -10.00 pips (entry 2025-07-21T01:45:00+00:00); long -10.00 pips (entry 2025-07-21T16:05:00+00:00)
- Drawdown event: 2,065.20 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-07-25T16:45:00+00:00.
- Volatility analysis: average M5 range 3.71 pips, below the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-07-28 to 2025-08-03 (ISO 2025-W31)

- Completed trades: 59; net P&L: 40.00 pips; expectancy: 0.68 pips / 0.07 R.
- Required metrics: profit factor 1.11; win rate 35.59%; average trade 0.68 pips; average hold 97.29 min; trades/day 9.83; maximum trade-close drawdown this week 2,055.20 pips.
- Best session by net P&L: London (07-11 UTC), 70.00 pips across 14 trades.
- Worst session by net P&L: Late (21-23 UTC), -40.00 pips across 4 trades.
- Largest winners: short 20.00 pips (entry 2025-07-28T06:15:00+00:00); short 20.00 pips (entry 2025-07-28T07:25:00+00:00); short 20.00 pips (entry 2025-07-28T08:35:00+00:00)
- Largest losers: long -10.00 pips (entry 2025-07-27T22:05:00+00:00); short -10.00 pips (entry 2025-07-28T09:00:00+00:00); short -10.00 pips (entry 2025-07-29T05:20:00+00:00)
- Drawdown event: 2,055.20 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-07-28T06:15:00+00:00.
- Volatility analysis: average M5 range 4.99 pips, above the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-08-04 to 2025-08-10 (ISO 2025-W32)

- Completed trades: 37; net P&L: -100.00 pips; expectancy: -2.70 pips / -0.27 R.
- Required metrics: profit factor 0.64; win rate 24.32%; average trade -2.70 pips; average hold 136.62 min; trades/day 6.17; maximum trade-close drawdown this week 2,105.20 pips.
- Best session by net P&L: Asia-Pacific (00-06 UTC), 30.00 pips across 6 trades.
- Worst session by net P&L: New York (12-20 UTC), -60.00 pips across 18 trades.
- Largest winners: short 20.00 pips (entry 2025-08-04T01:15:00+00:00); short 20.00 pips (entry 2025-08-05T02:10:00+00:00); long 20.00 pips (entry 2025-08-05T15:45:00+00:00)
- Largest losers: short -10.00 pips (entry 2025-08-04T02:15:00+00:00); long -10.00 pips (entry 2025-08-04T03:20:00+00:00); short -10.00 pips (entry 2025-08-04T08:20:00+00:00)
- Drawdown event: 2,105.20 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-08-08T20:25:00+00:00.
- Volatility analysis: average M5 range 4.20 pips, above the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-08-11 to 2025-08-17 (ISO 2025-W33)

- Completed trades: 31; net P&L: -70.40 pips; expectancy: -2.27 pips / -0.23 R.
- Required metrics: profit factor 0.69; win rate 25.81%; average trade -2.27 pips; average hold 190.97 min; trades/day 5.17; maximum trade-close drawdown this week 2,185.60 pips.
- Best session by net P&L: Asia-Pacific (00-06 UTC), 30.00 pips across 3 trades.
- Worst session by net P&L: New York (12-20 UTC), -70.40 pips across 19 trades.
- Largest winners: short 20.00 pips (entry 2025-08-11T10:40:00+00:00); long 20.00 pips (entry 2025-08-12T16:25:00+00:00); long 20.00 pips (entry 2025-08-13T01:05:00+00:00)
- Largest losers: short -10.40 pips (entry 2025-08-12T19:20:00+00:00); short -10.00 pips (entry 2025-08-08T20:25:00+00:00); long -10.00 pips (entry 2025-08-11T02:50:00+00:00)
- Drawdown event: 2,185.60 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-08-14T18:10:00+00:00.
- Volatility analysis: average M5 range 3.53 pips, below the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-08-18 to 2025-08-24 (ISO 2025-W34)

- Completed trades: 41; net P&L: -80.00 pips; expectancy: -1.95 pips / -0.20 R.
- Required metrics: profit factor 0.73; win rate 26.83%; average trade -1.95 pips; average hold 152.93 min; trades/day 6.83; maximum trade-close drawdown this week 2,305.60 pips.
- Best session by net P&L: New York (12-20 UTC), -10.00 pips across 22 trades.
- Worst session by net P&L: Asia-Pacific (00-06 UTC), -30.00 pips across 9 trades.
- Largest winners: short 20.00 pips (entry 2025-08-18T07:30:00+00:00); short 20.00 pips (entry 2025-08-19T01:45:00+00:00); long 20.00 pips (entry 2025-08-19T04:30:00+00:00)
- Largest losers: long -10.00 pips (entry 2025-08-15T14:50:00+00:00); short -10.00 pips (entry 2025-08-18T02:35:00+00:00); long -10.00 pips (entry 2025-08-18T05:05:00+00:00)
- Drawdown event: 2,305.60 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-08-21T13:40:00+00:00.
- Volatility analysis: average M5 range 3.43 pips, below the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-08-25 to 2025-08-31 (ISO 2025-W35)

- Completed trades: 44; net P&L: -20.00 pips; expectancy: -0.45 pips / -0.05 R.
- Required metrics: profit factor 0.93; win rate 31.82%; average trade -0.45 pips; average hold 120.23 min; trades/day 7.33; maximum trade-close drawdown this week 2,285.60 pips.
- Best session by net P&L: New York (12-20 UTC), 60.00 pips across 21 trades.
- Worst session by net P&L: London (07-11 UTC), -50.00 pips across 14 trades.
- Largest winners: short 20.00 pips (entry 2025-08-22T19:50:00+00:00); short 20.00 pips (entry 2025-08-25T15:55:00+00:00); short 20.00 pips (entry 2025-08-25T16:50:00+00:00)
- Largest losers: short -10.00 pips (entry 2025-08-25T01:05:00+00:00); long -10.00 pips (entry 2025-08-25T07:10:00+00:00); short -10.00 pips (entry 2025-08-25T09:00:00+00:00)
- Drawdown event: 2,285.60 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-08-25T15:55:00+00:00.
- Volatility analysis: average M5 range 3.62 pips, below the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-09-01 to 2025-09-07 (ISO 2025-W36)

- Completed trades: 32; net P&L: -20.00 pips; expectancy: -0.62 pips / -0.06 R.
- Required metrics: profit factor 0.91; win rate 31.25%; average trade -0.62 pips; average hold 172.66 min; trades/day 5.33; maximum trade-close drawdown this week 2,345.60 pips.
- Best session by net P&L: Asia-Pacific (00-06 UTC), 20.00 pips across 4 trades.
- Worst session by net P&L: London (07-11 UTC), -40.00 pips across 13 trades.
- Largest winners: long 20.00 pips (entry 2025-09-01T03:20:00+00:00); short 20.00 pips (entry 2025-09-01T13:00:00+00:00); short 20.00 pips (entry 2025-09-02T08:15:00+00:00)
- Largest losers: short -10.00 pips (entry 2025-08-29T19:15:00+00:00); long -10.00 pips (entry 2025-09-01T07:35:00+00:00); long -10.00 pips (entry 2025-09-01T09:50:00+00:00)
- Drawdown event: 2,345.60 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-09-04T14:00:00+00:00.
- Volatility analysis: average M5 range 3.56 pips, below the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-09-08 to 2025-09-14 (ISO 2025-W37)

- Completed trades: 37; net P&L: -190.00 pips; expectancy: -5.14 pips / -0.51 R.
- Required metrics: profit factor 0.39; win rate 16.22%; average trade -5.14 pips; average hold 154.32 min; trades/day 6.17; maximum trade-close drawdown this week 2,485.60 pips.
- Best session by net P&L: Late (21-23 UTC), -20.00 pips across 2 trades.
- Worst session by net P&L: London (07-11 UTC), -60.00 pips across 9 trades.
- Largest winners: long 20.00 pips (entry 2025-09-08T13:45:00+00:00); long 20.00 pips (entry 2025-09-08T19:20:00+00:00); short 20.00 pips (entry 2025-09-09T11:40:00+00:00)
- Largest losers: short -10.00 pips (entry 2025-09-05T19:30:00+00:00); long -10.00 pips (entry 2025-09-08T08:40:00+00:00); short -10.00 pips (entry 2025-09-08T10:15:00+00:00)
- Drawdown event: 2,485.60 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-09-12T17:50:00+00:00.
- Volatility analysis: average M5 range 3.50 pips, below the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-09-15 to 2025-09-21 (ISO 2025-W38)

- Completed trades: 40; net P&L: 50.00 pips; expectancy: 1.25 pips / 0.12 R.
- Required metrics: profit factor 1.20; win rate 37.50%; average trade 1.25 pips; average hold 153.00 min; trades/day 6.67; maximum trade-close drawdown this week 2,525.60 pips.
- Best session by net P&L: London (07-11 UTC), 70.00 pips across 8 trades.
- Worst session by net P&L: Asia-Pacific (00-06 UTC), -30.00 pips across 12 trades.
- Largest winners: long 20.00 pips (entry 2025-09-15T08:10:00+00:00); long 20.00 pips (entry 2025-09-15T11:05:00+00:00); long 20.00 pips (entry 2025-09-16T03:20:00+00:00)
- Largest losers: long -10.00 pips (entry 2025-09-12T18:10:00+00:00); short -10.00 pips (entry 2025-09-15T01:10:00+00:00); long -10.00 pips (entry 2025-09-15T04:55:00+00:00)
- Drawdown event: 2,525.60 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-09-15T08:10:00+00:00.
- Volatility analysis: average M5 range 3.78 pips, at the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-09-22 to 2025-09-28 (ISO 2025-W39)

- Completed trades: 35; net P&L: -20.00 pips; expectancy: -0.57 pips / -0.06 R.
- Required metrics: profit factor 0.92; win rate 31.43%; average trade -0.57 pips; average hold 162.57 min; trades/day 5.83; maximum trade-close drawdown this week 2,475.60 pips.
- Best session by net P&L: New York (12-20 UTC), 30.00 pips across 15 trades.
- Worst session by net P&L: London (07-11 UTC), -20.00 pips across 11 trades.
- Largest winners: short 20.00 pips (entry 2025-09-19T16:20:00+00:00); long 20.00 pips (entry 2025-09-22T06:50:00+00:00); long 20.00 pips (entry 2025-09-22T09:10:00+00:00)
- Largest losers: short -10.00 pips (entry 2025-09-22T05:30:00+00:00); long -10.00 pips (entry 2025-09-22T11:10:00+00:00); short -10.00 pips (entry 2025-09-22T14:50:00+00:00)
- Drawdown event: 2,475.60 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-09-24T02:05:00+00:00.
- Volatility analysis: average M5 range 3.40 pips, below the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-09-29 to 2025-10-05 (ISO 2025-W40)

- Completed trades: 33; net P&L: -98.80 pips; expectancy: -2.99 pips / -0.30 R.
- Required metrics: profit factor 0.62; win rate 24.24%; average trade -2.99 pips; average hold 183.03 min; trades/day 5.50; maximum trade-close drawdown this week 2,575.60 pips.
- Best session by net P&L: Asia-Pacific (00-06 UTC), 10.00 pips across 5 trades.
- Worst session by net P&L: New York (12-20 UTC), -100.00 pips across 19 trades.
- Largest winners: long 20.00 pips (entry 2025-09-26T18:35:00+00:00); long 20.00 pips (entry 2025-09-30T06:55:00+00:00); short 20.00 pips (entry 2025-09-30T11:15:00+00:00)
- Largest losers: long -18.80 pips (entry 2025-10-03T21:05:00+00:00); long -10.00 pips (entry 2025-09-29T01:40:00+00:00); short -10.00 pips (entry 2025-09-29T12:15:00+00:00)
- Drawdown event: 2,575.60 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-10-02T14:40:00+00:00.
- Volatility analysis: average M5 range 3.56 pips, below the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-10-06 to 2025-10-12 (ISO 2025-W41)

- Completed trades: 42; net P&L: -90.10 pips; expectancy: -2.15 pips / -0.21 R.
- Required metrics: profit factor 0.71; win rate 26.19%; average trade -2.15 pips; average hold 146.90 min; trades/day 7.00; maximum trade-close drawdown this week 2,644.50 pips.
- Best session by net P&L: Asia-Pacific (00-06 UTC), 30.00 pips across 6 trades.
- Worst session by net P&L: New York (12-20 UTC), -50.10 pips across 23 trades.
- Largest winners: short 20.00 pips (entry 2025-10-06T06:15:00+00:00); long 20.00 pips (entry 2025-10-06T12:20:00+00:00); long 20.00 pips (entry 2025-10-06T14:45:00+00:00)
- Largest losers: short -10.10 pips (entry 2025-10-07T12:30:00+00:00); short -10.00 pips (entry 2025-10-05T22:10:00+00:00); long -10.00 pips (entry 2025-10-06T03:20:00+00:00)
- Drawdown event: 2,644.50 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-10-12T23:05:00+00:00.
- Volatility analysis: average M5 range 3.67 pips, below the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-10-13 to 2025-10-19 (ISO 2025-W42)

- Completed trades: 29; net P&L: 40.00 pips; expectancy: 1.38 pips / 0.14 R.
- Required metrics: profit factor 1.22; win rate 37.93%; average trade 1.38 pips; average hold 202.24 min; trades/day 4.83; maximum trade-close drawdown this week 2,664.50 pips.
- Best session by net P&L: New York (12-20 UTC), 30.00 pips across 12 trades.
- Worst session by net P&L: Asia-Pacific (00-06 UTC), -10.00 pips across 7 trades.
- Largest winners: short 20.00 pips (entry 2025-10-13T08:50:00+00:00); short 20.00 pips (entry 2025-10-13T12:40:00+00:00); long 20.00 pips (entry 2025-10-14T02:25:00+00:00)
- Largest losers: short -10.00 pips (entry 2025-10-12T23:05:00+00:00); long -10.00 pips (entry 2025-10-13T01:45:00+00:00); short -10.00 pips (entry 2025-10-14T01:05:00+00:00)
- Drawdown event: 2,664.50 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-10-13T08:50:00+00:00.
- Volatility analysis: average M5 range 3.62 pips, below the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-10-20 to 2025-10-26 (ISO 2025-W43)

- Completed trades: 26; net P&L: -110.00 pips; expectancy: -4.23 pips / -0.42 R.
- Required metrics: profit factor 0.48; win rate 19.23%; average trade -4.23 pips; average hold 224.23 min; trades/day 5.20; maximum trade-close drawdown this week 2,714.50 pips.
- Best session by net P&L: London (07-11 UTC), 10.00 pips across 8 trades.
- Worst session by net P&L: New York (12-20 UTC), -80.00 pips across 11 trades.
- Largest winners: short 20.00 pips (entry 2025-10-20T11:05:00+00:00); short 20.00 pips (entry 2025-10-21T03:40:00+00:00); short 20.00 pips (entry 2025-10-22T08:10:00+00:00)
- Largest losers: short -10.00 pips (entry 2025-10-17T21:40:00+00:00); long -10.00 pips (entry 2025-10-20T02:00:00+00:00); long -10.00 pips (entry 2025-10-20T03:15:00+00:00)
- Drawdown event: 2,714.50 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-10-24T08:55:00+00:00.
- Volatility analysis: average M5 range 2.88 pips, below the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-10-27 to 2025-11-02 (ISO 2025-W44)

- Completed trades: 34; net P&L: -100.00 pips; expectancy: -2.94 pips / -0.29 R.
- Required metrics: profit factor 0.62; win rate 23.53%; average trade -2.94 pips; average hold 175.88 min; trades/day 5.67; maximum trade-close drawdown this week 2,814.50 pips.
- Best session by net P&L: London (07-11 UTC), 10.00 pips across 8 trades.
- Worst session by net P&L: New York (12-20 UTC), -110.00 pips across 17 trades.
- Largest winners: long 20.00 pips (entry 2025-10-27T08:45:00+00:00); short 20.00 pips (entry 2025-10-29T01:45:00+00:00); short 20.00 pips (entry 2025-10-29T18:05:00+00:00)
- Largest losers: long -10.00 pips (entry 2025-10-24T20:45:00+00:00); short -10.00 pips (entry 2025-10-27T08:00:00+00:00); long -10.00 pips (entry 2025-10-27T23:30:00+00:00)
- Drawdown event: 2,814.50 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-10-30T00:20:00+00:00.
- Volatility analysis: average M5 range 3.22 pips, below the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-11-03 to 2025-11-09 (ISO 2025-W45)

- Completed trades: 31; net P&L: -10.00 pips; expectancy: -0.32 pips / -0.03 R.
- Required metrics: profit factor 0.95; win rate 32.26%; average trade -0.32 pips; average hold 200.00 min; trades/day 5.17; maximum trade-close drawdown this week 2,914.50 pips.
- Best session by net P&L: London (07-11 UTC), 10.00 pips across 8 trades.
- Worst session by net P&L: Late (21-23 UTC), -10.00 pips across 1 trades.
- Largest winners: short 20.00 pips (entry 2025-11-03T18:25:00+00:00); long 20.00 pips (entry 2025-11-04T03:05:00+00:00); short 20.00 pips (entry 2025-11-04T08:40:00+00:00)
- Largest losers: long -10.00 pips (entry 2025-10-31T20:25:00+00:00); short -10.00 pips (entry 2025-11-03T01:05:00+00:00); long -10.00 pips (entry 2025-11-03T02:10:00+00:00)
- Drawdown event: 2,914.50 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-11-05T14:40:00+00:00.
- Volatility analysis: average M5 range 2.73 pips, below the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-11-10 to 2025-11-16 (ISO 2025-W46)

- Completed trades: 32; net P&L: -140.00 pips; expectancy: -4.38 pips / -0.44 R.
- Required metrics: profit factor 0.46; win rate 18.75%; average trade -4.38 pips; average hold 188.44 min; trades/day 5.33; maximum trade-close drawdown this week 2,994.50 pips.
- Best session by net P&L: London (07-11 UTC), 10.00 pips across 8 trades.
- Worst session by net P&L: Asia-Pacific (00-06 UTC), -90.00 pips across 12 trades.
- Largest winners: long 20.00 pips (entry 2025-11-11T10:20:00+00:00); long 20.00 pips (entry 2025-11-13T07:25:00+00:00); long 20.00 pips (entry 2025-11-13T08:05:00+00:00)
- Largest losers: short -10.00 pips (entry 2025-11-09T23:10:00+00:00); short -10.00 pips (entry 2025-11-10T03:20:00+00:00); long -10.00 pips (entry 2025-11-10T05:30:00+00:00)
- Drawdown event: 2,994.50 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-11-13T07:25:00+00:00.
- Volatility analysis: average M5 range 2.89 pips, below the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-11-17 to 2025-11-23 (ISO 2025-W47)

- Completed trades: 29; net P&L: -50.00 pips; expectancy: -1.72 pips / -0.17 R.
- Required metrics: profit factor 0.76; win rate 27.59%; average trade -1.72 pips; average hold 229.83 min; trades/day 4.83; maximum trade-close drawdown this week 3,014.50 pips.
- Best session by net P&L: Asia-Pacific (00-06 UTC), 20.00 pips across 4 trades.
- Worst session by net P&L: London (07-11 UTC), -30.00 pips across 6 trades.
- Largest winners: short 20.00 pips (entry 2025-11-14T14:50:00+00:00); short 20.00 pips (entry 2025-11-17T00:20:00+00:00); short 20.00 pips (entry 2025-11-18T15:55:00+00:00)
- Largest losers: long -10.00 pips (entry 2025-11-17T16:00:00+00:00); short -10.00 pips (entry 2025-11-17T18:15:00+00:00); long -10.00 pips (entry 2025-11-18T04:25:00+00:00)
- Drawdown event: 3,014.50 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-11-21T19:40:00+00:00.
- Volatility analysis: average M5 range 3.01 pips, below the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-11-24 to 2025-11-30 (ISO 2025-W48)

- Completed trades: 24; net P&L: -60.00 pips; expectancy: -2.50 pips / -0.25 R.
- Required metrics: profit factor 0.67; win rate 25.00%; average trade -2.50 pips; average hold 250.83 min; trades/day 4.00; maximum trade-close drawdown this week 3,094.50 pips.
- Best session by net P&L: Asia-Pacific (00-06 UTC), 10.00 pips across 5 trades.
- Worst session by net P&L: London (07-11 UTC), -40.00 pips across 7 trades.
- Largest winners: long 20.00 pips (entry 2025-11-24T02:15:00+00:00); long 20.00 pips (entry 2025-11-25T12:45:00+00:00); short 20.00 pips (entry 2025-11-26T07:55:00+00:00)
- Largest losers: long -10.00 pips (entry 2025-11-21T19:40:00+00:00); short -10.00 pips (entry 2025-11-24T00:15:00+00:00); long -10.00 pips (entry 2025-11-24T10:10:00+00:00)
- Drawdown event: 3,094.50 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-11-26T07:55:00+00:00.
- Volatility analysis: average M5 range 3.12 pips, below the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-12-01 to 2025-12-07 (ISO 2025-W49)

- Completed trades: 25; net P&L: -70.00 pips; expectancy: -2.80 pips / -0.28 R.
- Required metrics: profit factor 0.63; win rate 24.00%; average trade -2.80 pips; average hold 258.80 min; trades/day 4.17; maximum trade-close drawdown this week 3,144.50 pips.
- Best session by net P&L: London (07-11 UTC), 10.00 pips across 8 trades.
- Worst session by net P&L: New York (12-20 UTC), -50.00 pips across 11 trades.
- Largest winners: long 20.00 pips (entry 2025-12-01T07:25:00+00:00); short 20.00 pips (entry 2025-12-01T17:55:00+00:00); long 20.00 pips (entry 2025-12-02T18:10:00+00:00)
- Largest losers: short -10.00 pips (entry 2025-11-28T21:35:00+00:00); long -10.00 pips (entry 2025-12-01T01:10:00+00:00); short -10.00 pips (entry 2025-12-01T02:20:00+00:00)
- Drawdown event: 3,144.50 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-12-07T22:55:00+00:00.
- Volatility analysis: average M5 range 2.71 pips, below the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-12-08 to 2025-12-14 (ISO 2025-W50)

- Completed trades: 25; net P&L: 19.20 pips; expectancy: 0.77 pips / 0.08 R.
- Required metrics: profit factor 1.12; win rate 36.00%; average trade 0.77 pips; average hold 250.60 min; trades/day 4.17; maximum trade-close drawdown this week 3,154.50 pips.
- Best session by net P&L: Asia-Pacific (00-06 UTC), 20.00 pips across 4 trades.
- Worst session by net P&L: London (07-11 UTC), -10.00 pips across 7 trades.
- Largest winners: long 20.00 pips (entry 2025-12-08T00:30:00+00:00); short 20.00 pips (entry 2025-12-08T07:50:00+00:00); short 20.00 pips (entry 2025-12-09T12:10:00+00:00)
- Largest losers: long -10.80 pips (entry 2025-12-12T17:40:00+00:00); long -10.00 pips (entry 2025-12-08T06:05:00+00:00); short -10.00 pips (entry 2025-12-08T15:05:00+00:00)
- Drawdown event: 3,154.50 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-12-09T12:10:00+00:00.
- Volatility analysis: average M5 range 2.88 pips, below the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-12-15 to 2025-12-21 (ISO 2025-W51)

- Completed trades: 32; net P&L: -110.00 pips; expectancy: -3.44 pips / -0.34 R.
- Required metrics: profit factor 0.56; win rate 21.88%; average trade -3.44 pips; average hold 179.38 min; trades/day 5.33; maximum trade-close drawdown this week 3,235.30 pips.
- Best session by net P&L: London (07-11 UTC), 0.00 pips across 6 trades.
- Worst session by net P&L: New York (12-20 UTC), -50.00 pips across 17 trades.
- Largest winners: long 20.00 pips (entry 2025-12-15T10:10:00+00:00); long 20.00 pips (entry 2025-12-16T12:00:00+00:00); short 20.00 pips (entry 2025-12-16T18:00:00+00:00)
- Largest losers: short -10.00 pips (entry 2025-12-14T22:10:00+00:00); long -10.00 pips (entry 2025-12-15T02:50:00+00:00); short -10.00 pips (entry 2025-12-15T03:50:00+00:00)
- Drawdown event: 3,235.30 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-12-19T19:05:00+00:00.
- Volatility analysis: average M5 range 3.07 pips, below the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-12-22 to 2025-12-28 (ISO 2025-W52)

- Completed trades: 16; net P&L: -10.00 pips; expectancy: -0.62 pips / -0.06 R.
- Required metrics: profit factor 0.91; win rate 31.25%; average trade -0.62 pips; average hold 335.00 min; trades/day 2.67; maximum trade-close drawdown this week 3,245.30 pips.
- Best session by net P&L: London (07-11 UTC), 30.00 pips across 3 trades.
- Worst session by net P&L: New York (12-20 UTC), -20.00 pips across 8 trades.
- Largest winners: long 20.00 pips (entry 2025-12-22T07:50:00+00:00); long 20.00 pips (entry 2025-12-22T13:10:00+00:00); long 20.00 pips (entry 2025-12-23T00:10:00+00:00)
- Largest losers: short -10.00 pips (entry 2025-12-19T20:50:00+00:00); long -10.00 pips (entry 2025-12-22T15:50:00+00:00); short -10.00 pips (entry 2025-12-22T16:25:00+00:00)
- Drawdown event: 3,245.30 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-12-22T07:50:00+00:00.
- Volatility analysis: average M5 range 2.70 pips, below the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.

### 2025-12-29 to 2026-01-04 (ISO 2026-W01)

- Completed trades: 17; net P&L: -36.10 pips; expectancy: -2.12 pips / -0.21 R.
- Required metrics: profit factor 0.70; win rate 29.41%; average trade -2.12 pips; average hold 221.18 min; trades/day 5.67; maximum trade-close drawdown this week 3,285.30 pips.
- Best session by net P&L: Asia-Pacific (00-06 UTC), 10.00 pips across 5 trades.
- Worst session by net P&L: New York (12-20 UTC), -36.10 pips across 8 trades.
- Largest winners: short 20.00 pips (entry 2025-12-29T03:05:00+00:00); long 20.00 pips (entry 2025-12-29T06:55:00+00:00); short 20.00 pips (entry 2025-12-30T11:55:00+00:00)
- Largest losers: short -10.00 pips (entry 2025-12-26T15:55:00+00:00); long -10.00 pips (entry 2025-12-29T01:25:00+00:00); long -10.00 pips (entry 2025-12-29T08:55:00+00:00)
- Drawdown event: 3,285.30 pips from running peak 2025-01-06T11:35:00+00:00 to trough 2025-12-31T16:40:00+00:00.
- Volatility analysis: average M5 range 2.88 pips, below the weekly median of 3.78 pips across data weeks.
- Spread analysis: modeled at a flat 1.0 pip per V1; no actual bid/ask spread observations are available.
- Lesson: descriptive historical results only. Keep V1 frozen and use demo records to confirm whether this observation persists; no next-version hypothesis is proposed.
