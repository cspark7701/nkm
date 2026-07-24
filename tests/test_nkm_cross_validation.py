"""
Unit and integration tests for src/nkm/validation.py (Task 02)
"""

import sys
from pathlib import Path
import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.nkm.validation import (
    get_input_data_hashes,
    compute_cross_validation,
    perform_interpolation_study,
    perform_grid_convergence_study,
    perform_linearity_study
)
from src.nkm.kickmap import NKMKickMap2D


def test_input_data_hashes():
    hashes = get_input_data_hashes(REPO_ROOT)
    assert "By.txt" in hashes
    assert "kickmap_file.txt" in hashes
    assert len(hashes["By.txt"]) == 64  # SHA-256 hex string length


def test_cross_validation_positions():
    x_positions = np.array([0.0, -0.010, -0.016, 0.016, 0.040])
    res = compute_cross_validation(x_positions, repo_root=REPO_ROOT)

    assert len(res["positions"]) == 5

    # Check x=0 stored beam axis: kick must be ~0
    pos_axis = res["positions"][0]
    assert pos_axis["x_mm"] == 0.0
    assert abs(pos_axis["kick_2d_mrad"]) < 1e-6
    assert abs(pos_axis["kick_tracking_thin_mrad"]) < 1e-6

    # Check x=-10mm: kick is ~ -5.434 mrad
    pos_10 = res["positions"][1]
    assert pos_10["x_mm"] == -10.0
    assert pos_10["kick_2d_mrad"] == pytest.approx(-5.4341, rel=1e-2)

    # Check x=-16mm nominal injection offset: kick is ~ -2.105 mrad
    pos_inj = res["positions"][2]
    assert pos_inj["x_mm"] == -16.0
    assert pos_inj["kick_2d_mrad"] == pytest.approx(-2.1046, rel=1e-2)
    assert pos_inj["kick_tracking_thin_mrad"] == pytest.approx(-2.1046, rel=1e-2)

    # Check tracking vs 2D kickmap agreement
    for p in res["positions"]:
        assert p["diff_2d_vs_thin_mrad"] < 1e-6


def test_interpolation_study():
    by_path = REPO_ROOT / "By.txt"
    x_test = np.linspace(-0.045, 0.045, 50)
    interp_res = perform_interpolation_study(by_path, x_test)

    assert interp_res["max_diff_T"] < 1e-3


def test_grid_convergence_study():
    by_path = REPO_ROOT / "By.txt"
    conv_res = perform_grid_convergence_study(by_path)

    # Errors must decrease as grid resolution increases
    errors = conv_res["errors_Tm"]
    assert errors[-1] < errors[0]


def test_linearity_study():
    kick_path = REPO_ROOT / "kickmap_file.txt"
    kmap = NKMKickMap2D(kick_path)

    lin_res = perform_linearity_study(kmap, x_test_m=-0.016)
    assert lin_res["max_linearity_error_mrad"] < 1e-12
