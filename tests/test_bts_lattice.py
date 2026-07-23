"""
Unit and Integration Tests for Milestone 2 BTS Lattice & Optics Validation
"""

import sys
from pathlib import Path
import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.nkm.bts_lattice import (
    BTSConfig,
    create_bts_lattice,
    validate_bts_lattice,
    check_symplecticity
)
from src.nkm.optics import (
    compute_mismatch_metric,
    compute_twiss_propagation,
    compute_bts_optics_metrics,
    beam_sigma_matrix_2d
)


@pytest.fixture
def default_config():
    return BTSConfig()


@pytest.fixture
def bts_lat(default_config):
    return create_bts_lattice(default_config)


def test_bts_config_defaults(default_config):
    """Test BTSConfig parameters and bending angle sum."""
    assert default_config.energy_eV == 4.0e9
    assert len(default_config.quad_strengths_list) == 9
    assert pytest.approx(default_config.total_bending_angle, abs=1e-5) == np.radians(7.855498)


def test_bts_lattice_creation_and_properties(bts_lat):
    """Test lattice element count, total length, and family names."""
    assert len(bts_lat) == 36
    assert pytest.approx(bts_lat.s_range[-1], abs=1e-3) == 21.789
    
    family_names = [elem.FamName for elem in bts_lat]
    assert "q11" in family_names
    assert "q33" in family_names
    assert "b1" in family_names
    assert "sept_in" in family_names


def test_bts_lattice_health_checks(bts_lat):
    """Verify that all lattice health validation checks pass."""
    val_res = validate_bts_lattice(bts_lat)
    assert val_res["all_checks_passed"] is True
    assert val_res["is_m44_finite"] is True
    assert val_res["is_m66_finite"] is True
    assert val_res["apertures_valid"] is True


def test_bts_lattice_symplecticity(bts_lat):
    """Verify linear map symplecticity error is within tight numerical tolerance."""
    val_res = validate_bts_lattice(bts_lat)
    assert val_res["symplecticity_error_m44"] < 1e-12
    assert val_res["symplecticity_error_m66"] < 1e-10


def test_mismatch_metric_identity():
    """Verify mismatch metric M_u returns exactly 0 when beam matches target."""
    m_x = compute_mismatch_metric(beta_out=10.0, alpha_out=-1.5,
                                  beta_target=10.0, alpha_target=-1.5)
    assert pytest.approx(m_x, abs=1e-12) == 0.0


def test_mismatch_metric_non_zero():
    """Verify mismatch metric M_u returns positive value for mismatched parameters."""
    m_x = compute_mismatch_metric(beta_out=20.0, alpha_out=0.0,
                                  beta_target=10.0, alpha_target=0.0)
    assert m_x > 0.0
    # For beta_out = 2 * beta_target and alpha = 0: Tr(diag(0.5, 2.0) * diag(2.0, 0.5)) = 0.5*2 + 2*0.5 = 2.5 -> M_u = 0.25
    assert pytest.approx(m_x, abs=1e-6) == 0.25


def test_zero_strength_quad_limit():
    """Verify lattice creation and optics with all quadrupoles set to zero strength."""
    config = BTSConfig(
        k_q11=0.0, k_q12=0.0, k_q13=0.0,
        k_q21=0.0, k_q22=0.0, k_q23=0.0,
        k_q31=0.0, k_q32=0.0, k_q33=0.0
    )
    lat_zero = create_bts_lattice(config)
    val = validate_bts_lattice(lat_zero)
    assert val["all_checks_passed"] is True
    assert val["symplecticity_error_m44"] < 1e-12
