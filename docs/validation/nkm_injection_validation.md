# NKM Injection Tracking & Beam Dynamics Validation Report — Milestone 5

## Executive Summary

This report documents the end-to-end simulation of 6D particle beam transport from the BTS exit through the Nonlinear Kicker Magnet (NKM) and into the storage-ring injection region, as specified in Milestone 5 of the refactoring roadmap. The beam generation, 6D tracking models, thin-kick / RK4 integration, and performance metric calculations have been modularized under `src/nkm/` and verified with automated tests.

---

## 1. Beam Distribution & Geometry Setup

The 6D particle ensembles are generated using `generate_6d_beam()`:

- **Beam Energy**: $E_0 = 4.0\text{ GeV}$ ($\gamma = 7827.8$)
- **Emittances**: $\varepsilon_x = \varepsilon_y = 10.89\text{ nm}\cdot\text{rad}$
- **Bunch Parameters**: $\sigma_z = 13.4\text{ mm}$, $\sigma_\delta = 1.1 \times 10^{-3}$
- **Injected Beam Entrance Centroid**: $x_{\text{inj}} = -5.7\text{ mm}$, $x_{\text{inj}}' = +3.0\text{ mrad}$
- **Circulating Stored Beam Entrance Centroid**: $x_{\text{circ}} = 0.0\text{ mm}$, $x_{\text{circ}}' = 0.0\text{ mrad}$

---

## 2. 3-Model Injection Comparison

The dynamics of injected and circulating beams were evaluated across 3 distinct models:

| Metric | Model 1: NKM Off | Model 2: Idealized Linear Kicker | Model 3: Realistic 2D Field-Map | Status / Remarks |
| :--- | :--- | :--- | :--- | :--- |
| **Injected Beam Kick ($\Delta x'$)** | $0.0000\text{ mrad}$ | $-5.7491\text{ mrad}$ | **$-3.7607\text{ mrad}$** | Inward kick towards storage ring orbit |
| **Stored Beam Kick ($\Delta x_{\text{circ}}'$)**| $0.0000\text{ mrad}$ | $0.0000\text{ mrad}$ | **$+0.0029\text{ mrad}$** | **Stored beam perturbation $< 0.003\text{ mrad}$** |
| **Beam Separation at NKM Exit** | $5.7000\text{ mm}$ | $2.6817\text{ mm}$ | **$2.1472\text{ mm}$** | Clear physical beam separation |
| **Injected Beam Transmission** | $100.0\%$ | $100.0\%$ | **$100.0\%$** | 1,000 / 1,000 particles survived |
| **Circulating Beam Transmission** | $100.0\%$ | $100.0\%$ | **$100.0\%$** | 1,000 / 1,000 particles survived |

> **Key Finding**: In Model 3 (Realistic RADIA Field-Map), the non-uniform kicker field provides a substantial $-3.76\text{ mrad}$ deflection to the off-axis injected beam ($x = -5.7\text{ mm}$) while leaving the on-axis stored beam ($x = 0$) virtually unperturbed ($\Delta x_{\text{circ}}' = 0.0029\text{ mrad}$), fulfilling the core physical requirement of the NKM.

---

## 3. Limiting Cases & Field Scale Verification

Linearity and scaling behavior were verified by scanning the NKM field scale factor $S \in [0.0, 1.2]$:

| Field Scale Factor ($S$) | Injected Kick ($\Delta x'$) | Stored Beam Kick ($\Delta x_{\text{circ}}'$) | Beam Separation | Verification Status |
| :--- | :--- | :--- | :--- | :--- |
| **$S = 0.0$ (Zero Field)** | $0.0000\text{ mrad}$ | $0.0000\text{ mrad}$ | $5.7000\text{ mm}$ | **PASSED** (Zero field yields zero kick) |
| **$S = 0.5$ (Half Field)** | $-1.8804\text{ mrad}$ | $+0.0015\text{ mrad}$ | $3.9236\text{ mm}$ | **PASSED** (Proportional half kick) |
| **$S = 1.0$ (Nominal Field)**| $-3.7607\text{ mrad}$ | $+0.0029\text{ mrad}$ | $2.1472\text{ mm}$ | **PASSED** (Nominal operating point) |
| **$S = 1.2$ (Over-driven)** | $-4.5129\text{ mrad}$ | $+0.0035\text{ mrad}$ | $1.4367\text{ mm}$ | **PASSED** (Proportional scale) |

---

## 4. Deliverables Summary

- **`src/nkm/beam.py`**: 6D beam distribution generator, centroid calculations, and projected emittance metrics.
- **`src/nkm/tracking.py`**: Thin-kick, RK4 step integration, and element tracking routines.
- **`src/nkm/injection.py`**: 3-model injection simulation pipeline and metrics summary.
- **`scripts/validate_nkm_injection.py`**: CLI script executing 3-model comparison and field scale scans.
- **`tests/test_injection.py`**: 4 unit tests verifying beam generation, thin kick limiting cases, RK4 step integration, and 3-model tracking metrics.
- **`results/injection/nkm_injection_phasespace.png`**: Publication plot of 6D phase space distributions.
- **`results/injection/injection_validation_metrics.json`**: Machine-readable JSON summary of injection metrics.
