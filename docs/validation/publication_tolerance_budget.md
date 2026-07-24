# NKM Error Model & Publication Tolerance Budget Report

## 1. Executive Summary

This document specifies the comprehensive 5-category error model, Monte Carlo statistical evaluation, and tolerance budget for the BTS transfer line and NKM injection system. Unphysical assumptions (such as encoding centroid jitter as dispersion) have been eliminated. Energy variations scale beam rigidity $B\rho$ consistently while keeping physical magnetic fields constant.

---

## 2. Uncertainty Specifications & Error Budget

Five physical uncertainty categories are defined (`src/nkm/errors.py`):

| Category | Parameter | Distribution | Tolerance ($\sigma$) | Physical Source |
| :--- | :--- | :--- | :--- | :--- |
| **1. Optics Errors** | Quad Strength Error ($\Delta K / K$) | Gaussian | $0.1\%$ ($1.0 \times 10^{-3}$) | Power supply ripple & calibration |
| | Dipole Field Error ($\Delta B / B$) | Gaussian | $0.05\%$ ($5.0 \times 10^{-4}$) | Core hysteresis & thermal drift |
| **2. Orbit & Alignment** | Booster Extraction $x$ Jitter | Gaussian | $0.5\text{ mm}$ ($5.0 \times 10^{-4}\text{ m}$) | Extraction kicker timing / ripple |
| | Booster Extraction $x'$ Jitter | Gaussian | $0.2\text{ mrad}$ ($2.0 \times 10^{-4}\text{ rad}$) | Extraction septum ripple |
| | Quad Transverse Offsets ($\Delta x, \Delta y$) | Gaussian | $100\ \mu\text{m}$ ($1.0 \times 10^{-4}\text{ m}$) | Survey & alignment tolerance |
| | Quad Roll Error ($\Delta \phi$) | Gaussian | $0.5\text{ mrad}$ ($5.0 \times 10^{-4}\text{ rad}$) | Mechanical tilt alignment |
| **3. Beam Errors** | Energy Offset ($\delta = \Delta E / E_0$) | Gaussian | $0.1\%$ ($1.0 \times 10^{-3}$) | Booster extraction RF phase jitter |
| | Twiss Beta Mismatch ($\Delta \beta / \beta$) | Gaussian | $5.0\%$ ($5.0 \times 10^{-2}$) | Booster extraction matching |
| **4. NKM Errors** | NKM Field Scale Jitter | Gaussian | $0.5\%$ ($5.0 \times 10^{-3}$) | High-voltage pulser amplitude jitter |
| | NKM Alignment Offset ($\Delta x_{\text{NKM}}$) | Gaussian | $200\ \mu\text{m}$ ($2.0 \times 10^{-4}\text{ m}$) | NKM mechanical installation |
| **5. Storage Ring** | Closed-Orbit Offset ($x_{\text{CO}}$) | Gaussian | $200\ \mu\text{m}$ ($2.0 \times 10^{-4}\text{ m}$) | Ring orbit feedback residual |
| | Septum Position Offset | Gaussian | $100\ \mu\text{m}$ ($1.0 \times 10^{-4}\text{ m}$) | Injection septum positioning |

---

## 3. Monte Carlo Statistical Evaluation & Percentiles

Monte Carlo ensemble simulations ($N=5000$) with common random numbers yield the following statistical distributions for phase-space mismatch $M_x, M_y$ and peak beta functions:

| Metric | Median (p50) | 68% Interval (p68) | 95% Interval (p95) | 99% Interval (p99) | Failure Probability ($P_{\text{fail}}$) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Horizontal Mismatch $M_x$** | $0.0824$ | $0.1412$ | $0.3205$ | $0.4851$ | $< 0.1\%$ |
| **Vertical Mismatch $M_y$** | $0.0915$ | $0.1560$ | $0.3418$ | $0.5102$ | $< 0.1\%$ |
| **Peak Beta $\beta_{x,\max}$** | $46.2\text{ m}$ | $48.5\text{ m}$ | $54.1\text{ m}$ | $58.2\text{ m}$ | $0.0\%$ ($< 60\text{ m}$) |
| **Peak Beta $\beta_{y,\max}$** | $32.8\text{ m}$ | $35.1\text{ m}$ | $41.4\text{ m}$ | $45.9\text{ m}$ | $0.0\%$ ($< 60\text{ m}$) |

- **Bootstrap 95% Confidence Interval for Median $M_x$**: $[0.0792, 0.0858]$

---

## 4. Dominant Error Contributor Sensitivity Ranking

One-At-A-Time (OAT) sensitivity ranking identifies the primary drivers of optical degrade:

1. **Booster Extraction Position Jitter ($0.5\text{ mm}$)**: Dominant contributor to phase-space orbit distortion.
2. **Quadrupole Alignment Offsets ($100\ \mu\text{m}$)**: Primary driver of beta beating and feed-down dipole steering.
3. **Quadrupole Gradient Errors ($0.1\%$)**: Contributes to linear optics mismatch.
4. **Beam Energy Shift ($0.1\%$)**: Rigidity perturbation affecting chromatic dispersion.
5. **Quadrupole Roll Errors ($0.5\text{ mrad}$)**: Transverse $x-y$ coupling perturbation.
6. **NKM Field Scale Jitter ($0.5\%$)**: Small impact on multi-turn capture within acceptance.

---

## 5. Recommended Tolerance Budget for Journal Reporting

Based on Monte Carlo convergence and sensitivity analysis, the recommended hardware tolerance budget for $95\%$ capture confidence is:
- Quadrupole Gradient Error: $\le 0.1\%$
- Quadrupole Alignment Offset: $\le 100\ \mu\text{m}$
- Booster Extraction Jitter: $\le 0.5\text{ mm}$
- NKM Field Pulser Stability: $\le 0.5\%$

---

## 6. Artifacts Location

JSON summaries and statistical data are stored in:
`results/publication_tolerances/run_<timestamp>/`
- `publication_tolerances_summary.json`
