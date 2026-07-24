# Milestone 06 — Robustness, Tolerances, and Error Budget Analysis

**Status**: COMPLETED  
**Date Completed**: 2026-07-24  

---

## 1. Executive Summary & Objective

The objective of Milestone 06 is to implement a Monte Carlo error budget analysis module (`src/nkm/errors.py`) to quantify the statistical impact of real-world machine imperfections (quadrupole gradient errors, misalignments, roll tilts, energy deviations, and kicker strength jitter) on exit optics mismatch, aperture margins, and beam transmission.

---

## 2. Technical Implementation & Error Definitions

### 2.1 Error Budget Configuration (`ErrorBudgetConfig`)
- Quadrupole relative gradient error: $\sigma_{\Delta K / K} = 0.1\%$ ($1 \times 10^{-3}$)
- Quadrupole horizontal/vertical misalignment: $\sigma_{dx} = \sigma_{dy} = 100\text{ }\mu\text{m}$ ($1 \times 10^{-4}\text{ m}$)
- Quadrupole roll tilt error: $\sigma_{\text{roll}} = 0.5\text{ mrad}$ ($5 \times 10^{-4}\text{ rad}$)
- Beam energy offset: $\sigma_{\Delta E / E} = 0.1\%$ ($1 \times 10^{-3}$)
- NKM kicker strength jitter: $\sigma_{\Delta V / V} = 0.5\%$ ($5 \times 10^{-3}$)

### 2.2 Monte Carlo Robustness Evaluator (`evaluate_monte_carlo_robustness`)
- Generates 200 random Gaussian seed realizations for all error components.
- Evaluates exit Twiss parameters, horizontal/vertical mismatch factors ($\mathcal{M}_x, \mathcal{M}_y$), peak beta functions ($\beta_{x,\max}, \beta_{y,\max}$), and beam survival rates across all seeds.
- Computes statistical metrics: mean, standard deviation, 95th percentile ($P_{95}$), and overall feasibility rate (percentage of seeds satisfying $\beta_{\max} \le 60.0\text{ m}$ and transmission $= 100\%$).

---

## 3. Key Results & Sensitivity Ranking

- **Feasibility Rate**:
  - Baseline unoptimized lattice: $0.0\%$ (due to baseline $\beta_{y,\max} = 242.6\text{ m}$).
  - SLSQP optimized lattice: $94.5\%$ feasibility.
  - MOGA knee-point solution: **$100.0\%$ feasibility** across 200 random seeds.
- **95th Percentile Mismatch Metrics ($P_{95}$)**:
  - $P_{95}(\mathcal{M}_x) = 0.42$
  - $P_{95}(\mathcal{M}_y) = 0.48$
- **Sensitivity Ranking**: Quadrupole gradient errors ($\sigma_K/K$) and quad misalignments ($\sigma_{dx}$) are the dominant drivers of exit optics mismatch.

---

## 4. Key Implementation Files Created

- `src/nkm/errors.py`: `ErrorBudgetConfig` dataclass, error injection logic, `evaluate_monte_carlo_robustness()`.
- `scripts/run_tolerance_study.py`: Monte Carlo tolerance study CLI runner supporting `--n-samples`.
- `tests/test_errors.py`: Unit test suite verifying reproducible seed generation, error perturbation, and sensitivity ranking.
- `docs/validation/tolerance_budget.md`: Milestone 06 error budget validation report.

---

## 5. Verification Command

```bash
python scripts/run_tolerance_study.py --n-samples 200
pytest tests/test_errors.py
```
