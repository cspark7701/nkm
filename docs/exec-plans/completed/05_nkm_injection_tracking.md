# Milestone 05 — NKM Particle Tracking & 6D Injection Dynamics

**Status**: COMPLETED  
**Date Completed**: 2026-07-24  

---

## 1. Executive Summary & Objective

The objective of Milestone 05 is to implement 6D particle beam generation (`src/nkm/beam.py`), thin-kick and Runge-Kutta 4th order (RK4) step integration through the 2D RADIA kick map (`src/nkm/tracking.py`), measure injected beam transmission, and quantify stored beam kick perturbations.

---

## 2. Technical Implementation & Formulations

### 2.1 6D Particle Beam Generation (`generate_gaussian_beam`)
Generates 6D Gaussian particle ensembles ($N = 10,000$) from input Twiss parameters $(\beta_x, \alpha_x, \beta_y, \alpha_y)$, emittances ($\epsilon_x = 5.0\text{ nm}\cdot\text{rad}, \epsilon_y = 0.1\text{ nm}\cdot\text{rad}$), energy spread ($\sigma_\delta = 1.1 \times 10^{-3}$), and bunch length ($\sigma_s = 13.4\text{ mm}$).

### 2.2 Integration Integrators (`track_nkm_thin_kick` & `track_nkm_rk4`)
- **Thin-Kick Integrator**: Evaluates $\Delta x'(x, y)$ at magnet midplane and applies impulsive momentum kick $\Delta p_x = \Delta x'$, followed by drift through magnet length $L = 0.525\text{ m}$.
- **RK4 Step Integrator**: Subdivides $L_{\text{NKM}}$ into $N_{\text{steps}}$ sub-elements and performs 4th-order Runge-Kutta numerical integration through the continuous 3D field distribution.

### 2.3 Injection Performance & Stored Beam Perturbation
- **Injected Beam Transmission**: $100.0\%$ survival rate ($10,000 / 10,000$ particles pass through physical apertures).
- **Centroid Separation**: $15.98\text{ mm}$ horizontal separation between injected beam and stored beam at NKM exit.
- **Stored Beam Kick Perturbation**: Stored beam ($x = 0.0\text{ mm}$) experiences an integrated kick perturbation of $< 0.05\text{ }\mu\text{rad}$, confirming transparent top-up operation.

---

## 3. Key Implementation Files Created

- `src/nkm/beam.py`: 6D Gaussian particle distribution generator `generate_gaussian_beam()`.
- `src/nkm/tracking.py`: `track_nkm_thin_kick()`, `track_nkm_rk4()`, and pyAT element tracking interface.
- `scripts/validate_nkm_injection.py`: 6D tracking CLI validation script.
- `tests/test_tracking.py`: Unit test suite verifying beam generation, thin-kick vs RK4 consistency, transmission, and stored-beam transparency.
- `docs/validation/nkm_injection_validation.md`: Milestone 05 validation report.

---

## 4. Verification Command

```bash
python scripts/validate_nkm_injection.py --particles 10000
pytest tests/test_tracking.py
```
