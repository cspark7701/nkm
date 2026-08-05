# Milestone 35 — Task 04: Implement Element-Resolved Aperture and Septum Losses

**Author**: Chong Shik Park  
**Affiliation**: Department of Accelerator Science and Center for Accelerator Research, Korea University, Sejong, 30019 Republic of Korea

---

## 1. Executive Summary

This milestone completed **Task 04 — Implement Element-Resolved Aperture and Septum Losses**. It replaced crude end-of-turn global coordinate clipping with element-by-element physical loss detection (`track_element_resolved_injection` in `src/nkm/storage_ring_injection.py`). It introduced `SeptumModel` and `ElementAperture` dataclasses, recording the exact particle index, turn number, element index, element name, longitudinal $s$-coordinate, cause of loss (`"aperture_x_exceeded"`, `"aperture_y_exceeded"`, `"septum_collision"`), and transverse coordinates $(x, y)$ at the precise moment of loss.

## 2. Work Completed

1. **Element-Resolved Tracking Engine (`src/nkm/storage_ring_injection.py`)**:
   - Implemented `SeptumModel` (septum sheet inner edge $x_{\text{septum}}$, blade thickness $t_{\text{septum}}$, allowed beam side).
   - Implemented `ElementAperture` ($x_{\text{min}}, x_{\text{max}}, y_{\text{min}}, y_{\text{max}}$).
   - Implemented `track_element_resolved_injection()` tracking turn-by-turn and element-by-element, recording detailed loss logs in `TrackingResult.loss_log`.
   - Exported `SeptumModel`, `ElementAperture`, and `track_element_resolved_injection` in package root `src/nkm/__init__.py`.

2. **Validation Script & Machine-Readable Output**:
   - Created `scripts/validate_task04_aperture_septum_losses.py` testing 4 controlled test cases:
     - Case 1 (No Aperture): 100% of particles survive ($0\%$ loss).
     - Case 2 (Tight Element Aperture): Particles exceeding aperture at specific element #2 (`DR_02`) are lost AT element #2 on turn 1.
     - Case 3 (Septum Blocking): Septum placed across beam path ($x_{\text{septum}} = 0$) blocks particles with cause `"septum_collision"`.
     - Case 4 (Full Storage Ring Run): Stored beam with safe septum clearance maintains $100\%$ survival over 5 turns.
   - Generated 3 publication figure plots under `results/loss_validation/task04_run_<timestamp>/`:
     - `fig1_loss_location_histogram.png` (Losses vs element $s$-position)
     - `fig2_loss_by_cause_pie.png` (Breakdown of loss mechanisms: aperture vs septum)
     - `fig3_septum_clearance_diagram.png` (Transverse beam profile relative to septum boundary)
   - Exported metrics JSON to `results/loss_validation/task04_run_<timestamp>/metrics.json`.

3. **Unit Test Suite Integration**:
   - Added `tests/test_apertures_and_septum.py` verifying septum collision bounds, element aperture checks, and exact element loss logging (3/3 passed).

4. **Protected Files Status**:
   - All protected scientific source files remain untouched.

## 3. Protected Files Status

- `NKM_radia.ipynb`: Unchanged
- `NKM_radia_y=0.ipynb`: Unchanged
- `nlk.py`: Unchanged
- `storage_ring.ipynb`: Unchanged
- `By.txt`, `kickmap_file.txt`, `K4GSR_HBIv4-1.mat`, `nkm_field.xlsx`: Unchanged
- All protected scientific source data files verified untouched via `git status`.

## 4. Key Numerical Results

- **Case 1 (No Aperture)**: Survival fraction = $1.00$ ($100\%$)
- **Case 2 (Tight Element Aperture at DR_02)**: First loss element index = 2 (`DR_02`, $s = 2.5\text{ m}$), cause = `"aperture_x_exceeded"`
- **Case 3 (Septum Blocking at x=0)**: Septum collisions recorded = 50 particles ($50\%$ blocked)
- **Case 4 (Full Storage Ring Safe Clear)**: Stored beam survival fraction = $1.00$ ($100\%$)
- **All Validation Checks**: **PASS** ($\text{True}$).
