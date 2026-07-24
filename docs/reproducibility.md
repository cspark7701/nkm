# Repository Reproducibility Guide

This document provides step-by-step instructions to verify protected input scientific source data, execute the full simulation pipeline, run automated regression tests, and regenerate every figure and table for publication from a clean environment.

---

## 1. System Requirements & Environment Setup

### Environment Dependencies:
- **OS**: Linux / macOS / Windows
- **Python**: 3.11+
- **Key Packages**: `accelerator-toolbox` (pyAT), `numpy`, `scipy`, `pandas`, `matplotlib`, `openpyxl`, `pymoo`, `pytest`

### Quick Environment Installation:
```bash
# Clone the repository
git clone https://github.com/cspark7701/nkm.git
cd nkm

# Install package in editable mode
pip install -e .
```

---

## 2. Protected Input File Integrity Verification

To ensure scientific source data files have not been corrupted, reformatted, or accidentally altered, run the automated hash inventory check:

```bash
python scripts/inventory_protected_hashes.py
```

Expected Output:
```
================================================================================
          NKM IMMUTABLE PROTECTED FILE HASH INVENTORY CHECK
================================================================================
Status: ALL PROTECTED INPUT FILES MATCH AUTHORITATIVE HASHES.
```

---

## 3. One-Command Paper Results & Artifact Reproduction

To regenerate all LaTeX tables (`.tex`), Markdown tables (`.md`), publication figures (`.png` and `.pdf`), and paper summary metrics into `results/paper/`:

```bash
python scripts/reproduce_paper.py
```

Generated Outputs Location:
- **LaTeX & Markdown Tables**: `results/paper/tables/`
  - `table1_bts_parameters.tex` / `.md`
  - `table2_quad_strengths.tex` / `.md`
  - `table3_optics_comparison.tex` / `.md`
- **Publication Figures (300 DPI & Vector PDF)**: `results/paper/figures/`
  - `fig1_bts_optics_comparison.png` / `.pdf`
  - `fig2_beam_envelopes_apertures.png` / `.pdf`
  - `fig3_nkm_fieldmap_kick.png` / `.pdf`
- **Machine-Readable Summary**: `results/paper/paper_summary_metrics.json`

---

## 4. Running the Automated Test Suite

To run the complete unit, integration, and paper regression test suite:

```bash
# Run all unit, integration, and paper regression tests
pytest

# Run paper regression tests specifically
pytest tests/test_paper_regression.py
```

Expected Test Results:
- `37 passed` across all test modules in `tests/`.

---

## 5. Summary of Primary Simulation Workflows

| Script / Notebook | Purpose | Deliverable / Output |
| :--- | :--- | :--- |
| `bts.ipynb` | Primary authoritative simulation notebook | End-to-end BTS setup & NKM tracking |
| `bts-moga.ipynb` | Optional MOGA Pareto optimization notebook | Multi-objective trade-off analysis |
| `scripts/record_baseline_metrics.py` | Baseline lattice verification | `results/baseline/` metrics |
| `scripts/validate_bts_optics.py` | BTS Twiss propagation & optics validation | `results/optics_validation/` |
| `scripts/validate_nkm_fieldmap.py` | RADIA 1D/2D field map verification | `results/fieldmap/` |
| `scripts/optimize_bts.py` | SLSQP & global quad optimization | `results/bts_optimization/` |
| `scripts/validate_nkm_injection.py` | 6D beam injection & kickmap tracking | `results/injection/` |
| `scripts/run_tolerance_study.py` | Monte Carlo error & robustness study | `results/tolerances/` |
| `scripts/run_bts_moga.py` | NSGA-II Pareto optimization execution | `results/moga/` |
| `scripts/reproduce_paper.py` | Full publication artifact regeneration | `results/paper/` |
