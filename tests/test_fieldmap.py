"""
Unit and Integration Tests for Milestone 3 NKM Field Map Ingestion & Validation
"""

import sys
from pathlib import Path
import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.nkm.fieldmap import (
    load_1d_fieldmap,
    validate_1d_fieldmap,
    NKMFieldMap1D,
    OutOfDomainError
)
from src.nkm.kickmap import (
    load_2d_kickmap,
    NKMKickMap2D
)


@pytest.fixture
def by_txt_path():
    p = REPO_ROOT / "By.txt"
    assert p.is_file(), f"By.txt missing at {p}"
    return p


@pytest.fixture
def excel_path():
    p = REPO_ROOT / "nkm_field.xlsx"
    assert p.is_file(), f"nkm_field.xlsx missing at {p}"
    return p


@pytest.fixture
def kickmap_path():
    p = REPO_ROOT / "kickmap_file.txt"
    assert p.is_file(), f"kickmap_file.txt missing at {p}"
    return p


def test_1d_fieldmap_loading_and_validation(by_txt_path, excel_path):
    """Test loading and validating 1D field maps."""
    x_by, by_vals = load_1d_fieldmap(by_txt_path)
    assert len(x_by) == 201
    val_by = validate_1d_fieldmap(x_by, by_vals)
    assert val_by["valid"] is True
    assert pytest.approx(val_by["peak_by_T"], abs=1e-3) == 0.146

    x_ex, by_ex = load_1d_fieldmap(excel_path)
    assert len(x_ex) == 51
    val_ex = validate_1d_fieldmap(x_ex, by_ex)
    assert val_ex["valid"] is True


def test_1d_interpolation_accuracy(by_txt_path):
    """Verify 1D interpolation reproduces tabulated source data points."""
    x_by, by_vals = load_1d_fieldmap(by_txt_path)
    fmap = NKMFieldMap1D(x_by, by_vals)
    
    by_interp = fmap.evaluate(x_by, method='linear')
    max_err = float(np.max(np.abs(by_interp - by_vals)))
    assert max_err < 1e-12


def test_1d_out_of_domain_protection(by_txt_path):
    """Verify that silent extrapolation is disabled by default."""
    x_by, by_vals = load_1d_fieldmap(by_txt_path)
    fmap = NKMFieldMap1D(x_by, by_vals, allow_extrapolation=False)
    
    with pytest.raises(OutOfDomainError):
        fmap.evaluate(0.10)  # x=100mm is outside [-50mm, 50mm]


def test_1d_symmetry_residuals(by_txt_path):
    """Verify odd symmetry residual for By.txt."""
    x_by, by_vals = load_1d_fieldmap(by_txt_path)
    val = validate_1d_fieldmap(x_by, by_vals)
    assert val["odd_symmetry_residual_T"] is not None
    assert val["odd_symmetry_residual_T"] < 1e-6


def test_2d_kickmap_loading_and_properties(kickmap_path):
    """Test 2D kick map parsing and dimension verification."""
    length_m, x_grid, y_grid, kx_map, ky_map = load_2d_kickmap(kickmap_path)
    assert length_m == 0.525
    assert len(x_grid) == 201
    assert len(y_grid) == 201
    assert kx_map.shape == (201, 201)
    assert ky_map.shape == (201, 201)


def test_2d_grid_interpolation_accuracy(kickmap_path):
    """Verify 2D interpolation error at grid nodes is zero."""
    kmap = NKMKickMap2D(kickmap_path)
    max_err = kmap.verify_grid_interpolation()
    assert max_err < 1e-12


def test_2d_out_of_domain_protection(kickmap_path):
    """Verify that silent extrapolation is disabled by default."""
    kmap = NKMKickMap2D(kickmap_path, allow_extrapolation=False)
    with pytest.raises(OutOfDomainError):
        kmap.evaluate(0.10, 0.0)  # 100 mm is outside [-50mm, 50mm]


def test_2d_symmetry_residuals(kickmap_path):
    """Verify 2D Kx and Ky odd symmetry residuals across x-y domain."""
    kmap = NKMKickMap2D(kickmap_path)
    sym = kmap.compute_symmetry_residuals()
    assert sym["kx_odd_x_symmetry_residual"] < 1e-6
    assert sym["ky_odd_y_symmetry_residual"] < 1e-6


def test_lorentz_kick_sign(kickmap_path):
    """Verify sign of Lorentz force kick at off-axis position."""
    kmap = NKMKickMap2D(kickmap_path)
    lorentz = kmap.verify_lorentz_kick_sign(x_offset_m=-0.010)
    assert lorentz["sign_verified"] is True
    assert lorentz["kx_value"] < 0.0  # negative kick for x < 0 in injection region
