"""
NKM Units and Physics Conventions Module

Provides immutable metadata structures, canonical unit conversions,
rigidity calculations, and sign conventions for NKM magnetic fields and kicks.
"""

from dataclasses import dataclass
from typing import Literal, Optional, Union, NewType
import numpy as np

# Physical NewType unit aliases
Meters = NewType("Meters", float)
Millimeters = NewType("Millimeters", float)
Radians = NewType("Radians", float)
Milliradians = NewType("Milliradians", float)
Tesla = NewType("Tesla", float)
TeslaMeters = NewType("TeslaMeters", float)
GigaelectronVolts = NewType("GigaelectronVolts", float)
ElectronVolts = NewType("ElectronVolts", float)

# Physical constants in SI units
SPEED_OF_LIGHT_MS: float = 299792458.0
ELEMENTARY_CHARGE_C: float = 1.602176634e-19
ELECTRON_CHARGE_C: float = -1.602176634e-19


def validate_positive(val: float, param_name: str) -> float:
    """Validate that a numerical parameter is strictly positive (> 0)."""
    if val <= 0:
        raise ValueError(f"Parameter '{param_name}' must be positive, got {val}")
    return float(val)


def validate_non_zero(val: float, param_name: str) -> float:
    """Validate that a numerical parameter is non-zero."""
    if val == 0:
        raise ValueError(f"Parameter '{param_name}' cannot be zero")
    return float(val)


def validate_finite(val: Union[float, np.ndarray], param_name: str) -> Union[float, np.ndarray]:
    """Validate that value(s) are finite (no NaN or Inf)."""
    if not np.all(np.isfinite(val)):
        raise ValueError(f"Parameter '{param_name}' contains non-finite values (NaN or Inf): {val}")
    return val


