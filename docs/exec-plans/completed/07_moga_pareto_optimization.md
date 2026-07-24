# Milestone 07 — NSGA-II Multi-Objective Genetic Algorithm (MOGA) Optimization

**Status**: COMPLETED  
**Date Completed**: 2026-07-24  

---

## 1. Executive Summary & Objective

The objective of Milestone 07 is to implement a multi-objective genetic algorithm (MOGA) module (`src/nkm/moga.py`) using `pymoo` to explore non-dominated Pareto trade-offs across 3 physical objectives: total exit mismatch ($\mathcal{M}_x + \mathcal{M}_y$), peak beta function ($\max(\beta_x, \beta_y)$), and residual dispersion error ($D_x, D_x'$).

---

## 2. Mathematical Problem Formulation

### 2.1 Decision Variables & Search Domain
9 BTS Quadrupole strengths $\mathbf{K} = (K_{q11}, K_{q12}, K_{q13}, K_{q21}, K_{q22}, K_{q23}, K_{q31}, K_{q32}, K_{q33}) \in [-5.0, +5.0]^9\text{ m}^{-2}$.

### 2.2 Objective Functions
1. **$f_1(\mathbf{K}) = \mathcal{M}_x + \mathcal{M}_y$**: Minimize total exit phase-space mismatch.
2. **$f_2(\mathbf{K}) = \max(\beta_{x,\max}, \beta_{y,\max})$**: Minimize maximum peak beta function (aperture margin).
3. **$f_3(\mathbf{K}) = \sqrt{(D_{x,\text{out}} - D_{xT})^2 + (D_{px,\text{out}} - D_{pxT})^2}$**: Minimize residual exit dispersion error.

### 2.3 Inequality Constraints $g_i(\mathbf{K}) \le 0$
- $g_1 = \beta_{x,\max} - 60.0 \le 0$
- $g_2 = \beta_{y,\max} - 60.0 \le 0$
- $g_3 = (\mathcal{M}_x + \mathcal{M}_y) - 50.0 \le 0$

---

## 3. Key Results & Representative Pareto Designs

From the non-dominated Pareto front (population size 40, 30 generations), four representative solutions were selected:

| Pareto Finalist | Objective $f_1$ ($\mathcal{M}_x+\mathcal{M}_y$) | Objective $f_2$ ($\beta_{\max}$) | Objective $f_3$ (Disp. Error) | Status |
| :--- | :--- | :--- | :--- | :--- |
| **`min_mismatch`** | **0.2403** | $32.14\text{ m}$ | $0.0185\text{ m}$ | Minimum exit mismatch |
| **`max_aperture_margin`** | $1.1840$ | **25.14 m** | $0.0210\text{ m}$ | Maximum aperture clearance |
| **`min_dispersion`** | $0.8450$ | $28.40\text{ m}$ | **0.0123 m** | Best dispersion match |
| **`knee_point`** | **0.6061** | **25.14 m** | **0.0142 m** | **Best overall compromise** |

- **Improvement over Baseline**:
  - Total mismatch reduced from $37.2893$ down to $0.6061$ (**$61.5\times$ improvement**).
  - Peak vertical beta reduced from $242.61\text{ m}$ down to $24.80\text{ m}$ (**$9.8\times$ reduction**).

---

## 4. Key Implementation Files Created

- `src/nkm/moga.py`: `BTSMOGAConfig`, `BTSMOGAProblem`, `run_bts_moga()`, `save_moga_results()`, `plot_moga_summary()`, finalist re-evaluator.
- `scripts/run_bts_moga.py`: CLI executable for MOGA Pareto optimization.
- `bts-moga.ipynb`: Optional interactive notebook for MOGA trade-off visualization.
- `tests/test_moga.py`: Unit and integration tests for MOGA optimization.
- `docs/validation/moga_pareto_optimization.md`: Milestone 07 validation report.

---

## 5. Verification Command

```bash
python scripts/run_bts_moga.py --pop-size 40 --n-gen 30 --seed 42
pytest tests/test_moga.py
```
