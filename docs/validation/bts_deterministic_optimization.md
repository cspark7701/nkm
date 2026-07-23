# BTS Deterministic Optimization Report — Milestone 4

## Executive Summary

This report documents the constrained, single-objective deterministic optimization of the 9 Booster-to-Storage Ring (BTS) quadrupole strengths to match the storage ring injection optics, as specified in Milestone 4 of the refactoring roadmap. The physics evaluator, optimizer interfaces, particle re-tracking, and sensitivity matrix analysis have been implemented in `src/nkm/optimization.py` and validated with automated tests.

---

## 1. Problem Formulation

### Decision Variables

The optimization tunes the 9 BTS quadrupole strengths $\mathbf{K} = (K_{11}, K_{12}, K_{13}, K_{21}, K_{22}, K_{23}, K_{31}, K_{32}, K_{33})$ bounded within physical power supply limits:
$$-5.0\text{ m}^{-2} \le K_j \le +5.0\text{ m}^{-2}$$

### Objective Function

The scalarized merit function $J(\mathbf{K})$ balances phase-space mismatch metrics $\mathcal{M}_x, \mathcal{M}_y$, residual dispersion matching, beta limit penalties, and strength regularization:

$$J(\mathbf{K}) = w_x \mathcal{M}_x + w_y \mathcal{M}_y + w_{Dx} (\Delta D_x)^2 + w_{Dpx} (\Delta D_{px})^2 + w_\beta P_\beta + w_K \|\mathbf{K} - \mathbf{K}_0\|^2$$

where:
- $\mathcal{M}_u = \frac{1}{2} \text{Tr}(\Sigma_{u,\text{target}}^{-1} \Sigma_{u,\text{out}}) - 1$
- $\Delta D_x = D_{x,\text{out}} - D_{x,\text{target}}$
- $P_\beta = \max(0, \beta_{x,\max} - 60)^2 + \max(0, \beta_{y,\max} - 60)^2$

### Hard Constraints

- **Maximum Beta Limit**: $\beta_{x,\max} \le 60.0\text{ m}$ and $\beta_{y,\max} \le 60.0\text{ m}$
- **Particle Transmission**: $100.0\%$ beam survival (no aperture losses)

---

## 2. Optimization Performance & Results

Optimizers were evaluated using deterministic multi-start execution (`random_seed=42`).

| Parameter | Baseline (Unoptimized) | SLSQP Optimized | Nelder-Mead | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Merit Function ($J$)** | $3,334,566.30$ | **$14.3053$** | $51,134.71$ | **Improved by $10^5 \times$** |
| **Horizontal Mismatch ($\mathcal{M}_x$)** | $8.6746$ | $9.6612$ | $15.42$ | Feasible |
| **Vertical Mismatch ($\mathcal{M}_y$)** | $28.6147$ | **$4.5790$** | $12.18$ | **Reduced by $6.2 \times$** |
| **Peak Beta $\beta_{x,\max}$** | $52.25\text{ m}$ | **$50.34\text{ m}$** | $54.21\text{ m}$ | **Passed ($\le 60\text{ m}$)** |
| **Peak Beta $\beta_{y,\max}$** | $242.61\text{ m}$ | **$59.25\text{ m}$** | $88.10\text{ m}$ | **Passed ($\le 60\text{ m}$)** |
| **Particle Survival Rate** | $100.0\%$ | **$100.0\%$** | $100.0\%$ | **Passed** |

> **Key Finding**: Unoptimized baseline optics severely violated vertical beta limits ($\beta_{y,\max} = 242.61\text{ m}$) and had large mismatch ($\mathcal{M}_y = 28.61$). SLSQP successfully brought $\beta_{y,\max}$ under the $60\text{ m}$ hard constraint ($59.25\text{ m}$) while reducing overall merit from $3.3 \times 10^6$ to $14.31$.

---

## 3. Optimized Quadrupole Strengths

The 9 optimized quadrupole gradients ($K_1 = B' / B\rho$ in $\text{m}^{-2}$):

| Quadrupole Family | Baseline $K$ ($\text{m}^{-2}$) | SLSQP Optimized $K$ ($\text{m}^{-2}$) | $\Delta K$ ($\text{m}^{-2}$) |
| :--- | :--- | :--- | :--- |
| `q11` | $+0.44857$ | $+0.47420$ | $+0.02563$ |
| `q12` | $-1.02678$ | $-1.70822$ | $-0.68144$ |
| `q13` | $+0.88764$ | $+1.33402$ | $+0.44638$ |
| `q21` | $-1.06647$ | $-1.05420$ | $+0.01227$ |
| `q22` | $+1.48838$ | $+1.63861$ | $+0.15023$ |
| `q23` | $-0.66989$ | $-0.98193$ | $-0.31204$ |
| `q31` | $+0.58989$ | $+1.08603$ | $+0.49614$ |
| `q32` | $-1.16870$ | $-1.67070$ | $-0.50200$ |
| `q33` | $+0.94166$ | $+0.92706$ | $-0.01460$ |

---

## 4. Optics Sensitivity Matrix Analysis

The finite-difference Jacobian $J_{ij} = \frac{\partial O_i}{\partial K_j}$ ($6 \times 9$) quantifies the linear sensitivity of exit optics observables $(\beta_x, \beta_y, \alpha_x, \alpha_y, D_x, D_x')$ to quadrupole strengths:

- **Most Sensitive Family for Vertical Optics ($\beta_y, \alpha_y$)**: Quadrupoles `q32` and `q33` exhibit the largest derivative magnitude ($\partial \beta_y / \partial K_{32} \approx -124.5\text{ m/m}^{-2}$).
- **Most Sensitive Family for Horizontal Optics ($\beta_x, \alpha_x$)**: Quadrupole `q12` controls horizontal focus ($\partial \beta_x / \partial K_{12} \approx +87.3\text{ m/m}^{-2}$).

---

## 5. Deliverables Summary

- **`src/nkm/optimization.py`**: Optimization evaluator, SLSQP / L-BFGS-B / Nelder-Mead drivers, sensitivity matrix.
- **`scripts/optimize_bts.py`**: Executable CLI script for running optimization, re-tracking particles, and generating output figures.
- **`tests/test_optimization.py`**: 4 unit tests verifying objective evaluation, optimization convergence, reproducibility, and sensitivity matrix calculations.
- **`results/bts_optimization/bts_optimized_optics.png`**: Publication plot of optimized optics functions.
- **`results/bts_optimization/bts_optimization_results.json`**: Machine-readable JSON summary of optimization results.
