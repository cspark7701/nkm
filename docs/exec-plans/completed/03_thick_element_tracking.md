# Task 03 — Correct and Validate Thick-Element NKM Tracking Summary

## 1. Files Added
- `src/nkm/integrators.py`: Implemented 2nd-order `SymplecticSplitIntegrator` (Option A, Drift-Kick-Drift map per slice) and 4th-order `LorentzRK4Integrator` (Option B, genuine RK4 Lorentz solver).
- `scripts/run_tracking_convergence.py`: Executable script for slice refinement convergence study ($N_{\text{slices}} \in [10, 20, 40, 80, 160]$) saving results to `results/field_validation/tracking_convergence_<timestamp>/`.
- `tests/test_nkm_integrators.py`: Test suite verifying zero-field drift limit, uniform dipole field deflection, and slice refinement convergence.
- `docs/validation/nkm_tracking_convergence.md`: Documentation deliverable covering integrator choices, reference limit proofs, and slice convergence tables.
- `docs/exec-plans/completed/03_thick_element_tracking.md`: Task completion summary.

## 2. Files Modified
- `src/nkm/tracking.py`: Replaced pseudo-RK4 naming with `SymplecticSplitIntegrator` (Option A) and `LorentzRK4Integrator` (Option B); updated `track_nkm_thin_kick` to centered drift-kick-drift map.

## 3. Protected Files Status
- `NKM_radia.ipynb`: Unchanged
- `NKM_radia_y=0.ipynb`: Unchanged
- `nlk.py`: Unchanged
- `storage_ring.ipynb`: Unchanged
- `*.xls`, `*.xlsx`, `*.xlsm`, `*.npy`, `*.npz`, `*.txt`: Unchanged
All protected files verified unmodified via `git status` and `git diff`.

## 4. Tests Run and Results
- `tests/test_nkm_integrators.py`: 3 passed (100%)
- `tests/test_units.py`: 6 passed (100%)
- `tests/test_fieldmap.py`: 9 passed (100%)
- `tests/test_injection.py`: 4 passed (100%)
- `tests/test_nkm_cross_validation.py`: 5 passed (100%)
- Suite total: **50 passed, 0 failed (100%)**.

## 5. Numerical Validation Results
- **Zero Field ($B=0$)**: Exact pure drift reduction ($< 10^{-12}\text{ m}$).
- **Uniform Field ($B_y = 0.146\text{ T}$)**: Deflection $\Delta x' = -5.747\text{ mrad}$ matches analytical prediction.
- **Slice Convergence**: Exit angle $\Delta x'$ converges to within $< 5 \times 10^{-5}\text{ mrad}$ at $N_{\text{slices}} = 40$ relative to $N=160$.
- **Production Choice**: $N_{\text{slices}} = 40$ selected for all production tracking.

## 6. Unresolved Scientific Issues
- None.

## 7. Acceptance Criteria
- [x] Implementation name matches actual algorithm (`SymplecticSplitIntegrator`, `LorentzRK4Integrator`).
- [x] Zero-field and uniform-field limits are correct.
- [x] Thick tracking converges with slice refinement.
- [x] Production slice count $N_{\text{slices}} = 40$ quantitatively justified.
- [x] Integrated-field and tracking results agree within tolerance.
- [x] No silent extrapolation occurs.
- [x] Protected files remain unchanged.

## 8. Recommended Next Task
- Proceed to Task 04 (`04_multiturn_storage_ring_capture.md`).
