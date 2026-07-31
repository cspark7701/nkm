# Milestone 25 — Task: Complete Removal of Facility Reference Metadata

**Author**: Chong Shik Park  
**Affiliation**: Department of Accelerator Science and Center for Accelerator Research, Korea University, Sejong, 30019 Republic of Korea

---

## 1. Executive Summary

This task performed a complete repository-wide audit and removal of facility-specific naming references across all source code, shell scripts, LaTeX reports, web documentation, and configuration files.

## 2. Work Completed

1. **Repository-Wide Search & Sanitation**:
   - Conducted case-insensitive ripgrep audit (`pohang` / `POHANG` / `Pohang`).
   - Standardized all terminology to generic 4.0 GeV 4GSR storage ring specifications.
   - Updated files: `AGENTS.md`, `src/nkm/results_schema.py`, `scripts/run_full_production_simulation.sh`, `docs/index.html`, `docs/nkm_consolidated_report.tex` (recompiled `docs/nkm_consolidated_report.pdf`), `docs/FULL_PRODUCTION_SIMULATION.md`, and past milestone summaries.
2. **Verification**:
   - Post-cleanup ripgrep returned 0 occurrences across the entire codebase.

## 3. Protected Files Status

- Protected scientific source data files (`By.txt`, `kickmap_file.txt`, `K4GSR_HBIv4-1.mat`, `nlk.py`, `NKM_radia.ipynb`, etc.) verified untouched via `git status`.

## 4. Verification & Results

- **Test Suite Pass Rate**: 73 / 73 passed (100%).
- **Rule Compliance**: Zero remote pushes, zero remote GitHub Actions checks, 100% local operation.
