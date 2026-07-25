# NKM — Nonlinear Kicker Magnet & BTS Optimization

Repository for studying the Nonlinear Kicker Magnet (NKM), Booster-to-Storage Ring (BTS) transfer line optics matching, off-axis beam injection, and reproducible publication generation.

> **Comprehensive Guide**: See [docs/SIMULATION_PROCEDURE_AND_PUBLICATION_WORKFLOW.md](file:///home/cspark/Work/projects/nkm/docs/SIMULATION_PROCEDURE_AND_PUBLICATION_WORKFLOW.md) for the single-file complete specification of the simulation procedure and paper reproduction pipeline.

---

## Key Objectives

1. **BTS Optical Matching**: Optimize quad strengths and transport parameters for target injection optics.
2. **NKM Field Integration**: Ingest and validate 3D/2D magnetic field maps from RADIA calculations.
3. **Nonlinear Kick Modeling**: Calculate realistic non-uniform kicks for injected and circulating beams.
4. **Beam Capture & Transmission**: Quantify injected-beam capture efficiency while minimizing stored-beam perturbation.
5. **Robustness & Tolerance Analysis**: Evaluate performance sensitivity against alignment, field map, energy, and quad errors.
6. **Data-Driven Reproduction**: Dynamically generate publication figures and tables without hard-coded numbers.

---

## Primary Workflows & Scripts

- **Authoritative Simulation Notebook**: `bts.ipynb`
- **Optional MOGA Pareto Notebook**: `bts-moga.ipynb`
- **Single-Command Paper Reproduction**: `python3 scripts/reproduce_paper.py`

| Workflow Phase | Script Command | Description |
| :--- | :--- | :--- |
| **Field Validation** | `python3 scripts/validate_nkm_kick.py` | 5-way field/kick cross-validation. |
| **Tracking Convergence** | `python3 scripts/run_tracking_convergence.py` | $N_{\text{slices}}$ thick symplectic tracking convergence. |
| **Multi-Turn Injection** | `python3 scripts/run_multiturn_injection.py` | Turn-by-turn capture efficiency & kicker models. |
| **Deterministic Opt** | `python3 scripts/optimize_bts_publication.py` | 2-stage SLSQP quad matching & SVD Jacobian analysis. |
| **Tolerance Budget** | `python3 scripts/run_publication_tolerances.py` | Monte Carlo robustness & OAT sensitivity rankings. |
| **MOGA Trade-offs** | `python3 scripts/run_publication_moga.py` | Multi-seed NSGA-II Pareto optimization. |
| **Paper Reproduction** | `python3 scripts/reproduce_paper.py` | Fully data-driven figure and table compilation. |

---

## Protected Scientific Source Data

The following source data and reference files are **immutable** and must not be reformatted, renamed, or modified:

- `NKM_radia.ipynb`, `NKM_radia_y=0.ipynb`
- `nlk.py`, `storage_ring.ipynb`
- Spreadsheet data (`*.xls`, `*.xlsx`, `*.xlsm`)
- Binary array data (`*.npy`, `*.npz`)
- Reference text files (`*.txt`)

All generated simulation outputs are saved under the `results/` directory.

---

## Installation & Setup

```bash
# Clone the repository
git clone https://github.com/cspark7701/nkm.git
cd nkm

# Install locked dependencies and package
pip install -r requirements-lock.txt
pip install -e .[dev,moga]

# Run single-command paper pipeline
python3 scripts/reproduce_paper.py

# Run test suite (68 tests)
pytest -v
```

---

## License & Citation

- **License**: [MIT License](file:///home/cspark/Work/projects/nkm/LICENSE)
- **Citation**: See [`CITATION.cff`](file:///home/cspark/Work/projects/nkm/CITATION.cff)
