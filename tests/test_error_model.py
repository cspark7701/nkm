"""
Unit tests for NKM error model and robust optimization (Task 06)
"""

import sys
from pathlib import Path
import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.nkm.errors import ErrorBudgetConfig, sample_error_ensemble, apply_sample_errors
from src.nkm.robust_optimization import evaluate_robustness_statistics, compute_one_at_a_time_sensitivity
from src.nkm.bts_lattice import BTSConfig


def test_ensemble_reproducibility():
    config = ErrorBudgetConfig()
    s1 = sample_error_ensemble(config, n_samples=50, seed=42)
    s2 = sample_error_ensemble(config, n_samples=50, seed=42)

    assert len(s1) == 50
    assert s1[0]["quad_k_err"] == s2[0]["quad_k_err"]
    assert s1[0]["energy_dp_p"] == s2[0]["energy_dp_p"]


def test_energy_rigidity_scaling():
    nominal = BTSConfig(energy_eV=4.0e9)
    sample = {
        "sample_id": 0,
        "quad_k_err": [0.0]*9,
        "quad_dx_m": [0.0]*9,
        "quad_dy_m": [0.0]*9,
        "quad_roll_rad": [0.0]*9,
        "quad_ds_m": [0.0]*9,
        "booster_x_m": 0.0,
        "booster_xp_rad": 0.0,
        "energy_dp_p": 0.01,  # 1% energy shift
        "beta_mismatch_x": 0.0,
        "beta_mismatch_y": 0.0,
        "nkm_scale_err": 0.0,
        "nkm_dx_m": 0.0,
        "ring_co_x_m": 0.0,
        "septum_x_m": 0.0,
    }

    lat, twiss = apply_sample_errors(nominal, sample)
    assert lat.energy == pytest.approx(4.0e9 * 1.01)
    # Dispersion uncorrupted by centroid jitter
    assert twiss["dispersion"][0] == 0.276200


def test_robustness_statistics():
    nominal = BTSConfig()
    target_twiss = {"beta": [2.336, 4.256], "alpha": [-0.016, 0.017]}
    samples = sample_error_ensemble(n_samples=20, seed=42)

    stats = evaluate_robustness_statistics(nominal, target_twiss, samples)

    assert "mismatch_x" in stats
    assert "p50_median" in stats["mismatch_x"]
    assert "p95" in stats["mismatch_x"]
    assert "bootstrap_95ci_median" in stats["mismatch_x"]
    assert stats["failure_probability"] >= 0.0


def test_oat_sensitivity_ranking():
    nominal = BTSConfig()
    target_twiss = {"beta": [2.336, 4.256], "alpha": [-0.016, 0.017]}

    rankings = compute_one_at_a_time_sensitivity(nominal, target_twiss, n_samples=20, seed=42)

    assert len(rankings) > 0
    # Values should be ordered descending
    vals = list(rankings.values())
    assert vals == sorted(vals, reverse=True)
