# Candidate 9: Weekend gap fade

Hypothesis: some opening gaps revert after the market reopens. Compare the
first observed bar after a gap of at least 36 elapsed hours, from a Friday
UTC bar to a Sunday or Monday UTC bar, with the previous Friday close.
If the opening bid differs by at least five pips, signal against the gap at
the first post-gap bar's close. No signal if no qualifying gap. This checks
calendar days explicitly, rather than treating ordinary missing data as a
weekend. A long closure due to missing data can nevertheless distort the
reference price.

Enter at the next available open, not at the already-observed reopening
price. Use one position, 10-pip stop, 20-pip target, fixed one-pip spread,
existing stop-first and gap conventions. The modeled spread is particularly
unreliable near a weekend open. Rare signals imply small-sample uncertainty.

[Gap trading](https://www.investopedia.com/articles/trading/05/playinggaps.asp)
describes gaps and fading toward pre-gap prices. It does not validate this
five-pip, weekend EURUSD adaptation or its fixed exits. No optimization.
