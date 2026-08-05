# Milestone 33 — Task 02: Validate True Longitudinal RADIA Field Integration

**Author**: Chong Shik Park  
**Affiliation**: Department of Accelerator Science and Center for Accelerator Research, Korea University, Sejong, 30019 Republic of Korea

---

## 1. Executive Summary

This milestone completed **Task 02 — Validate True Longitudinal RADIA Field Integration**. It implemented direct 1D numerical quadrature functions (`integrate_longitudinal_field` in `src/nkm/fieldmap.py`), clearly distinguishing transverse field profiles $B_y(x)$, longitudinal profiles $B_y(z)$, and 2D integrated kick maps $I_y(x,y)$. Direct Simpson and Trapezoidal numerical quadratures along $z$ were compared against the 2D kick map (`kickmap_file.txt`), analytical 4-wire model (`nlk.py`), and thick symplectic/RK4 tracking.

## 2. Work Completed

1. **Direct 1D Longitudinal Quadrature (`src/nkm/fieldmap.py`)**:
   - Implemented `integrate_longitudinal_field(z, by, method="simpson")` performing direct 1D quadrature along longitudinal axis $z$ (meters).
   - Exported `integrate_longitudinal_field` in package root `src/nkm/__init__.py`.

2. **Validation Script & Machine-Readable Output**:
   - Created `scripts/validate_task02_longitudinal_integration.py` performing grid resolution convergence scans ($N_z = 21, 51, 101, 201, 401, 1001$) and generating publication-quality figures under `results/field_validation/task02_run_<timestamp>/`:
     - `fig1_longitudinal_field_profile.png` ($B_y(z)$ profile and cumulative integral)
     - `fig2_longitudinal_quadrature_convergence.png` (Grid resolution residual log-log plot)
     - `fig3_fieldmap_vs_analytical_comparison.png` (RADIA kick map vs 4-wire `nlk.py` model comparison)
   - Exported metrics JSON to `results/field_validation/task02_run_<timestamp>/task02_longitudinal_integration_metrics.json`.

3. **Unit Test Suite Integration**:
   - Added `test_integrate_longitudinal_field` in `tests/test_fieldmap.py` verifying Simpson vs Trapezoidal quadrature against analytical Gaussian integrals (`scipy.special.erf`).
   - Verified 81 / 81 unit tests passing across the repository.

4. **Domain Boundary Guards**:
   - Verified that `OutOfDomainError` is strictly raised when evaluating fields outside bounds ($z \notin [-0.05, 0.05]\text{ m}$), refusing silent extrapolation.

## 3. Protected Files Status

- `NKM_radia.ipynb`: Unchanged
- `NKM_radia_y=0.ipynb`: Unchanged
- `nlk.py`: Unchanged
- `storage_ring.ipynb`: Unchanged
- `By.txt`, `kickmap_file.txt`, `K4GSR_HBIv4-1.mat`, `nkm_field.xlsx`: Unchanged
- All protected scientific source data files verified untouched via `git status`.

## 4. Key Numerical Results

- **Peak Field at $x = -10\text{ mm}$**: $-0.146109\text{ T}$
- **Integrated Field $I_y$ (Simpson Quadrature, $N_z=201$)**: $-0.070112\text{ T}\cdot\text{m}$
- **Integrated Field $I_y$ (Trapezoid Quadrature, $N_z=201$)**: $-0.070108\text{ T}\cdot\text{m}$
- **Simpson vs Trapezoid Residual**: $4.0 \times 10^{-6}\text{ T}\cdot\text{m}$
- **Direct Quadrature Kick Angle ($4.0\text{ GeV}$ electron)**: $-5.2547\text{ mrad}$
- **2D Kick Map Kick Angle ($x=-10\text{ mm}$)**: $-5.4341\text{ mrad}$
- **Symplectic Thick Tracking Kick Angle**: $-5.0424\text{ mrad}$
- **RK4 Thick Tracking Kick Angle**: $-5.0420\text{ mrad}$
- **Thick Tracking vs Quadrature Residual**: $2.123 \times 10^{-4}\text{ rad}$ ($0.21\text{ mrad}$)
- **Domain Guard Enforcement**: Verified (`True`).
