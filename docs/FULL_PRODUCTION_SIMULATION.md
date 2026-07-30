# Full Production Simulation & Analysis Pipeline Guide

This guide documents the **Single-File Full Production Simulation & Analysis Pipeline** for the NKM and BTS Transfer Line framework at POHANG 4GSR.

The pipeline executes full physics simulations, numerical parameter scans, optics optimization, Monte Carlo tolerance budgeting, and multi-objective Pareto trade-off studies in a single, automated, reproducible run.

---

## 1. Primary Components & 1-to-1 Mapping

The full production simulation suite consists of two 1-to-1 matching entry points:

1. **Automated Shell Script**: [`scripts/run_full_production_simulation.sh`](file:///home/cspark/Work/projects/nkm/scripts/run_full_production_simulation.sh)
2. **Consolidated Jupyter Notebook**: [`notebooks/04_full_production_simulation.ipynb`](file:///home/cspark/Work/projects/nkm/notebooks/04_full_production_simulation.ipynb)

Both entry points execute the exact same 8 simulation steps in identical sequence using shared underlying Python modules in `src/nkm/`.

---

## 2. Command Line Usage & Options

### Running the Production Script

```bash
# Run with default settings (Verbose output, 90% CPU cores allocated)
./scripts/run_full_production_simulation.sh

# Run in QUIET mode (Ideal for LLM / AI agent prompts like Codex / Antigravity to prevent token consumption)
./scripts/run_full_production_simulation.sh --quiet

# Specify custom parallel worker cores and output directory
./scripts/run_full_production_simulation.sh --parallel 7 --output-dir results/my_custom_run
```

### Command Line Options

| Flag | Long Option | Default | Description |
| :--- | :--- | :--- | :--- |
| `-q` | `--quiet` | Off (`--verbose`) | Suppresses screen output and redirects all verbose stdout/stderr to a master log file under `results/production_run_<timestamp>/logs/production_run.log`. Recommended for background runs and AI agent turns. |
| `-v` | `--verbose` | On | Prints full real-time simulation step logs directly to terminal screen. |
| `-p` | `--parallel` | 90% Cores | Sets the number of parallel CPU worker processes ($N_{\text{workers}} = \max(1, \lfloor 0.9 \times N_{\text{cpu}} \rfloor)$). |
| `-o` | `--output-dir` | `results/production_run_<timestamp>` | Custom target directory for output artifacts. |
| `-h` | `--help` | — | Displays usage summary. |

---

## 3. Parallel Execution & CPU Core Scaling

The pipeline detects total system CPU cores via `os.cpu_count()` and defaults to **90% of available cores** (e.g., 7 cores on an 8-core system), leaving 10% for OS responsiveness:

- **Monte Carlo Tolerance Scan**: Distributes 500 seeds across $N_{\text{workers}}$ parallel workers using Python `multiprocessing`.
- **MOGA NSGA-II Evaluation**: Evaluates population generations across $N_{\text{workers}}$ concurrent worker processes.
- **Tracking Convergence**: Evaluates slicing integration steps concurrently.

---

## 4. Sequential 8-Step Pipeline Breakdown

1. **Step 1: Input Hash Cataloging & Baseline Metrics**: Verifies SHA-256 hashes of scientific source files (`By.txt`, `kickmap_file.txt`, `K4GSR_HBIv4-1.mat`).
2. **Step 2: Field & Kick Map Cross-Validation**: Fits 5th-order field polynomials and verifies 2D kickmap symmetry.
3. **Step 3: Symplectic Slicing Convergence**: Scans $N_{\text{slices}} \in \{5, 10, 20, 50, 100\}$ to confirm $< 10^{-6}\text{ rad}$ angular convergence.
4. **Step 4: Multi-Turn Storage Ring Tracking**: Simulates 1,000 particles across 1,000 turns over 4 kicker models with physical apertures.
5. **Step 5: SLSQP Quadrupole Optics Matching**: Optimizes 8 BTS quad families for target injection Twiss parameters ($\beta_x = 7.56\text{ m}, \beta_y = 12.27\text{ m}$).
6. **Step 6: Monte Carlo Tolerance Budget**: Simulates quad misalignments ($\sigma_{x,y}=100\,\mu\text{m}$), roll errors ($\sigma_\phi=0.5\text{ mrad}$), and gradient errors.
7. **Step 7: MOGA NSGA-II Pareto Optimization**: Generates multi-objective Pareto trade-off fronts between mismatch, beta peaks, and stay-clears.
8. **Step 8: Publication Data Consolidation**: Compiles final figures, metrics, LaTeX tables, and provenance logs into `results/production_run_<timestamp>/summary/`.

---

## 5. Structured Results Directory Layout

```text
results/production_run_<timestamp>/
├── logs/
│   └── production_run.log
├── fieldmap/
│   └── fieldmap_validation_metrics.json
├── convergence/
│   └── tracking_convergence_metrics.json
├── multiturn/
│   └── multiturn_injection_metrics.json
├── optimization/
│   └── bts_matching_metrics.json
├── tolerances/
│   └── tolerance_study_metrics.json
├── moga/
│   └── moga_pareto_results.json
└── summary/
    ├── paper_figures/
    └── paper_metrics_summary.json
```
