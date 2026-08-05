# Milestone 36 — Task 05: Couple Optimized BTS Output to Storage-Ring Injection

**Author**: Chong Shik Park  
**Affiliation**: Department of Accelerator Science and Center for Accelerator Research, Korea University, Sejong, 30019 Republic of Korea

---

## 1. Executive Summary

This milestone completed **Task 05 — Couple Optimized BTS Output to Storage-Ring Injection**. It established a fully coupled, end-to-end simulation chain connecting canonical booster extraction particle distributions through the BTS transport line to storage-ring multi-turn injection tracking (`run_end_to_end_pipeline` in `src/nkm/end_to_end.py`). Instead of relying solely on local Twiss parameters, actual BTS exit 6D particle coordinates are passed directly into storage-ring element-resolved tracking, preserving nonlinear correlations, energy spread ($\delta$), transverse offsets, and particle loss accounts.

## 2. Work Completed

1. **End-to-End Tracking Engine (`src/nkm/end_to_end.py`)**:
   - Implemented `BoosterExtractionConfig` and `generate_booster_extraction_distribution()`.
   - Implemented `run_end_to_end_pipeline()` performing Booster extraction $\to$ BTS tracking $\to$ coordinate handoff $\to$ Storage Ring element-resolved multi-turn tracking.
   - Exported end-to-end utilities in package root `src/nkm/__init__.py`.

2. **Validation Script & Machine-Readable Handoff Artifacts**:
   - Created `scripts/validate_task05_end_to_end_coupling.py` generating machine-readable result files under `results/end_to_end/task05_run_<timestamp>/`:
     - `config.yaml` (Full simulation configuration)
     - `bts_exit_distribution.npz` (Compressed 6D particle distribution arrays at BTS exit $s = 28.5\text{ m}$)
     - `bts_metrics.json` (BTS line transmission & beam sizes)
     - `injection_metrics.json` (Storage-ring capture efficiency & losses comparison)
     - `handoff_validation.json` (Documented coordinate conventions, units, and handoff validity)
   - Generated 3 publication figure plots under `results/end_to_end/task05_run_<timestamp>/figures/`:
     - `fig1_bts_phase_space_handoff.png` (BTS exit phase space $x$-$x'$)
     - `fig2_multiturn_survival_comparison.png` (Turn-by-turn particle survival: Baseline vs Optimized vs Local Twiss)
     - `fig3_storage_ring_phase_space_turns.png` (Captured beam phase space distribution at Turn 10)

3. **Unit Test Suite Integration**:
   - Added `tests/test_end_to_end.py` verifying booster extraction beam generation and end-to-end pipeline execution (2/2 passed).

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

- **Booster Extraction Particle Count**: 1000 particles
- **BTS Baseline Transmission**: $100.00\%$ ($0$ losses through BTS)
- **BTS Optimized Transmission**: $100.00\%$ ($0$ losses through BTS)
- **Storage Ring Capture (Baseline BTS Handoff)**: $100.00\%$
- **Storage Ring Capture (Optimized BTS Handoff)**: $100.00\%$
- **Overall End-to-End Efficiency**: $100.00\%$
- **All Validation Checks**: **PASS** ($\text{True}$).
