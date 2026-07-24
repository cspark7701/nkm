# NKM Multi-Objective Genetic Algorithm (MOGA) Pareto Optimization Report

## 1. Executive Summary

This document specifies the Multi-Objective Genetic Algorithm (MOGA / NSGA-II) optimization formulation, physical feasibility enforcement, multi-seed Pareto reproducibility, and archival standards for the NKM Booster-to-Storage-Ring (BTS) transfer line.

---

## 2. Objective and Constraint Formulation

The optimization evaluates trade-offs between three physically distinct objectives subject to hard lattice stability and hardware constraints (`src/nkm/moga.py`):

### Objectives (to minimize):
1. **Total Optical Mismatch ($f_1$)**: $M_x + M_y$ at the BTS exit interface.
2. **Peak Beta Function ($f_2$)**: $\max(\beta_{x,\max}, \beta_{y,\max})$ along the BTS line.
3. **Residual Dispersion ($f_3$)**: $\sqrt{D_x^2 + D_{px}^2}$ at the BTS exit.

### Hard Inequality Constraints ($g_i \le 0$):
1. $g_1 = \max \beta_x - 60.0 \le 0$
2. $g_2 = \max \beta_y - 60.0 \le 0$
3. $g_3 = \text{Hardware limit violation} \le 0$ ($K_i \in [-3.0, +3.0]\text{ m}^{-2}$, $B_{\text{pole}} \le 1.2\text{ T}$)

---

## 3. Strict Feasibility Enforcement & Fallback Protocol

- **Feasibility Rule**: A solution candidate is classified as feasible if and only if all constraint violations $CV \le 10^{-5}$. Infeasible solutions are **never** labeled feasible.
- **Infeasible Fallback**: If an optimization run yields zero feasible candidates (`feasible_fraction = 0.0`), the optimizer returns `success = False`, reports the minimum constraint violation (`min_violation`), and exports the top 5 least-infeasible candidate solutions separately.

---

## 4. True Beam Envelope-to-Aperture Margin Metric

Peak beta function surrogate is replaced with the physical envelope-to-aperture clearance margin $M_{\text{ap}}$:

$$M_{\text{ap}}(s) = r_{\text{pipe}} - \left( 3 \sqrt{\epsilon_x \beta_x(s)} + |D_x(s) \cdot \delta| \right)$$

where $r_{\text{pipe}} = 19.35\text{ mm}$, $\epsilon_x = 0.1\ \mu\text{m}\cdot\text{rad}$, and $\delta = 1.1 \times 10^{-3}$.

---

## 5. Multi-Seed Reproducibility & Archival Standards

- **Multi-Seed Convergence**: Optimization is evaluated across 5 independent random seeds ($42, 101, 202, 303, 404$).
- **Archival Formats**: All population histories, feasible Pareto sets, and representative solution configurations are saved in documented non-pickle JSON/CSV formats under:
  `results/publication_moga/run_<timestamp>/`
  - `moga_summary.json`
  - `moga_pareto_front.csv`
