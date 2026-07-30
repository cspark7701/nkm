#!/usr/bin/env bash
# ==============================================================================
# NKM Environment Setup & Verification Script
# Targets a new user or fresh machine setup for the NKM simulation repository.
# ==============================================================================
set -e

REPO_URL="https://github.com/cspark7701/nkm.git"
TARGET_DIR="nkm"

echo "======================================================================"
echo "          NKM Simulation Repository — Environment Setup               "
echo "======================================================================"

# 1. Clone repository if not inside repo root
if [ ! -f "pyproject.toml" ]; then
    if [ ! -d "$TARGET_DIR" ]; then
        echo "[1/4] Cloning repository from $REPO_URL ..."
        git clone "$REPO_URL" "$TARGET_DIR"
        cd "$TARGET_DIR"
    else
        echo "[1/4] Entering existing directory $TARGET_DIR ..."
        cd "$TARGET_DIR"
    fi
else
    echo "[1/4] Already inside NKM repository root."
fi

# 2. Set up Python virtual environment (venv or conda)
ENV_DIR="venv"
if command -v conda &> /dev/null && [ -z "$VIRTUAL_ENV" ]; then
    echo "[2/4] Setting up Conda environment (nkm-env)..."
    eval "$(conda shell.bash hook)"
    if conda env list | grep -q "nkm-env"; then
        echo "  Activating existing nkm-env environment..."
        conda activate nkm-env
        if ! python3 -m pip --version &> /dev/null; then
            echo "  Installing pip into nkm-env..."
            conda install -y pip -n nkm-env
        fi
    else
        echo "  Creating new nkm-env Conda environment (Python 3.11 with pip)..."
        conda create -n nkm-env python=3.11 pip -y
        conda activate nkm-env
    fi
elif [ ! -d "$ENV_DIR" ]; then
    echo "[2/4] Creating Python virtual environment in $ENV_DIR..."
    python3 -m venv "$ENV_DIR"
    source "$ENV_DIR/bin/activate"
else
    echo "[2/4] Activating existing virtual environment ($ENV_DIR)..."
    source "$ENV_DIR/bin/activate"
fi

# 3. Install packages
echo "[3/4] Installing dependencies and package in editable mode..."
python3 -m pip install --upgrade pip
if [ -f "requirements-lock.txt" ]; then
    pip install -r requirements-lock.txt
fi
pip install -e .[dev,moga]

# 4. Verify installation via pytest
echo "[4/4] Running pytest suite to verify setup..."
pytest -v

echo "======================================================================"
echo " Setup & Verification Successful!                                    "
echo " You can now run:                                                      "
echo "   python3 scripts/reproduce_paper.py                                 "
echo "======================================================================"
