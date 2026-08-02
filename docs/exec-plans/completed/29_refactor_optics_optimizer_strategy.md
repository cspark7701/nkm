# Milestone 29 — Refactor #3: Optics Optimizer Strategy Pattern (`OpticsOptimizer`)

**Author**: Chong Shik Park  
**Affiliation**: Department of Accelerator Science and Center for Accelerator Research, Korea University, Sejong, 30019 Republic of Korea

---

## 1. Executive Summary

This refactoring milestone implemented the **Optics Optimizer Strategy Pattern** across `src/nkm/optimization.py` and `src/nkm/robust_optimization.py`. The abstract strategy interface `BaseOpticsObjective` decouples objective evaluation strategies (`DeterministicObjective`, `RobustMonteCarloObjective`) from optimization execution algorithms in `OpticsOptimizer`, eliminating duplicate quadrupole bound checking and Twiss propagation logic.

## 2. Work Completed

1. **Strategy Interface & Objective Classes (`src/nkm/optimization.py` & `src/nkm/robust_optimization.py`)**:
   - Implemented `BaseOpticsObjective` abstract base class defining `evaluate()`, `compute_residual_vector()`, and `compute_scalar_merit()`.
   - Refactored `DeterministicObjective` (with `BTSOptimizationEvaluator` as backward-compatible alias) for deterministic single-seed optics matching.
   - Implemented `RobustMonteCarloObjective` in `src/nkm/robust_optimization.py` for Monte Carlo error ensemble objective evaluation.

2. **Unified Optimizer Engine (`src/nkm/optimization.py`)**:
   - Implemented `OpticsOptimizer` class managing quadrupole hardware bounds (`quad_bounds`), algorithm selection (`least_squares`, `SLSQP`, `Nelder-Mead`), multi-start global search (`n_starts`), and result packaging (`BTSOptimizationResult`).
   - Refactored `optimize_bts_quadrupoles()` to delegate to `OpticsOptimizer` using `DeterministicObjective` strategy, preserving 100% backward compatibility for all existing scripts and tests.
   - Exported strategy classes in package root `src/nkm/__init__.py`.

3. **Unit Tests & Integration Validation (`tests/test_optimization.py`)**:
   - Added `test_optics_optimizer_strategy_pattern` verifying `OpticsOptimizer` execution with both `DeterministicObjective` and `RobustMonteCarloObjective` strategies.
   - Verified 5/5 tests passing in `tests/test_optimization.py`.

## 3. Protected Files Status

- `NKM_radia.ipynb`: Unchanged
- `NKM_radia_y=0.ipynb`: Unchanged
- `nlk.py`: Unchanged
- `storage_ring.ipynb`: Unchanged
- `By.txt`, `kickmap_file.txt`, `K4GSR_HBIv4-1.mat`, `nkm_field.xlsx`: Unchanged
- All protected scientific data files verified untouched via `git status`.

## 4. Verification & Results

- **`test_optimization.py` Pass Rate**: 5 / 5 passed (100%).
- **Backward Compatibility**: 100% non-breaking API compatibility across all optimization callers.
- **Rule Compliance**: Zero remote pushes, zero remote GitHub Actions checks, 100% local operation.