@dataclass(frozen=True)
class KickMapMetadata:
    coordinate_unit: Literal["m", "mm"]
    value_type: Literal["field", "integrated_field", "kick_angle"]
    value_unit: Literal["T", "T_m", "T_mm", "rad", "mrad"]
    beam_energy_eV: Optional[float]
    particle_charge_C: float = ELECTRON_CHARGE_C
    longitudinal_unit: Optional[Literal["m", "mm"]] = "m"
    sign_convention: str = "AT"

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Validate metadata consistency."""
        valid_coords = ("m", "mm")
        valid_types = ("field", "integrated_field", "kick_angle")
        valid_units = ("T", "T_m", "T_mm", "rad", "mrad")

        if self.coordinate_unit not in valid_coords:
            raise ValueError(f"Invalid coordinate_unit: '{self.coordinate_unit}'. Must be one of {valid_coords}")
        if self.value_type not in valid_types:
            raise ValueError(f"Invalid value_type: '{self.value_type}'. Must be one of {valid_types}")
        if self.value_unit not in valid_units:
            raise ValueError(f"Invalid value_unit: '{self.value_unit}'. Must be one of {valid_units}")
        if self.beam_energy_eV is not None and self.beam_energy_eV <= 0:
            raise ValueError(f"beam_energy_eV must be positive if provided, got {self.beam_energy_eV}")

        # Check value_type and value_unit compatibility
        if self.value_type == "field" and self.value_unit != "T":
            raise ValueError(f"value_type 'field' requires value_unit 'T', got '{self.value_unit}'")
        if self.value_type == "integrated_field" and self.value_unit not in ("T_m", "T_mm"):
            raise ValueError(f"value_type 'integrated_field' requires 'T_m' or 'T_mm', got '{self.value_unit}'")
        if self.value_type == "kick_angle" and self.value_unit not in ("rad", "mrad"):
            raise ValueError(f"value_type 'kick_angle' requires 'rad' or 'mrad', got '{self.value_unit}'")


def compute_rigidity(beam_energy_eV: Union[float, ElectronVolts],
                     particle_charge_C: float = ELECTRON_CHARGE_C) -> TeslaMeters:
    """
    Calculate magnetic rigidity B*rho in T*m.
    
    B*rho = p0 / |q| = E_eV * e / (|q| * c)
    For relativistic electron (|q| = e): B*rho = E_eV / c
    """
    validate_positive(float(beam_energy_eV), "beam_energy_eV")
    validate_non_zero(float(particle_charge_C), "particle_charge_C")
    
    charge_abs = abs(particle_charge_C)
    rigidity = (float(beam_energy_eV) * ELEMENTARY_CHARGE_C) / (charge_abs * SPEED_OF_LIGHT_MS)
    return TeslaMeters(float(rigidity))


def convert_coordinate(val: Union[float, np.ndarray], from_unit: str, to_unit: str = "m") -> Union[float, np.ndarray]:
    """Convert coordinate from from_unit to to_unit ('m' or 'mm')."""
    if from_unit == to_unit:
        return val
    if from_unit == "mm" and to_unit == "m":
        return val * 1e-3
    if from_unit == "m" and to_unit == "mm":
        return val * 1e3
    raise ValueError(f"Unsupported coordinate conversion from '{from_unit}' to '{to_unit}'")


def convert_integrated_field(val: Union[float, np.ndarray], from_unit: str, to_unit: str = "T_m") -> Union[float, np.ndarray]:
    """Convert integrated field from from_unit to to_unit ('T_m' or 'T_mm')."""
    if from_unit == to_unit:
        return val
    if from_unit == "T_mm" and to_unit == "T_m":
        return val * 1e-3
    if from_unit == "T_m" and to_unit == "T_mm":
        return val * 1e3
    raise ValueError(f"Unsupported integrated field conversion from '{from_unit}' to '{to_unit}'")


def convert_kick_angle(val: Union[float, np.ndarray], from_unit: str, to_unit: str = "rad") -> Union[float, np.ndarray]:
    """Convert kick angle from from_unit to to_unit ('rad' or 'mrad')."""
    if from_unit == to_unit:
        return val
    if from_unit == "mrad" and to_unit == "rad":
        return val * 1e-3
    if from_unit == "rad" and to_unit == "mrad":
        return val * 1e3
    raise ValueError(f"Unsupported kick angle conversion from '{from_unit}' to '{to_unit}'")


def integrated_field_to_kick(integrated_field: Union[float, np.ndarray],
                            metadata: KickMapMetadata,
                            beam_energy_eV: Optional[float] = None) -> Union[float, np.ndarray]:
    """
    Convert integrated field integral(B_y ds) to horizontal kick angle Delta x' in radians.
    
    Sign convention (AT / Lorentz):
    Delta x' = (q / |q|) * (integrated_field_Tm / B_rho)
    For electron (q < 0): Delta x' = - integrated_field_Tm / B_rho
    """
    energy = beam_energy_eV if beam_energy_eV is not None else metadata.beam_energy_eV
    if energy is None:
        raise ValueError("beam_energy_eV must be provided in metadata or as argument")

    int_field_Tm = convert_integrated_field(integrated_field, metadata.value_unit, "T_m")
    brho = compute_rigidity(energy, metadata.particle_charge_C)
    
    charge_sign = float(np.sign(metadata.particle_charge_C))  # -1.0 for electron
    kick_rad = charge_sign * (int_field_Tm / brho)
    return kick_rad


def kick_to_integrated_field(kick_rad: Union[float, np.ndarray],
                             metadata: KickMapMetadata,
                             beam_energy_eV: Optional[float] = None) -> Union[float, np.ndarray]:
    """
    Convert horizontal kick angle Delta x' in radians to integrated field integral(B_y ds) in T*m.
    """
    energy = beam_energy_eV if beam_energy_eV is not None else metadata.beam_energy_eV
    if energy is None:
        raise ValueError("beam_energy_eV must be provided in metadata or as argument")

    brho = compute_rigidity(energy, metadata.particle_charge_C)
    charge_sign = float(np.sign(metadata.particle_charge_C))  # -1.0 for electron
    int_field_Tm = charge_sign * kick_rad * brho
    return convert_integrated_field(int_field_Tm, "T_m", metadata.value_unit)
