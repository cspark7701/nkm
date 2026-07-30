# Milestone 21 — Task 04: Full Production Simulation Script, Parity Notebook, & Documentation

**Author**: Chong Shik Park  
**Affiliation**: Department of Accelerator Science and Center for Accelerator Research, Korea University, Sejong, 30019 Republic of Korea

---

## 1. Executive Summary

Task 04 delivered the unified **Single-File Full Production Simulation & Analysis Pipeline** for the NKM and BTS transfer line at POHANG 4GSR. The pipeline consists of an automated shell script (`scripts/run_full_production_simulation.sh`), a 1-to-1 parity Jupyter notebook (`notebooks/04_full_production_simulation.ipynb`), and comprehensive documentation (`docs/FULL_PRODUCTION_SIMULATION.md`).

Per user instructions ("Continue to Task04. But do not run full production simulation dry run yet."), all script, notebook, and documentation assets have been constructed, validated for syntax and layout, and held ready for execution without running the actual long production simulation.

## 2. Work Completed

1. **Automated Shell Script (`scripts/run_full_production_simulation.sh`)**:
   - Single shell script executing full production parameter scanning and analysis.
   - **Parallel CPU Core Allocation**: Automatically detects host CPU core count (`os.cpu_count()`) and defaults to 90% utilization ($N_{\text{workers}} = \max(1, \lfloor 0.9 \times N_{\text{cpu}} \rfloor)$), configurable via `--parallel N`.
   - **Verbosity Flag**: Includes `--quiet` / `-q` option to suppress screen stdout and log directly to file (saving tokens during AI turn interactions), and `--verbose` / `-v` for real-time console logging.
   - **Structured Step Logging**: 8 sequential simulation steps (Input cataloging, Fieldmap cross-validation, Symplectic slicing convergence, Multi-turn tracking, SLSQP BTS optics matching, Monte Carlo tolerance budgeting, MOGA NSGA-II Pareto optimization, and Publication data consolidation).
   - **Isolated Output Folders**: Saves results cleanly into timestamped directories (`results/production_run_<timestamp>/`).

2. **Parity Jupyter Notebook (`notebooks/04_full_production_simulation.ipynb`)**:
   - 1-to-1 match with the shell script across all 8 simulation and analysis steps.
   - Includes detailed markdown descriptions, parameter scan setups, inline visualization cells, and isolated results directory management.

3. **Pipeline Documentation (`docs/FULL_PRODUCTION_SIMULATION.md`)**:
   - Outlines pipeline architecture, command-line arguments, CPU core scaling logic, 8-step execution flow, and output directory structure.

## 3. Protected Files Status

- All protected source files (`NKM_radia.ipynb`, `By.txt`, `kickmap_file.txt`, `K4GSR_HBIv4-1.mat`, etc.) verified unchanged.

## 4. Verification & Results

- `scripts/run_full_production_simulation.sh` validated with bash syntax check (`bash -n`).
- `notebooks/04_full_production_simulation.ipynb` validated for nbformat 4 JSON schema compliance.
- Dry run / production simulation execution held pending user invocation signal.
