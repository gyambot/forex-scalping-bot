# Forex Scalping Bot

The project has one frozen strategy: **Breakout Scalping V1**. Its 2025
historical baseline and 2026 temporal validation are both negative under the
documented data and execution assumptions; no profitability is claimed. Do not
design V2 until the baseline metrics exist and at least 100 completed demo
trades have been collected.
See the [project charter](docs/PROJECT_CHARTER.md), [roadmap](docs/ROADMAP.md),
and [V1 specification](strategies/breakout_scalping_v1.md).

## Project layout

- `strategies/` — versioned, frozen strategy specifications
- `scripts/` — backtest runner, trade logger, and metrics generator
- `tests/` — automated checks for the backtest framework
- `data/` — acquired market data, converted input files, and provenance
- `backtests/` — generated historical run outputs
- `validation/` — validation reports and workflow
- `paper_trading/` — demo-trading journal and workflow
- `metrics/` — reviewed metric snapshots
- `reports/` — performance and promotion/rejection reports
- `docs/` — project charter and roadmap

## Run a V1 backtest

Requires Python 3.10 or newer; the runner uses only the Python standard
library.

1. Prepare chronological EURUSD M5 bid OHLC data as
   `data/eurusd_m5.csv`. Use the exact header and explicit-offset timestamps
   described in the [V1 specification](strategies/breakout_scalping_v1.md).
   Archived HistData may retain its source-derived UTC offset; MT5 demo data
   uses the configured broker-time offset. For the archived HistData M1 source
   format, see [data provenance](data/README.md) and `scripts/prepare_histdata.py`.
2. Run:

   ```powershell
   python scripts/backtest.py --input data/eurusd_m5.csv --output-dir backtests/run_001
   ```

3. Review `backtests/run_001/trades.csv` and `metrics.json`; record data
   provenance and limitations in a
   [validation report](validation/VALIDATION_REPORT_TEMPLATE.md).

## Generate weekly review

The report generator accepts the V1 trade CSV or the structured demo log (only
rows marked `completed=true` count) plus its corresponding M5 bid OHLC file:

```powershell
python -m scripts.generate_weekly_review --bars data/eurusd_m5_2025.csv --trades backtests/2025_histdata_v1/trades.csv --output reports/weekly/WEEKLY_REVIEW.md
```

For ongoing demo reviews, use demo-period M5 bars and
`paper_trading/DEMO_TRADING_LOG.csv`. The checked-in weekly report is a
historical 2025 breakdown, not a demo-performance report.

## Record and review demo trades

The original incomplete CSV header is preserved in
`paper_trading/DEMO_TRADING_LOG_SEED.csv`; the operational
`paper_trading/DEMO_TRADING_LOG.csv` uses the full schema in the
[trade-capture specification](paper_trading/TRADE_CAPTURE_SPECIFICATION.md).
Record only a fully closed, reconciled demo position. Supply a JSON object with
all schema fields to the recorder:

```powershell
python -m paper_trading.trade_recorder --trade-json paper_trading/trade.json
python -m paper_trading.generate_demo_metrics
python -m paper_trading.check_gate
python -m paper_trading.generate_demo_review
```

Metrics and the gate count include only rule-compliant completed V1 demo
positions. Reaching 100 makes the project ready for a V2 review only; it does
not approve or define V2. All generated summaries remain descriptive and
cannot substitute for broker-history reconciliation.

For manual broker-to-project capture, copy
`paper_trading/trade_import_template.csv`, fill one row only after a position
is fully closed and reconciled, then run:

```powershell
python -m paper_trading.manual_trade_capture --trade-csv paper_trading\trade_import.csv
python -m paper_trading.generate_demo_metrics
python -m paper_trading.check_gate
```

See the [manual workflow](paper_trading/demo_trade_workflow.md) and
[reconciliation guide](paper_trading/TRADE_RECONCILIATION.md). The importer
only validates and appends records; it does not connect to MT5 or execute
orders.

## Check MT5 demo connectivity

The read-only MT5 connector targets the IC Markets demo server
`ICMarketsSC-Demo`. Copy `paper_trading/.env.template` to
`paper_trading/.env`, edit it locally to set the demo login and password, and
keep it out of source control. Never put credentials in scripts, reports, or
command arguments. Install the official `MetaTrader5` Python package if it is
not already available, install/open the broker's MT5 desktop terminal, and
sign in to the demo account. Prefer leaving `MT5_PASSWORD` unset so the
connector attaches to the already authenticated terminal session; it verifies
the configured login and server after attaching. A password in `.env` is an
optional fallback for a fresh terminal login. Set
`MT5_BROKER_UTC_OFFSET=+02:00` (or `+03:00` when the IC Markets server clock
changes) in `.env`; do not store credentials in this setting.

```powershell
python -m paper_trading.mt5_healthcheck
```

The command writes `paper_trading/MT5_HEALTHCHECK.json` and exits nonzero when
the terminal/account checks fail. The price-feed API
(`paper_trading.mt5_price_feed`) returns the current EURUSD bid/ask/spread and
the latest completed M5 bars, including the latest 100. A quote is treated as
fresh for connectivity checks only when its MT5 timestamp is within 120
seconds of the configured broker clock. Bar clock fields are preserved and
tagged with the configured explicit offset; the project does not convert them
to UTC. A timestamp outside that tolerance is reported as a warning and does
not make an otherwise valid quote unavailable. This is not a strategy spread
filter. These modules only connect,
inspect account/terminal permissions, select the EURUSD symbol for Market
Watch, and read prices/bars; they contain no trading or order-management
operations. Healthcheck success does not authorize demo orders.

## Monitor read-only V1 signals

After confirming the terminal is connected to the expected demo account, run:

```powershell
python -m paper_trading.live_signal_monitor --interval 5
```

The monitor evaluates each newly completed M5 bar and appends LONG, SHORT, or
NO SIGNAL to `paper_trading/LIVE_SIGNAL_LOG.csv`. These are raw breakout
candidates; the monitor does not simulate or manage positions, place trades,
or assert trade eligibility while a position is open. See
[signal validation](paper_trading/SIGNAL_VALIDATION.md) for historical parity
results and this limitation.

For signal-only observation records, run:

```powershell
python -m paper_trading.signal_observer --interval 5
```

The observer writes one row per newly completed M5 bar to
`paper_trading/SIGNAL_OBSERVATION_LOG.csv` and refreshes
`paper_trading/SIGNAL_OBSERVATION_REPORT.md` when stopped with Ctrl+C. Use
`--max-polls N` for a bounded observation session. The report is descriptive
only, flags broker-clock skew, and does not analyze trade performance. Signal
observations do not count toward the 100 completed demo-trade requirement.

Parameters are frozen in the runner and cannot be changed through command-line
options. The OHLC simulation uses conservative assumptions documented in the
strategy specification; it is not tick-level execution modeling.

The first full-year historical baseline, its limitations, and the decision not
to change V1 are recorded in
[the 2025 baseline report](reports/BASELINE_BACKTEST_2025.md). Historical
trades do not count toward the mandatory 100 completed demo trades required
before V2 may even be proposed. Use
[the demo journal](paper_trading/DEMO_TRADING_JOURNAL_TEMPLATE.md) and
[weekly review](reports/weekly/WEEKLY_REVIEW.md) to continue evidence collection.

## Run tests

```powershell
python -m unittest discover -s tests -v
```

Backtest results alone are not sufficient for promotion. Follow the backtest,
validation, and demo gates in the roadmap and charter.
