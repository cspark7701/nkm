# Milestone 32 — Task 01: Fix NKM Kick Component and Sign Conventions

**Author**: Chong Shik Park  
**Affiliation**: Department of Accelerator Science and Center for Accelerator Research, Korea University, Sejong, 30019 Republic of Korea

---

## 1. Executive Summary

This milestone completed **Task 01 — Fix NKM Kick Component and Sign Conventions**. It established a single, authoritative, component-aware field-to-kick conversion module (`integrated_field_to_transverse_kicks` and `transverse_kicks_to_integrated_field` in `src/nkm/units.py`) based on Lorentz-force physics. All 2D kick map evaluation methods (`src/nkm/kickmap.py`), symplectic thick integrators, and RK4 integrators (`src/nkm/integrators.py`) now use this unified implementation.

## 2. Work Completed

1. **Unified Component-Aware Converter (`src/nkm/units.py`)**:
   - Implemented `integrated_field_to_transverse_kicks(int_bx_t_m, int_by_t_m, beam_energy_eV, particle_charge_C, coordinate_convention)`:
     $$\Delta x' = \frac{q}{|q|} \frac{\int B_y\,ds}{B\rho}, \quad \Delta y' = -\frac{q}{|q|} \frac{\int B_x\,ds}{B\rho}$$
   - Implemented `transverse_kicks_to_integrated_field(delta_xp, delta_yp, ...)` inverse mapping.
   - Refactored `integrated_field_to_kick()` and `kick_to_integrated_field()` to delegate to the component-aware functions.

2. **2D Kick Map & Integrator Integration**:
   - Updated `NKMKickMap2D.evaluate_kick()` in `src/nkm/kickmap.py` to use `integrated_field_to_transverse_kicks()` for simultaneous 2-plane field maps.
   - Updated `SymplecticSplitIntegrator` and `LorentzRK4Integrator` in `src/nkm/integrators.py` to evaluate 2-plane transverse deflection angles.

3. **Validation Script & Machine-Readable Output**:
   - Created `scripts/validate_task01_kick_conventions.py` outputting metrics JSON to `results/kick_conventions/task01_metrics.json`.
   - Verified exact charge sign reversal ($q = -e$ vs $q = +e$) and symplectic/RK4 agreement to within $7.8 \times 10^{-18}\text{ rad}$.

4. **Unit Test Suite Integration**:
   - Added `test_integrated_field_to_transverse_kicks_two_plane` in `tests/test_units.py`.
   - Added `test_two_plane_thin_thick_kick_agreement` in `tests/test_nkm_integrators.py`.
   - Passed 80 / 80 unit tests (100% pass rate across the full repository).

## 3. Protected Files Status

- `NKM_radia.ipynb`: Unchanged
- `NKM_radia_y=0.ipynb`: Unchanged
- `nlk.py`: Unchanged
- `storage_ring.ipynb`: Unchanged
- `By.txt`, `kickmap_file.txt`, `K4GSR_HBIv4-1.mat`, `nkm_field.xlsx`: Unchanged
- All protected scientific source data files verified untouched via `git status`.

## 4. Key Numerical Results

- **Magnetic Rigidity ($B\rho$ at $4.0\text{ GeV}$)**: $13.342564\text{ T}\cdot\text{m}$
- **Electron 2-plane Deflection ($\int B_x ds=0.05\text{ T}\cdot\text{m}, \int B_y ds=0.0767\text{ T}\cdot\text{m}$)**:
  - $\Delta x' = -5.7485\text{ mrad}$
  - $\Delta y' = +3.7474\text{ mrad}$
- **Positron Charge Sign Reversal**:
  - $\Delta x' = +5.7485\text{ mrad}$
  - $\Delta y' = -3.7474\text{ mrad}$
  - Exact anti-symmetry verified ($\text{True}$).
- **Symplectic vs Analytic Error**: $7.806 \times 10^{-18}\text{ rad}$
- **RK4 vs Analytic Error**: $7.806 \times 10^{-18}\text{ rad}$
