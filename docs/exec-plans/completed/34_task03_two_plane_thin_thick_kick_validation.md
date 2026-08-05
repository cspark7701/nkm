# Milestone 34 — Task 03: Add Two-Plane Thin/Thick NKM Validation

**Author**: Chong Shik Park  
**Affiliation**: Department of Accelerator Science and Center for Accelerator Research, Korea University, Sejong, 30019 Republic of Korea

---

## 1. Executive Summary

This milestone completed **Task 03 — Add Two-Plane Thin/Thick NKM Validation**. It validated two-plane particle tracking ($x, y$) across 6 field configurations (zero field, constant $B_y$, constant $B_x$, coupled constant $B_x, B_y$, linear quadrupole field, and coupled off-axis field away from $y=0$) and 4 tracking formulations (Analytic prediction, Centered Thin Lens map, 2nd-order Verlet Symplectic Split-Operator, and 4th-order Runge-Kutta Lorentz Integrator). It performed a slice count convergence scan ($N_{\text{slices}} \in \{5, 10, 20, 40, 80, 160, 320\}$), quantitatively justifying $N_{\text{slices}} = 40$ as the production setting.

## 2. Work Completed

1. **Two-Plane Tracking Integration (`src/nkm/tracking.py`)**:
   - Updated `track_nkm_thin_kick` to call `integrated_field_to_transverse_kicks()`, supporting simultaneous 2-plane kicks ($\Delta x', \Delta y'$) away from $y=0$.
   - Verified that centered thin lens map follows half-drift $L/2$ $\to$ thin kick $\to$ half-drift $L/2$.

2. **Validation Script & Machine-Readable Output**:
   - Created `scripts/validate_task03_two_plane_tracking.py` executing 6 field configurations and a 7-point slice count convergence scan.
   - Generated 3 publication figure plots under `results/tracking_convergence/task03_run_<timestamp>/`:
     - `fig1_slice_convergence_angle.png` (Exit angle residuals $|\Delta x' - \Delta x'_{ref}|$, $|\Delta y' - \Delta y'_{ref}|$ vs $N_{\text{slices}}$)
     - `fig2_slice_convergence_position.png` (Exit position residuals $|x - x_{ref}|$, $|y - y_{ref}|$ vs $N_{\text{slices}}$)
     - `fig3_emittance_and_loss_convergence.png` (RMS beam sizes and geometric emittance stability vs $N_{\text{slices}}$)
   - Exported metrics JSON to `results/tracking_convergence/task03_run_<timestamp>/metrics.json`.

3. **Production Slice Count Justification**:
   - At $N_{\text{slices}} = 40$, exit angle residual relative to fine benchmark $N_{\text{slices}} = 320$ is $2.371 \times 10^{-5}\text{ mrad}$ ($2.371 \times 10^{-8}\text{ rad}$), well below the $10^{-4}\text{ mrad}$ tolerance while executing $8\times$ faster than fine tracking.

4. **Protected Files Safeguard**:
   - Verified via `git status` that all protected files remain untouched.

## 3. Protected Files Status

- `NKM_radia.ipynb`: Unchanged
- `NKM_radia_y=0.ipynb`: Unchanged
- `nlk.py`: Unchanged
- `storage_ring.ipynb`: Unchanged
- `By.txt`, `kickmap_file.txt`, `K4GSR_HBIv4-1.mat`, `nkm_field.xlsx`: Unchanged
- All protected scientific source data files verified untouched via `git status`.

## 4. Key Numerical Results

- **Symplectic vs RK4 Max Exit Angle Difference**: $3.856 \times 10^{-9}\text{ rad}$ (exact agreement between 2nd-order symplectic Verlet and 4th-order RK4 integrators).
- **$N_{\text{slices}}=40$ Exit Angle Residual (vs $N=320$)**: $2.371 \times 10^{-5}\text{ mrad}$ ($2.371 \times 10^{-8}\text{ rad}$).
- **Production Choice**: $N_{\text{slices}} = 40$ (Justified).
- **All Validation Checks**: **PASS** ($\text{True}$).
