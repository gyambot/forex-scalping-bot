# Candidate 8: Daily-return time-series momentum

Hypothesis: direction of the previous 24 elapsed hours may persist after the
London open. This is not a moving-average pullback or price-level breakout.
At 07:55 London bar open (nominal close 08:00), compare its close with the
close of the bar whose UTC opening instant is exactly 24 hours earlier.
Greater means long, less means short, equal or missing means no signal.
This intentionally skips days without an exact prior observation and uses
Europe/London daylight saving. Enter next available open; single position,
10-pip stop, 20-pip target, one-pip spread and existing historical gap and
stop-first rules. No other filter or parameter sweep.

[Time Series Momentum](https://www.aqr.com/Insights/Research/Journal-Article/Time-Series-Momentum)
documents past-return momentum across futures and currencies at roughly
12-month horizons. It does not validate this much shorter 24-hour/M5
adaptation. These fixed intraday rules and exits are research assumptions.
