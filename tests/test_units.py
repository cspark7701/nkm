"""
Unit tests for src/nkm/units.py
"""

import pytest
import numpy as np

from nkm.units import (
    KickMapMetadata,
    compute_rigidity,
    convert_coordinate,
    convert_integrated_field,
    convert_kick_angle,
    integrated_field_to_kick,
    kick_to_integrated_field,
    ELECTRON_CHARGE_C,
    ELEMENTARY_CHARGE_C,
    SPEED_OF_LIGHT_MS
)


def test_rigidity_computation():
    energy_eV = 4.0e9  # 4 GeV
    brho = compute_rigidity(energy_eV)
    # Expected B*rho = 4e9 / 299792458 ~ 13.34256 T*m
    expected = 4.0e9 / SPEED_OF_LIGHT_MS
    assert pytest.approx(brho, rel=1e-6) == expected

    with pytest.raises(ValueError, match="beam_energy_eV must be positive"):
        compute_rigidity(-1.0)

    with pytest.raises(ValueError, match="particle_charge_C cannot be zero"):
        compute_rigidity(4.0e9, particle_charge_C=0.0)


def test_metadata_validation():
    # Valid metadata
    meta = KickMapMetadata(
        coordinate_unit="m",
        value_type="integrated_field",
        value_unit="T_m",
        beam_energy_eV=4.0e9
    )
    assert meta.coordinate_unit == "m"

    # Invalid coordinate unit
    with pytest.raises(ValueError, match="Invalid coordinate_unit"):
        KickMapMetadata(coordinate_unit="cm", value_type="field", value_unit="T", beam_energy_eV=4.0e9)

    # Incompatible value_type and value_unit
    with pytest.raises(ValueError, match="value_type 'field' requires value_unit 'T'"):
        KickMapMetadata(coordinate_unit="m", value_type="field", value_unit="T_m", beam_energy_eV=4.0e9)

    with pytest.raises(ValueError, match="value_type 'kick_angle' requires 'rad' or 'mrad'"):
        KickMapMetadata(coordinate_unit="m", value_type="kick_angle", value_unit="T_m", beam_energy_eV=4.0e9)


def test_conversions():
    # T_mm to T_m
    assert convert_integrated_field(1000.0, "T_mm", "T_m") == 1.0
    assert convert_integrated_field(1.5, "T_m", "T_mm") == 1500.0

    # mrad to rad
    assert convert_kick_angle(5.749, "mrad", "rad") == 5.749e-3
    assert convert_kick_angle(0.005749, "rad", "mrad") == 5.749

    # coordinate mm to m
    assert convert_coordinate(50.0, "mm", "m") == 0.05


def test_electron_and_positive_charge_signs():
    meta_e = KickMapMetadata(
        coordinate_unit="m",
        value_type="integrated_field",
        value_unit="T_m",
        beam_energy_eV=4.0e9,
        particle_charge_C=ELECTRON_CHARGE_C
    )

    meta_p = KickMapMetadata(
        coordinate_unit="m",
        value_type="integrated_field",
        value_unit="T_m",
        beam_energy_eV=4.0e9,
        particle_charge_C=ELEMENTARY_CHARGE_C
    )

    int_field = 0.0767  # T*m (~5.749 mrad at 4 GeV)
    kick_e = integrated_field_to_kick(int_field, meta_e)
    kick_p = integrated_field_to_kick(int_field, meta_p)

    # Electron kick must be negative for positive integrated vertical field (AT convention)
    assert kick_e < 0
    assert kick_p > 0
    assert pytest.approx(abs(kick_e), rel=1e-6) == abs(kick_p)


def test_roundtrip_conversions():
    meta = KickMapMetadata(
        coordinate_unit="m",
        value_type="integrated_field",
        value_unit="T_m",
        beam_energy_eV=4.0e9
    )

    orig_int_field = np.array([0.01, 0.05, 0.0767])
    kick_rad = integrated_field_to_kick(orig_int_field, meta)
    recovered_int_field = kick_to_integrated_field(kick_rad, meta)

    np.testing.assert_allclose(orig_int_field, recovered_int_field, rtol=1e-12)


def test_rejection_of_ambiguous_input():
    meta_no_energy = KickMapMetadata(
        coordinate_unit="m",
        value_type="integrated_field",
        value_unit="T_m",
        beam_energy_eV=None
    )

    with pytest.raises(ValueError, match="beam_energy_eV must be provided"):
        integrated_field_to_kick(0.05, meta_no_energy)
