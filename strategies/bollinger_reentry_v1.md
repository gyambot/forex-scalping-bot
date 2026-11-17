# Candidate 7: Bollinger re-entry mean reversion

Research only, not a change to the baseline. Hypothesis: an extreme close
followed by re-entry inside the Bollinger bands may indicate short-term
reversal, unlike the trend or range breakouts previously tested.

Use the last 20 observed M5 closes including the current close. Bands are
the arithmetic mean plus/minus two population standard deviations. If the
preceding completed close is strictly below its own lower band and the
current close is inside or on its own bands, signal long; reverse for a
preceding close above the upper band. Each bar uses its own causal bands.
No signal before 21 bars. No session filter. Windows can span data gaps.
The signal enters at the next available open; single position, 10-pip stop,
20-pip target, fixed one-pip spread and existing stop-first/gap conventions.
No parameter optimization.

The public [Bollinger Bands explanation](https://www.investopedia.com/terms/b/bollingerbands.asp)
describes 20-period/two-standard-deviation bands and band-bounce mean
reversion; the M5 re-entry, risk and fill rules above are our fixed
interpretation, not a claim that the source validated them on EURUSD.
