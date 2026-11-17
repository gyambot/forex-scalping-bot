# Breakout Scalping V1 — Frozen Specification

**Status:** Frozen baseline; historical baseline and temporal validation completed; demo evidence pending  
**Strategy family:** Breakout scalping  
**Instrument:** EURUSD  
**Signal timeframe:** M5  
**Parameters:** Fixed below; no optimization or command-line overrides

## Hypothesis

A close beyond the prior 20 completed M5 bars' high or low captures a
short-term EURUSD breakout often enough for a fixed 2R target to overcome a
fixed 1R stop and modeled spread. This is a hypothesis, not a performance
claim; only backtest, validation, and demo results can support it.

## Frozen rules

| Setting | V1 value |
|---|---|
| Lookback | 20 completed bars |
| Entry signal | Current bar close strictly above prior 20-bar high (long), or strictly below prior 20-bar low (short) |
| Entry execution | Next M5 bar open |
| Stop loss | 10 pips from actual entry price (1R) |
| Take profit | 20 pips from actual entry price (2R) |
| Modeled spread | 1.0 pip, fixed |
| Concurrent positions | One |
| Position size | One normalized unit; results reported in pips and R, not account currency |
| Pip size | 0.0001 |

The 20-bar channel excludes the signal bar. There are no additional filters,
time windows, indicators, or discretionary overrides. Signals while a position
is open are ignored. If a position exits during a bar, a signal at that bar's
close may schedule an entry for the following bar.

## Data and execution assumptions

- Input is chronological EURUSD M5 **bid** OHLC data with explicit-offset
  timestamps. MT5 demo observations use the configured broker-time offset;
  archived historical data may retain its original source offset.
- Entry is at the next bar's bid open plus the fixed spread for a long, and at
  the bid open for a short. Long exits use bid; short exits use ask (bid plus
  the fixed spread).
- The runner does not model commission, slippage, latency, financing, rejected
  orders, or variable spreads. These limitations must be considered when
  interpreting results.
- Stops and targets are checked against each bar's OHLC. If both are touched
  in the same bar, the stop is assumed to fill first. A gap through a stop is
  filled at the bar open, which is worse than the stop price; a favorable gap
  through a target is conservatively filled at the target.
- OHLC data cannot establish the exact intrabar fill time or event ordering.
  Hold time is estimated in whole five-minute bars. This is not tick-level
  execution simulation.
- Any open position is closed at the final available bar close and marked
  `end_of_data`; this forced close must be considered when interpreting a run.

## Input format

CSV header:

```csv
timestamp,open,high,low,close
2025-01-06T08:00:00Z,1.03000,1.03020,1.02990,1.03010
```

Prices are bid prices. Timestamps must be ISO-8601 with an explicit source
offset and on five-minute boundaries. Bars must be strictly chronological,
unique, finite, positive, and have internally consistent OHLC values. The
runner rejects malformed input.

## Outputs

For each run, the runner writes `trades.csv` and `metrics.json`. Metrics include
net profit, profit factor, expectancy, win rate, maximum drawdown, average
trade, average hold time, trades per day, and trade count. Net profit, average
trade, and expectancy are reported in pips; expectancy in R is also provided.
Metrics describe the supplied data and assumptions only; they do not establish
future profitability.

## Frozen baseline change control

Do not change parameters during a run or optimize them. A proposed change must
be a separately versioned, single-hypothesis experiment, supported by evidence
and reviewed against V1. Do not design V2 until V1 has been tested.
