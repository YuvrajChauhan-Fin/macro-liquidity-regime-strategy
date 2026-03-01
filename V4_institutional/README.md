# V4 Institutional Liquidity Regime Strategy

## Overview

This project implements a macro-driven multi-asset allocation framework using:

- Global Liquidity Regime Classification (US M2, ECB Assets)
- Regime Strength Scaling (-1 to +2)
- Cross-Asset Momentum (NIFTY vs SPY)
- Gold as Defensive Allocation
- Inverse Volatility Risk Budgeting
- Volatility Targeting Overlay (10% annualized)
- Walk-Forward Out-of-Sample Validation

---

## Strategy Logic

1. Estimate liquidity regime using rolling growth of global monetary aggregates.
2. Classify regime into strength buckets.
3. Allocate across equities and gold based on regime strength.
4. Rank equities via 12-month momentum.
5. Apply inverse volatility risk budgeting.
6. Apply portfolio-level volatility targeting.
7. Validate using 10-year expanding walk-forward framework.

---

## Out-of-Sample Results (2017–2026)

- Sharpe Ratio: ~1.4
- CAGR: ~16–17%
- Volatility: ~12%
- Max Drawdown: ~ -13%
- Months Tested: 101

---

## Research Validation

- Regime bucket analysis performed
- Volatility targeting diagnostic performed
- Allocation sensitivity tested
- Robust to parameter perturbations

---

## Disclaimer

This is a research project for educational and portfolio demonstration purposes.