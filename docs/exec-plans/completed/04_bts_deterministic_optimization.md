# Milestone 04 — Deterministic Constrained BTS Optics Matching

**Status**: COMPLETED  
**Date Completed**: 2026-07-24  

---

## 1. Executive Summary & Objective

The objective of Milestone 04 is to implement a deterministic constrained optimization module (`src/nkm/optics_optimizer.py`) using SciPy's SLSQP and trust-constr solvers. The optimizer tunes the 9 BTS quadrupole gradients ($K_1 \dots K_9$) to minimize exit optics mismatch ($\mathcal{M}_x, \mathcal{M}_y$) and residual dispersion while enforcing hard peak beta function constraints ($\beta_{x,\max}, \beta_{y,\max} \le 60.0\text{ m}$).

---

## 2. Mathematical Formulation & Problem Definition

### 2.1 Optimization Objective Function

$$\min_{\mathbf{K} \in [-5.0, +5.0]^9} J(\mathbf{K}) = w_x \mathcal{M}_x + w_y \mathcal{M}_y + w_D (D_x - D_{xT})^2 + w_{D'} (D_{px} - D_{pxT})^2 + P_\beta(\mathbf{K})$$

- Decision variables: 9 quadrupole strengths $\mathbf{K} = (K_{q11}, K_{q12}, K_{q13}, K_{q21}, K_{q22}, K_{q23}, K_{q31}, K_{q32}, K_{q33})$.
- Hard constraints:
  $$g_1(\mathbf{K}) = \beta_{x,\max}(\mathbf{K}) - 60.0 \le 0$$
  $$g_2(\mathbf{K}) = \beta_{y,\max}(\mathbf{K}) - 60.0 \le 0$$

### 2.2 Sensitivity Analysis

Calculates the $4 \times 9$ Jacobian matrix $J_{ij} = \frac{\partial O_i}{\partial K_j}$ for observables $O = (\beta_x, \alpha_x, \beta_y, \alpha_y)$ at the BTS exit to identify the most effective quadrupole knobs.

---

## 3. Key Results & Performance Comparison

- **SLSQP Convergence**: Converged in 28 iterations with 100% feasibility.
- **Vertical Beta Function**: Reduced peak vertical beta $\beta_{y,\max}$ from $242.61\text{ m}$ down to $59.25\text{ m}$ (satisfying $\le 60.0\text{ m}$ constraint).
- **Vertical Mismatch Factor**: Reduced vertical mismatch $\mathcal{M}_y$ from $28.6147$ down to $4.5790$ ($6.25\times$ reduction).
- **Exit Dispersion Matching**: Matched exit dispersion $D_x = 0.0815\text{ m}$ and $D_{px} = 0.0470\text{ rad}$ to target values ($0.0809\text{ m}, 0.0475\text{ rad}$).

---

## 4. Key Implementation Files Created

- `src/nkm/optics_optimizer.py`: `BTSOpticsOptimizer` class, SLSQP/trust-constr solvers, Jacobian sensitivity calculator.
- `scripts/optimize_bts.py`: CLI optimization runner supporting `--method SLSQP|trust-constr`.
- `tests/test_optics_optimizer.py`: Unit tests for deterministic optimization convergence, bounds enforcement, and sensitivity matrix.
- `docs/validation/bts_deterministic_optimization.md`: Milestone 04 validation report.

---

## 5. Verification Command

```bash
python scripts/optimize_bts.py --method SLSQP
pytest tests/test_optics_optimizer.py
```
