# BTS Multi-Objective Genetic Algorithm (MOGA) Pareto Optimization Report — Milestone 7

## Executive Summary

This report documents the multi-objective Pareto optimization of the 9 Booster-to-Storage Ring (BTS) transfer line quadrupole strengths using NSGA-II, as specified in Milestone 7 of the refactoring roadmap. The formulation, solver interfaces, duplicate elimination, Pareto front generation, representative design selection, deep 6D re-evaluation, and error budget robustness analysis have been modularized under `src/nkm/moga.py` and validated with automated tests.

`bts-moga.ipynb` remains an optional, stand-alone notebook that reuses modular library components without duplicating lattice or optics code, providing full transparency on computational cost.

---

## 1. Problem Formulation

### Decision Variables

The optimization tunes the 9 BTS quadrupole strengths $\mathbf{K} = (K_{q11}, K_{q12}, K_{q13}, K_{q21}, K_{q22}, K_{q23}, K_{q31}, K_{q32}, K_{q33})$ bounded within physical power supply limits:
$$-5.0\text{ m}^{-2} \le K_j \le +5.0\text{ m}^{-2}$$

### Multi-Objective Trade-off Functions

Rather than scalarizing competing physics goals into an arbitrary weighted sum, MOGA solves the multi-objective optimization problem to reveal explicit Pareto trade-offs:

1. **Objective 1 — Total Optical Mismatch ($f_1$)**:
   $$f_1(\mathbf{K}) = \mathcal{M}_x + \mathcal{M}_y$$
   where $\mathcal{M}_u = \frac{1}{2} \text{Tr}(\Sigma_{u,\text{target}}^{-1} \Sigma_{u,\text{out}}) - 1$ measures phase-space matching to storage ring injection optics.

2. **Objective 2 — Peak Beta Function / Aperture Risk ($f_2$)**:
   $$f_2(\mathbf{K}) = \max\left(\max_s \beta_x(s), \max_s \beta_y(s)\right)$$
   Minimizing $f_2$ maximizes physical aperture clearance along the transport line.

3. **Objective 3 — Residual Dispersion ($f_3$)**:
   $$f_3(\mathbf{K}) = \sqrt{(D_{x,\text{out}} - D_{x,\text{target}})^2 + (D_{px,\text{out}} - D_{px,\text{target}})^2}$$

### Inequality Constraints ($g_i(\mathbf{K}) \le 0$)

- **Hard Beta Limit**: $g_1 = \max_s \beta_x(s) - 60.0\text{ m} \le 0$
- **Hard Beta Limit**: $g_2 = \max_s \beta_y(s) - 60.0\text{ m} \le 0$
- **Mismatch Bound**: $g_3 = (\mathcal{M}_x + \mathcal{M}_y) - 50.0 \le 0$

---

## 2. Representative Pareto Solutions

MOGA generates a non-dominated Pareto front from which 4 key representative designs are extracted:

1. **`min_mismatch`**: Minimizes total exit optical mismatch ($f_1$).
2. **`max_aperture_margin`**: Minimizes peak beta function ($f_2$), maximizing clearance against vacuum chamber walls.
3. **`min_dispersion`**: Minimizes residual dispersion error ($f_3$) at the injection point.
4. **`knee_point`**: Balanced compromise closest to the normalized ideal point in 3D objective space.

### Re-evaluation & Robustness Comparison

| Representative Solution | Total Mismatch ($\mathcal{M}_x+\mathcal{M}_y$) | Peak $\beta$ [m] | Residual Disp. [m] | MC Feasibility Rate |
| :--- | :--- | :--- | :--- | :--- |
| **`min_mismatch`** | **$0.2403$** | $29.96\text{ m}$ | $0.1724\text{ m}$ | **$100.0\%$** |
| **`max_aperture_margin`**| $1.0989$ | **$25.14\text{ m}$** | $0.0299\text{ m}$ | **$100.0\%$** |
| **`min_dispersion`** | $1.9190$ | $25.14\text{ m}$ | **$0.0123\text{ m}$** | **$100.0\%$** |
| **`knee_point` (Compromise)** | **$0.6061$** | **$25.14\text{ m}$** | **$0.0491\text{ m}$** | **$100.0\%$** |
| *SLSQP Baseline (M4)* | $14.2402$ | $59.25\text{ m}$ | $0.0340\text{ m}$ | $92.0\%$ |

---

## 3. Analysis & Key Insights

1. **Trade-off Between Mismatch & Aperture Risk**:
   Focusing purely on optics matching (`min_mismatch`) achieves an ultra-low total mismatch of $0.2403$ while keeping peak beta at $29.96\text{ m}$.
2. **Knee-Point Solution Superiority**:
   The `knee_point` compromise design achieves a total mismatch of $0.6061$, peak beta of $25.14\text{ m}$, and residual dispersion of $0.0491\text{ m}$, providing a $23.5\times$ improvement in mismatch and a $34.1\text{ m}$ reduction in peak beta compared to the single-objective SLSQP result from Milestone 4.
3. **Monte Carlo Robustness**:
   All 4 representative Pareto designs achieve a $100\%$ Monte Carlo feasibility rate under standard quadrupole gradient, alignment, and roll error budgets.


---

## 4. Deliverables & Acceptance Verification

- **`src/nkm/moga.py`**: Modular NSGA-II problem formulation, Pareto extractor, representative selector, and plotting functions.
- **`bts-moga.ipynb`**: Clean optional notebook utilizing library imports and documenting execution cost.
- **`scripts/run_bts_moga.py`**: CLI executable for batch MOGA optimization.
- **`tests/test_moga.py`**: 4 unit tests verifying problem evaluation, reproducibility, solution selection, and saving/plotting.
- **`results/moga/`**:
  - `moga_pareto_front.csv`
  - `representative_solutions.json`
  - `moga_result.pkl`
  - `moga_pareto_front_2d.png`
  - `moga_convergence.png`
  - `moga_parallel_coordinates.png`
