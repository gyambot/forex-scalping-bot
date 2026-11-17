# Live Signal Engine Validation

## Frozen rule implemented

For each completed EURUSD M5 bar after at least 20 prior completed bars, the
engine compares the current bar's close with the high and low of exactly the
preceding 20 bars (the current bar is excluded):

- `LONG` when close is strictly greater than the prior-channel high.
- `SHORT` when close is strictly less than the prior-channel low.
- `NO SIGNAL` otherwise, including when fewer than 20 prior bars are present.

The same `breakout_signal_at` function is called by the backtest and the live
engine. V1 enters on the next bar's open. Stop and target prices are not
reported as actual levels by the signal engine because their frozen distances
are anchored to that future entry price. The signal log leaves these fields
blank and records the signal bar close as `current_price`.

The signal timestamp uses the MT5 bar's opening timestamp, matching the
backtest's `signal_time` convention. The signal is only evaluated after MT5
returns the bar as completed. MT5 wall-clock fields are retained directly
with the configured broker offset; the engine does not convert them to UTC.

## Historical parity procedure and result

Run the test suite with:

```powershell
python -m unittest paper_trading.tests.test_live_signal_engine -v
```

The historical parity test loads `data/eurusd_m5_2025.csv`, iterates every
completed bar through the live engine's raw breakout evaluator, and compares
timestamps, directions, and channel levels against an independent strict
20-bar calculation over the same source bars.

For the checked-in 2025 dataset (73,683 M5 bars), the raw V1 rule produced
8,733 candidates. The V1 backtest produced 2,260 trades. This is an expected
and important discrepancy: raw candidate signals while a simulated position
is open are ignored by the backtest's one-position rule. The signal engine
does not simulate positions or access broker positions, so it reports raw
breakout candidates and does **not** claim all candidates are eligible V1
trade entries. The historical test proves rule parity for breakout detection,
not trade-count, fill, or position-state parity.

## Live read-only operation

With the IC Markets demo terminal already authenticated and local
`paper_trading/.env` configured, run:

```powershell
python -m paper_trading.live_signal_monitor --interval 5
```

The monitor reads the latest 21 completed bars, evaluates the newest one, and
appends one state per newly observed bar to `LIVE_SIGNAL_LOG.csv`. It does not
submit, modify, or close orders and does not manage positions. Restarting it
does not duplicate the latest timestamp already present in the log. A feed,
validation, or file error stops the monitor visibly; it is not silently
ignored. Stop the loop with Ctrl+C.

This log is signal evidence only. It is not a trade log, does not count toward
the 100-demo-trade gate, and does not authorize or automate execution.
