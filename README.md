# NKM — Nonlinear Kicker Magnet & BTS Optimization

Repository for studying the Nonlinear Kicker Magnet (NKM), Booster-to-Storage Ring (BTS) transfer line optics matching, and off-axis beam injection into the storage ring.

## Key Objectives

1. **BTS Optical Matching**: Optimize quad strengths and transport parameters for target injection optics.
2. **NKM Field Integration**: Ingest and validate 3D/2D magnetic field maps from RADIA calculations.
3. **Nonlinear Kick Modeling**: Calculate realistic non-uniform kicks for injected and circulating beams.
4. **Beam Capture & Transmission**: Quantify injected-beam capture efficiency while minimizing stored-beam perturbation.
5. **Robustness & Tolerance Analysis**: Evaluate performance sensitivity against alignment, field map, energy, and quad errors.

---

## Primary Workflows

- **`bts.ipynb`**: Authoritative simulation notebook for BTS lattice setup, optics propagation, NKM field loading, and injection tracking.
- **`bts-moga.ipynb`**: Optional multi-objective genetic algorithm (MOGA) study. Must remain independently executable and non-blocking for `bts.ipynb`.

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

### Requirements

- Python 3.11+
- `accelerator-toolbox` (pyAT)
- `numpy`, `scipy`, `pandas`, `matplotlib`, `openpyxl`
- `pymoo` (optional, for MOGA)
- `jupyter` / `pytest`

### Quick Start

```bash
# Clone the repository
git clone https://github.com/cspark7701/nkm.git
cd nkm

# Install in editable mode
pip install -e .

# Verify protected input file hashes
python scripts/inventory_protected_hashes.py

# Record baseline metrics from bts.ipynb workflow
python scripts/record_baseline_metrics.py

# Run test suite
pytest
```

---

## Project Structure

```
nkm/
├── AGENTS.md                  # Project rules and protected file safeguards
├── README.md                  # Repository overview and setup
├── pyproject.toml             # Package metadata and dependencies
├── 00_nkm_refactor/           # Refactoring milestones and roadmap
├── src/nkm/                   # Reusable library modules
│   └── __init__.py
├── tests/                     # Unit and integration test suite
│   ├── __init__.py
│   └── test_baseline.py
├── scripts/                   # CLI scripts for hashes, baseline, optimization
│   ├── inventory_protected_hashes.py
│   └── record_baseline_metrics.py
├── results/                   # Generated results (separated from source data)
│   └── baseline/
├── docs/                      # Documentation and validation reports
│   └── validation/
└── bts.ipynb                  # Authoritative simulation notebook
```

---

## License & Attribution

Internal research project for NKM and BTS injection studies.
