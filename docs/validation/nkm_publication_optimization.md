# Physically-Constrained BTS Quadrupole Optics Optimization Report

## 1. Executive Summary

This document specifies the physically-constrained, reproducible optimization formulation for matching the BTS transfer line optics to the storage ring target parameters. Generic common bounds are replaced with element-specific magnet hardware limits, and objective residuals are normalized by physical target tolerances.

---

## 2. Hardware and Optics Constraints

All candidate quadrupole configurations are subject to strict hard constraints (`src/nkm/constraints.py`):

| Constraint Category | Parameter / Property | Limit / Bound | Physics Motivation |
| :--- | :--- | :--- | :--- |
| **Quad Strength Limit** | $K_i$ ($i = 1\dots9$) | $[-3.0, +3.0]\text{ m}^{-2}$ | Magnet core saturation & power supply current limits |
| **Pole-Tip Field Limit** | $B_{\text{pole}} = |K_i| \cdot B\rho \cdot r_{\text{bore}}$ | $\le 1.2\text{ T}$ | Ferrite / iron pole-tip saturation limit ($r_{\text{bore}} = 19.35\text{ mm}$) |
| **Peak Beta Function** | $\max(\beta_x(s), \beta_y(s))$ | $\le 60.0\text{ m}$ | Physical aperture stay-clear & chromatic aberration minimization |
| **Peak Dispersion** | $\max |D_x(s)|$ | $\le 1.5\text{ m}$ | Transverse beam envelope & momentum acceptance control |

---

## 3. Normalized Objective Formulation

The objective merit function $J$ separates hard constraint violations from soft target residuals (`src/nkm/objectives.py`). Each residual $r_i$ is normalized by its physical target tolerance $\sigma_i$:

$$r_i = \frac{O_i - O_{i,\text{target}}}{\sigma_i}, \qquad J = \sum_{i=1}^{6} r_i^2$$

### Normalization Scale Factors ($\sigma_i$)
- $\sigma_{\beta_x} = 0.05\text{ m}$, $\sigma_{\beta_y} = 0.05\text{ m}$
- $\sigma_{\alpha_x} = 0.01$, $\sigma_{\alpha_y} = 0.01$
- $\sigma_{D_x} = 0.002\text{ m}$, $\sigma_{D_{px}} = 0.001$

---

## 4. Two-Stage Optimization Algorithm

1. **Stage 1 (Bounded Least-Squares)**: `scipy.optimize.least_squares` minimizes the vector of normalized residuals $\mathbf{r}(\mathbf{K})$ within hardware bounds $[K_{\min}, K_{\max}]$.
2. **Stage 2 (Constrained Refinement)**: `SLSQP` minimizes scalar merit $J(\mathbf{K})$ subject to hard peak-beta bounds and hardware constraints.

---

## 5. Sensitivity Analysis & Significant-Digit Stability

- **Jacobian Sensitivity Matrix**: $\mathbf{J}_{ij} = \frac{\partial O_i}{\partial K_j}$ ($6 \times 9$ matrix) computed via central finite differences.
- **SVD Analysis**: Singular values $\mathbf{S} = [s_1, \dots, s_6]$ characterize optics controllability across quadrupole families.
- **Significant Digits**: Optimized quad strengths are reported to 6 decimal places ($\Delta K \le 10^{-6}\text{ m}^{-2}$), matching power-supply setpoint resolution $\Delta I / I \le 10^{-4}$.

---

## 6. Execution & Verification Artifacts

Summary results and JSON reports are saved under:
`results/bts_publication_optimization/run_<timestamp>/`
- `bts_optimization_summary.json`
