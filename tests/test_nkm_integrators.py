"""
Unit tests for Symplectic Split and Lorentz RK4 integrators (Task 03)
"""

import sys
from pathlib import Path
import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.nkm.integrators import SymplecticSplitIntegrator, LorentzRK4Integrator
from src.nkm.tracking import track_nkm_thick_symplectic, track_nkm_thick_rk4, track_nkm_thin_kick
from src.nkm.units import compute_rigidity, ELECTRON_CHARGE_C


def test_zero_field_limit():
    """Zero magnetic field should reduce to a pure drift of length L."""
    def zero_field(x, y, z):
        return np.zeros_like(x), np.zeros_like(x)

    beam_in = np.zeros((6, 2))
    beam_in[0, 0] = -0.010  # x = -10 mm
    beam_in[1, 0] = 0.001   # xp = 1 mrad
    beam_in[2, 1] = 0.005   # y = 5 mm
    beam_in[3, 1] = -0.002  # yp = -2 mrad

    length_m = 0.525

    # Symplectic split tracker
    beam_sym = track_nkm_thick_symplectic(beam_in, zero_field, length_m=length_m, n_slices=20)
    # RK4 tracker
    beam_rk4 = track_nkm_thick_rk4(beam_in, zero_field, length_m=length_m, n_slices=20)

    # Pure drift x_out = x_in + xp * L, xp_out = xp_in
    np.testing.assert_allclose(beam_sym[0, :], beam_in[0, :] + beam_in[1, :] * length_m, atol=1e-12)
    np.testing.assert_allclose(beam_sym[1, :], beam_in[1, :], atol=1e-12)
    np.testing.assert_allclose(beam_sym[2, :], beam_in[2, :] + beam_in[3, :] * length_m, atol=1e-12)
    np.testing.assert_allclose(beam_sym[3, :], beam_in[3, :], atol=1e-12)

    np.testing.assert_allclose(beam_rk4[0, :], beam_in[0, :] + beam_in[1, :] * length_m, atol=1e-12)
    np.testing.assert_allclose(beam_rk4[1, :], beam_in[1, :], atol=1e-12)


def test_uniform_field_limit():
    """Uniform dipole field By = B0 gives constant deflection rate Delta xp = - B0 * L / B_rho for electrons."""
    B0 = 0.146  # 0.146 T
    def uniform_field(x, y, z):
        return np.full_like(x, B0), np.zeros_like(x)

    length_m = 0.525
    energy_GeV = 4.0
    brho = compute_rigidity(energy_GeV * 1e9, ELECTRON_CHARGE_C)
    expected_kick_rad = - B0 * length_m / brho  # ~ -0.005747 rad

    beam_in = np.zeros((6, 1))

    beam_sym = track_nkm_thick_symplectic(beam_in, uniform_field, length_m=length_m, n_slices=100, energy_GeV=energy_GeV)
    beam_rk4 = track_nkm_thick_rk4(beam_in, uniform_field, length_m=length_m, n_slices=100, energy_GeV=energy_GeV)

    assert pytest.approx(beam_sym[1, 0], rel=1e-4) == expected_kick_rad
    assert pytest.approx(beam_rk4[1, 0], rel=1e-4) == expected_kick_rad


def test_slice_convergence():
    """Check convergence of exit position and angle as slice count increases."""
    def nkm_model_field(x, y, z):
        # Model NKM B_y(x) profile
        by = 0.146 * np.exp(-((x + 0.010)/0.015)**2)
        bx = np.zeros_like(x)
        return by, bx

    beam_in = np.zeros((6, 1))
    beam_in[0, 0] = -0.010  # -10 mm offset

    slice_counts = [10, 20, 40, 80, 160]
    exit_xp = []

    for n in slice_counts:
        out = track_nkm_thick_symplectic(beam_in, nkm_model_field, length_m=0.525, n_slices=n)
        exit_xp.append(out[1, 0])

    ref_xp = exit_xp[-1]
    errors = [abs(xp - ref_xp) for xp in exit_xp]

    # Error must decrease monotonically with slice refinement
    assert errors[-2] < errors[0]
    assert errors[-1] < 1e-7
