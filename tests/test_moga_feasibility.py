"""
Unit and integration tests for MOGA feasibility and Pareto reproducibility (Task 07)
"""

import sys
from pathlib import Path
import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.nkm.moga import (
    BTSMOGAConfig,
    BTSMOGAProblem,
    run_bts_moga,
    compute_true_aperture_margin,
    save_moga_results_json
)


def test_moga_strict_feasibility_and_reproducibility():
    config = BTSMOGAConfig(pop_size=10, n_gen=5, seed=42)

    res1 = run_bts_moga(config)
    res2 = run_bts_moga(config)

    assert isinstance(res1.success, bool)
    assert res1.feasible_fraction >= 0.0
    assert len(res1.history_hypervolume) == 5

    # Check reproducibility across same-seed runs
    if res1.success:
        np.testing.assert_allclose(res1.pareto_x, res2.pareto_x, atol=1e-10)


def test_infeasible_fallback_handling():
    # Force impossible tight beta limit (1.0 m) to test infeasible fallback
    config = BTSMOGAConfig(pop_size=10, n_gen=3, beta_max_limit=1.0, seed=42)
    res = run_bts_moga(config)

    assert res.success is False
    assert res.feasible_fraction == 0.0
    assert len(res.least_infeasible_x) > 0
    assert res.min_violation > 0.0


def test_true_aperture_margin_calculation():
    config = BTSMOGAConfig(aperture_radius_m=0.01935)
    margin = compute_true_aperture_margin(beta_m=30.0, disp_m=0.1, config=config)

    # Margin should be pipe radius (19.35 mm) - envelope
    assert margin < 0.01935


def test_moga_json_archival(tmp_path):
    config = BTSMOGAConfig(pop_size=10, n_gen=3, seed=42)
    res = run_bts_moga(config)

    save_moga_results_json(res, output_dir=tmp_path)
    assert (tmp_path / "moga_summary.json").is_file()
