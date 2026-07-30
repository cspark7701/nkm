# NKM Installation & Environment Setup Guide

This guide provides step-by-step instructions for setting up the **Nonlinear Kicker Magnet (NKM) & BTS Simulation Framework** on a new machine or for a new user.

---

## Prerequisites

- **Operating System**: Linux (Ubuntu 20.04+ recommended) or macOS
- **Git**: Installed and configured (`git --version`)
- **Python**: Version 3.9 to 3.11 (`python3 --version`)
- **Conda / Miniforge** *(Recommended)* OR **Python `venv`**

---

## Quick Start (Automated 1-Command Setup)

To clone, set up the Python environment, install all dependencies, and run verification tests automatically:

```bash
bash <(curl -s https://raw.githubusercontent.com/cspark7701/nkm/main/scripts/setup_environment.sh)
```

Or from an existing clone:

```bash
./scripts/setup_environment.sh
```

---

## Manual Installation Step-by-Step

### Step 1: Git Clone the Repository

```bash
git clone https://github.com/cspark7701/nkm.git
cd nkm
```

---

### Step 2: Set Up the Python Environment

#### Option A: Using Conda (Recommended)

```bash
# Create a dedicated Conda environment with Python 3.11
conda create -n nkm-env python=3.11 -y
conda activate nkm-env
```

Or using `environment.yml`:

```bash
conda env create -f environment.yml
conda activate nkm-env
```

#### Option B: Using Python `venv`

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### Step 3: Install Package & Dependencies

Upgrade `pip` and install the exact pinned scientific dependencies locked in `requirements-lock.txt`, followed by the `nkm` package in editable mode:

```bash
# Upgrade pip
python3 -m pip install --upgrade pip

# Install locked dependencies
pip install -r requirements-lock.txt

# Install nkm package with development & MOGA optional extras
pip install -e .[dev,moga]
```

---

### Step 4: Verify Installation with Pytest

Run the test suite to verify that all modules, lattice loaders, field maps, and physics algorithms work correctly on your system:

```bash
pytest -v
```

Expected output:
```text
73 passed in ~3 minutes
```

> **Note**: Missing simulation output files (such as `storage_ring_lattice_nkm.mat`) are automatically resurrected from the protected source data (`K4GSR_HBIv4-1.mat`) upon running `pytest` or loading the lattice for the first time.

---

## Next Steps

After a successful installation:

1. **Run Paper Pipeline**:
   ```bash
   python3 scripts/reproduce_paper.py
   ```
2. **Run Main Simulation Notebook**:
   ```bash
   jupyter notebook notebooks/01_bts_main_simulation.ipynb
   ```
