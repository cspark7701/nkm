"""
Unit and Integration Tests for Milestone 6 BTS & NKM Error Modeling and Robustness
"""

import sys
from pathlib import Path
import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.nkm.bts_lattice import BTSConfig
from src.nkm.errors import (
    ErrorBudgetConfig,
    sample_error_ensemble,
    apply_sample_errors,
    evaluate_monte_carlo_robustness,
    compute_error_sensitivity_ranking
)


@pytest.fixture
def nominal_bts_config():
    return BTSConfig(
        k_q11=0.47419899, k_q12=-1.70822248, k_q13=1.33402498,
        k_q21=-1.05419705, k_q22=1.63861169, k_q23=-0.98192641,
        k_q31=1.08602944, k_q32=-1.67069631, k_q33=0.92706350
    )


@pytest.fixture
def target_twiss():
    return {
        'beta': [2.336495, 4.256241],
        'alpha': [-0.016335, 0.017772],
        'dispersion': [0.080868, 0.047472, 0.0, 0.0]
    }


def test_error_budget_config():
    """Test default error budget configuration values."""
    config = ErrorBudgetConfig()
    assert config.quad_k_rel_std == 1e-3
    assert config.quad_dx_std_m == 1e-4
    assert config.nkm_scale_std == 5e-3


def test_sample_error_ensemble_reproducibility():
    """Test reproducible Monte Carlo error sampling."""
    config = ErrorBudgetConfig()
    samples1 = sample_error_ensemble(config, n_samples=50, seed=42)
    samples2 = sample_error_ensemble(config, n_samples=50, seed=42)
    
    assert len(samples1) == 50
    assert samples1[0]["quad_k_err"] == samples2[0]["quad_k_err"]
    assert samples1[10]["booster_dx_m"] == samples2[10]["booster_dx_m"]


def test_apply_sample_errors(nominal_bts_config):
    """Test applying an error realization to an AT lattice."""
    samples = sample_error_ensemble(n_samples=5, seed=42)
    s = samples[0]
    lattice, init_twiss = apply_sample_errors(nominal_bts_config, s)
    
    assert len(lattice) > 0
    # Check that alignment and tilt vectors are set on quadrupoles
    q11 = [e for e in lattice if e.FamName == 'q11'][0]
    assert hasattr(q11, 'T1')
    assert hasattr(q11, 'R1')
    assert q11.T1.shape == (6,)
    assert q11.R1.shape == (6, 6)


def test_monte_carlo_robustness_execution(nominal_bts_config, target_twiss):
    """Test Monte Carlo robustness evaluator on a small ensemble."""
    res = evaluate_monte_carlo_robustness(nominal_bts_config, target_twiss, n_samples=20, seed=42)
    
    assert res["n_samples"] == 20
    assert res["feasible_fraction"] == 1.0
    assert "p50" in res["mismatch_x"]
    assert "p95" in res["mismatch_x"]
    assert res["mismatch_x"]["mean"] > 0.0
    assert res["mismatch_y"]["mean"] > 0.0
