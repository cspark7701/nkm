# Task 07 — MOGA Feasibility and Reproducibility Summary

## 1. Files Added
- `scripts/run_publication_moga.py`: Execution script for multi-seed NSGA-II Pareto optimization evaluating hypervolume convergence, feasible fractions, knee-point variability, and non-pickle JSON/CSV archival under `results/publication_moga/run_<timestamp>/`.
- `tests/test_moga_feasibility.py`: Unit test suite verifying strict feasibility enforcement, infeasible population fallback (`success=False`), true beam envelope-to-aperture margin calculations, and JSON/CSV archival.
- `docs/validation/nkm_moga_pareto.md`: Documentation deliverable covering NSGA-II MOGA objective and constraint formulations, feasibility rules, true envelope margin formulas, and multi-seed reproducibility.
- `docs/exec-plans/completed/15_moga_feasibility_reproducibility.md`: Task completion summary (saved with prefix `15_` per user directive).

## 2. Files Modified
- `src/nkm/moga.py`: Updated `BTSMOGAProblem`, `run_bts_moga`, and `save_moga_results_json` to enforce strict constraint feasibility ($CV \le 10^{-5}$), handle infeasible fallbacks, calculate hypervolume convergence histories, and compute true envelope-to-aperture clearance margins $M_{\text{ap}}$.
- `bts-moga.ipynb`: Revised notebook to incorporate updated `src.nkm.moga` workflow and non-pickle JSON/CSV result archival.

## 3. Protected Files Status
- `NKM_radia.ipynb`: Unchanged
- `NKM_radia_y=0.ipynb`: Unchanged
- `nlk.py`: Unchanged
- `storage_ring.ipynb`: Unchanged
- `*.xls`, `*.xlsx`, `*.xlsm`, `*.npy`, `*.npz`, `*.txt`: Unchanged
All protected files verified unmodified via `git status` and `git diff`.

## 4. Tests Run and Results
- `tests/test_moga_feasibility.py`: 4 passed (100%)
- `tests/test_error_model.py`: 4 passed (100%)
- `tests/test_publication_optimization.py`: 5 passed (100%)
- `tests/test_storage_ring_injection.py`: 2 passed (100%)
- `tests/test_nkm_integrators.py`: 3 passed (100%)
- `tests/test_nkm_cross_validation.py`: 5 passed (100%)
- `tests/test_units.py`: 6 passed (100%)
- `tests/test_fieldmap.py`: 9 passed (100%)
- `tests/test_injection.py`: 4 passed (100%)
- Overall test suite: **61 passed, 0 failed (100%)**.

## 5. Numerical Validation Results
- **Strict Feasibility**: Infeasible solutions are never labeled feasible. Infeasible runs return `success=False` with the top 5 least-infeasible candidates exported.
- **True Aperture Margin**: Peak beta surrogate replaced with physical envelope clearance $M_{\text{ap}} = r_{\text{pipe}} - (3\sqrt{\epsilon \beta} + |D_x \delta|)$.
- **Multi-Seed Reproducibility**: Tested across 5 independent random seeds ($42, 101, 202, 303, 404$) evaluating hypervolume convergence and knee-point variability.

## 6. Unresolved Scientific Issues
- None.

## 7. Acceptance Criteria
- [x] Infeasible solutions are never labeled feasible.
- [x] Infeasible runs export least-infeasible population and minimum constraint violation.
- [x] Peak beta surrogate replaced with true beam envelope-to-aperture margin.
- [x] Multi-seed Pareto front and hypervolume convergence evaluated.
- [x] Non-pickle JSON/CSV archival standards enforced.
- [x] Protected files remain unchanged.

## 8. Recommended Next Task
- Proceed to Task 08 (`08_data_driven_paper_pipeline.md`).
