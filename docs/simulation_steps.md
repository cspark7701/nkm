# Step-by-Step Journal Paper Simulation Procedure

This document provides a clear, step-by-step guide to running all NKM and BTS simulation workflows, interactive notebooks, command-line scripts, automated regression tests, and publication artifact generators for journal paper writing.

---

## 1. Environment Verification & Data Integrity Check

Before running simulations, verify that your Python environment is active and that all scientific source input files match their authoritative SHA256 hashes.

```bash
# Step 1.1: Verify environment dependencies and editable installation
pip install -e .

# Step 1.2: Check protected input scientific data hashes
python scripts/inventory_protected_hashes.py
```

> **What this does**: Ensures `By.txt`, `kickmap_file.txt`, `nkm_field.xlsx`, and reference lattices are intact before generating paper results.

---

## 2. Interactive Notebook Workflows

The repository contains two primary Jupyter Notebooks depending on your paper scope:

### A. Authoritative Simulation Notebook — [`bts.ipynb`](file:///home/cspark/Work/projects/nkm/bts.ipynb)
- **Role**: Primary workflow notebook for the main text of the journal paper.
- **What it executes**:
  1. **BTS Lattice Construction**: Builds the 36-element transport line in Accelerator Toolbox (pyAT).
  2. **Baseline Optics Propagation**: Computes initial Twiss functions $\beta_x(s), \beta_y(s), D_x(s)$.
  3. **RADIA Field Map Ingestion**: Loads 1D $B_y(z)$ profile and 2D integrated kick map $\Delta x'(x,y)$.
  4. **Single-Objective Optimization**: Matches BTS exit optics to storage ring target ($\beta_x=2.34\text{ m}, \beta_y=4.26\text{ m}$) while constraining peak $\beta \le 60\text{ m}$.
  5. **6D Beam Injection Tracking**: Tracks $10,000$ particles through thin-kick and RK4 integration models to measure beam transmission and stored beam perturbation.
  6. **Error Budget Analysis**: Evaluates sensitivity against quadrupole misalignments ($\pm 100\,\mu\text{m}$), gradient errors ($0.1\%$), and roll tilts ($0.5\text{ mrad}$).

```bash
# Launch Jupyter Lab / Notebook to run bts.ipynb interactively:
jupyter lab bts.ipynb
```

---

### B. Optional Multi-Objective Notebook — [`bts-moga.ipynb`](file:///home/cspark/Work/projects/nkm/bts-moga.ipynb)
- **Role**: Optional MOGA Pareto study notebook for trade-off analysis sections.
- **What it executes**:
  1. Runs NSGA-II multi-objective genetic algorithm over 9 BTS quadrupole strengths.
  2. Evaluates Pareto trade-offs between exit mismatch ($\mathcal{M}_x + \mathcal{M}_y$), peak beta function ($\beta_{\max}$), and residual dispersion ($D_x, D_x'$).
  3. Plots 2D/3D Pareto fronts, parallel coordinates, and convergence histories.

```bash
# Launch optional MOGA notebook:
jupyter lab bts-moga.ipynb
```

---

## 3. Step-by-Step Python Command-Line Pipeline

If you prefer batch execution via Python scripts, follow this chronological sequence. Each step saves structured data and figures into the `results/` directory:

```bash
# Step 3.1: Record baseline unoptimized metrics
python scripts/record_baseline_metrics.py
# Output: results/baseline/baseline_summary_metrics.json

# Step 3.2: Validate BTS lattice geometry & linear Twiss propagation
python scripts/validate_bts_optics.py
# Output: results/optics_validation/bts_twiss_propagation.png

# Step 3.3: Validate RADIA 1D/2D magnetic field map & symmetry
python scripts/validate_nkm_fieldmap.py
# Output: results/fieldmap/fieldmap_validation_metrics.json

# Step 3.4: Run SLSQP optics matching & Jacobian sensitivity matrix
python scripts/optimize_bts.py --method SLSQP
# Output: results/bts_optimization/bts_optimized_optics.png

# Step 3.5: Run 6D particle injection tracking & stored beam kick evaluation
python scripts/validate_nkm_injection.py --particles 10000
# Output: results/injection/nkm_injection_phasespace.png

# Step 3.6: Run Monte Carlo error budget study (200 random seeds)
python scripts/run_tolerance_study.py --n-samples 200
# Output: results/tolerances/monte_carlo_mismatch.png

# Step 3.7: Run NSGA-II MOGA Pareto optimization (pop=40, gen=30)
python scripts/run_bts_moga.py --pop-size 40 --n-gen 30 --seed 42
# Output: results/moga/moga_pareto_front_2d.png
```

---

## 4. One-Command Paper Artifact Generation

For paper writing, you can generate **all LaTeX tables (`.tex`)**, **Markdown tables (`.md`)**, **300 DPI publication figures (`.png` & `.pdf`)**, and **machine-readable JSON metrics** with a single command:

```bash
python scripts/reproduce_paper.py
```

### Generated Paper Deliverables Summary (`results/paper/`):

#### 📄 LaTeX & Markdown Tables ([`results/paper/tables/`](file:///home/cspark/Work/projects/nkm/results/paper/tables/))
- **`table1_bts_parameters.tex` / `.md`**: BTS line parameters, energy, emittances, and target Twiss parameters.
- **`table2_quad_strengths.tex` / `.md`**: Quadrupole strengths $K_1 \dots K_9$ comparison (Baseline vs SLSQP vs MOGA Knee-Point).
- **`table3_optics_comparison.tex` / `.md`**: Optics metrics ($\mathcal{M}_x, \mathcal{M}_y$, peak $\beta_x, \beta_y$, exit $D_x, D_x'$).

#### 🖼️ Publication Figures ([`results/paper/figures/`](file:///home/cspark/Work/projects/nkm/results/paper/figures/))
- **`fig1_bts_optics_comparison.png` / `.pdf`**: $\beta_x(s), \beta_y(s), D_x(s)$ optics functions along the BTS line.
- **`fig2_beam_envelopes_apertures.png` / `.pdf`**: Transverse $3\sigma$ beam envelopes vs physical vacuum chamber apertures.
- **`fig3_nkm_fieldmap_kick.png` / `.pdf`**: RADIA 2D integrated deflection profile $\Delta x'(x, y=0)$.

#### 📊 Summary Metrics
- **`paper_summary_metrics.json`**: Key numerical values, ratio improvements, and statistical confidence bounds.

---

## 5. Paper Regression & Automated Testing

To ensure all numbers in your manuscript are strictly reproducible and pass physics checks, run the automated test suite:

```bash
# Run all 41 unit, integration, and paper regression tests
pytest

# Or run paper-specific regression tests specifically
pytest tests/test_paper_regression.py
```

---

## 6. Paper Documentation References

You can consult the pre-compiled Markdown reports for direct copy-pasting of text, tables, and references:
- **Paper Results & LaTeX Snippets**: [`docs/paper_results.md`](file:///home/cspark/Work/projects/nkm/docs/paper_results.md)
- **Reproducibility Guide**: [`docs/reproducibility.md`](file:///home/cspark/Work/projects/nkm/docs/reproducibility.md)
- **MOGA Optimization Report**: [`docs/validation/moga_pareto_optimization.md`](file:///home/cspark/Work/projects/nkm/docs/validation/moga_pareto_optimization.md)
