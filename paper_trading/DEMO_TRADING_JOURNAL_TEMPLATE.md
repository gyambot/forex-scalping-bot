# Breakout Scalping V1 — Demo Trading Journal

Use one row per signal, including skipped or rejected orders. Record broker
timestamps and execution details; do not alter the frozen strategy while
collecting V1 results.

## Mandatory V2 gate

- V1 baseline metrics: **Recorded**
- Latest temporal validation: **Negative; review before demo activity**
- Completed demo trades: **0 / 100**
- V2 status: **Blocked**
- Historical backtest/validation trades do not count.
- Count a trade only after the position is closed and its actual execution,
  costs, result, and completion status are recorded in
  [`DEMO_TRADING_LOG.csv`](./DEMO_TRADING_LOG.csv).
- V2 is prohibited until baseline metrics exist and the log contains at least
  100 completed demo trades. There are no exceptions.

Demo activity is for evidence collection only; these results do not authorize
live trading or override the negative historical results.

Use the CSV log as the machine-readable source for counts and weekly reports.
The Markdown table below is a human review aid; skipped signals, rejected
orders, open positions, and historical trades do not count toward the gate.

| Field | Entry |
|---|---|
| Date and broker time (explicit offset) | |
| Broker / demo account identifier (no credentials) | |
| Instrument / timeframe | EURUSD / M5 |
| Signal direction and signal-bar close | |
| Prior 20-bar high / low | |
| Intended entry / actual fill | |
| Spread at signal and fill | |
| Stop / target | 10 pips / 20 pips |
| Position size | |
| Exit time / actual exit / reason | |
| Gross and net P&L (pips) | |
| P&L (R) | |
| Slippage, commission, or other costs | |
| Order rejection / platform issue | |
| Rule followed without discretion? | |
| Notes / evidence reference | |

## Daily review

- Date and demo days observed:
- Signals / trades / skipped signals:
- Net profit:
- Profit factor:
- Expectancy:
- Win rate:
- Maximum drawdown:
- Average trade:
- Average hold time:
- Trades per day:
- Trade count:
- Operational issues:
- Any rule deviations:
- Reviewer and next review date:

## Promotion review

Do not promote based on a short or selectively chosen sample. Review the
complete backtest, untouched validation period, and demo record together against
pre-declared risk and performance criteria. Record **Promote / Reject / Continue
Demo**, evidence, and reviewer approval.
