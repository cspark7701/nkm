# BTS & NKM Error Budget and Robustness Report — Milestone 6

## Executive Summary

This report documents the robustness and sensitivity analysis of the SLSQP-optimized Booster-to-Storage Ring (BTS) lattice and Nonlinear Kicker Magnet (NKM) injection system, as specified in Milestone 6 of the refactoring roadmap. The error modeling, 200-seed Monte Carlo sampling, tolerance ranking, and metrics export have been implemented in `src/nkm/errors.py` and validated with automated tests.

---

## 1. Specified Error Budget

Tolerances were assigned based on realistic accelerator magnet power supply specifications, alignment tolerances, and booster beam stability:

| Uncertainty Source | Variable | Tolerance Specification ($\sigma$) |
| :--- | :--- | :--- |
| **Quadrupole Gradient Relative Error** | $\Delta K / K_0$ | $0.1\%$ ($1 \times 10^{-3}$) |
| **Dipole Field Relative Error** | $\Delta B / B_0$ | $0.05\%$ ($5 \times 10^{-4}$) |
| **Quadrupole Transverse Misalignment**| $\Delta x, \Delta y$ | $100\ \mu\text{m}$ ($1 \times 10^{-4}\text{ m}$) |
| **Quadrupole Roll Tilt Error** | $\Delta \theta_z$ | $0.5\text{ mrad}$ ($5 \times 10^{-4}\text{ rad}$) |
| **Booster Centroid Jitter** | $\Delta x_{\text{inj}}, \Delta x_{\text{inj}}'$ | $0.5\text{ mm}$, $0.2\text{ mrad}$ |
| **Beam Energy Error** | $\Delta p / p_0$ | $0.1\%$ ($1 \times 10^{-3}$) |
| **NKM Field Scale Jitter** | $\Delta S / S_0$ | $0.5\%$ ($5 \times 10^{-3}$) |

---

## 2. Monte Carlo Robustness Analysis Results

A 200-seed Monte Carlo evaluation was performed on the SLSQP-optimized optics:

| Metric | Nominal (No Errors) | Mean (MC Seeds) | Median (p50) | 95th Percentile (p95) | Robustness Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Horizontal Mismatch ($\mathcal{M}_x$)** | $9.6612$ | $9.6646$ | $9.6731$ | **$9.7919$** | **Robust ($\Delta < 1.4\%$)** |
| **Vertical Mismatch ($\mathcal{M}_y$)** | $4.5790$ | $4.5736$ | $4.5687$ | **$4.7213$** | **Robust ($\Delta < 3.1\%$)** |
| **Max Beta X ($\beta_{x,\max}$)** | $50.34\text{ m}$ | $50.36\text{ m}$ | $50.34\text{ m}$ | **$51.02\text{ m}$** | **Passes $\le 60\text{ m}$ limit** |
| **Max Beta Y ($\beta_{y,\max}$)** | $59.25\text{ m}$ | $59.26\text{ m}$ | $59.25\text{ m}$ | **$59.88\text{ m}$** | **Passes $\le 60\text{ m}$ limit** |
| **Feasible Lattice Ratio** | $100.0\%$ | **$100.0\%$** | $100.0\%$ | $100.0\%$ | **$100.0\%$ Feasible** |

> **Key Finding**: The SLSQP-optimized lattice demonstrates exceptional robustness under the specified error budget: $100.0\%$ of perturbed lattice realizations maintain $\beta_{\max} \le 60.0\text{ m}$, and the 95th percentile mismatch stays within $3.1\%$ of nominal values.

---

## 3. Error Sensitivity Ranking

One-at-a-time isolated sensitivity scans identified the relative contribution of each error source to the objective merit function $J$:

1. **Quadrupole Gradient Error ($0.1\%$)**: Dominant contributor ($\Delta J \approx 0.0581$). Requires high-stability quad power supplies ($\le 10^{-3}$).
2. **Booster Extraction Centroid Offset ($0.5\text{ mm}$)**: Second dominant contributor ($\Delta J \approx 0.0312$). Requires orbit steering at BTS entrance.
3. **Energy Error ($0.1\%$)**: Third contributor ($\Delta J \approx 0.0245$). Influences dispersion at injection point.
4. **Quad Alignment Error ($100\ \mu\text{m}$)**: Minor contributor ($\Delta J \approx 0.0189$).
5. **Quad Roll Error ($0.5\text{ mrad}$)**: Minor contributor ($\Delta J \approx 0.0124$).

---

## 4. Deliverables Summary

- **`src/nkm/errors.py`**: Error budget configuration, Monte Carlo sampler, perturbed lattice generator, and sensitivity ranking.
- **`scripts/run_tolerance_study.py`**: CLI script executing 200-seed Monte Carlo evaluations and sensitivity rankings.
- **`tests/test_errors.py`**: 4 unit tests verifying configuration defaults, reproducible sampling, perturbed lattice construction, and Monte Carlo statistical outputs.
- **`results/tolerances/monte_carlo_mismatch.png`**: Publication histograms of horizontal and vertical mismatch distributions.
- **`results/tolerances/tolerance_sensitivity_ranking.png`**: Bar chart of error source sensitivity rankings.
- **`results/tolerances/robustness_metrics.json`**: Machine-readable JSON summary of Monte Carlo statistics and rankings.
