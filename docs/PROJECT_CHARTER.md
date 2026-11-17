# Forex Scalping Bot Project Charter

## Mission

Build a profitable and robust breakout scalping bot through continuous
improvement driven by real trading results. This project exists to create,
test, improve, validate, and deploy a tradable breakout scalping system; it is
not an academic research project.

## Rule 0: The Market Is the Teacher

Improvements must be justified by historical tests, validation tests, or demo
trading metrics:

**Trade → Measure → Learn → Improve → Validate → Repeat**

## Rule 1: One Strategy Family Only

The only strategy family is **Breakout Scalping**, evolved from Breakout
Scalping V1. Filters and trade-management changes may support this family.
Strategy pivots are prohibited unless used strictly as breakout-supporting
filters.

## Rule 2: Engineering Over Research

Every task must answer: “Will this improve the breakout scalping bot?” If not,
do not do it. Avoid academic exploration, unrelated strategy discovery,
indicator hunting, and theory-only investigations.

## Rule 3: Version Evolution

Maintain a version history. Each future version must introduce exactly one
hypothesis; never combine multiple changes in a version. V1 parameters remain
frozen. V2 is prohibited until V1 has baseline metrics and at least **100
completed demo trades**; there are no exceptions.

## Rule 4: Metrics Drive Decisions

Every review must report net profit, profit factor, expectancy, win rate,
maximum drawdown, average trade, average hold time, trades per day, and trade
count. Opinions do not override metrics.

## Rule 5: Promotion Requirements

A version becomes the baseline only when expectancy and profit factor improve,
drawdown remains acceptable, validation passes, and demo performance is
acceptable. Otherwise reject it and keep the previous baseline.

## Rule 6: Demo Before Trust

Required workflow: **Backtest → Validation → Demo Trading → Performance Review
→ Promotion or Rejection**. Forward demo results take precedence over
historical simulations. Count only completed demo trades toward the 100-trade
gate; historical trades do not count.

## Rule 7: No Curve Fitting

Prohibit massive parameter sweeps, optimization loops, brute-force searches,
and endless threshold tuning. Every modification must have one clearly defined
hypothesis.

## Rule 8: Every Loss Teaches

Document why each rejected version failed, what market condition exposed its
weakness, and what improvement will be tested next. No random modifications.

## Success Definition

Success is continuously improving the current breakout scalping bot through
**Trade → Measure → Learn → Improve → Validate → Repeat**, not finding a
perfect strategy.
