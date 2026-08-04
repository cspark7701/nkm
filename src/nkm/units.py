"""
NKM Units and Physics Conventions Module

Provides immutable metadata structures, canonical unit conversions,
rigidity calculations, and sign conventions for NKM magnetic fields and kicks.
"""

from dataclasses import dataclass
from typing import Literal, Optional, Union, NewType, Tuple
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


def integrated_field_to_transverse_kicks(
    int_bx_t_m: Union[float, np.ndarray],
    int_by_t_m: Union[float, np.ndarray],
    *,
    beam_energy_eV: float,
    particle_charge_C: float = ELECTRON_CHARGE_C,
    coordinate_convention: str = "AT"
) -> Tuple[Union[float, np.ndarray], Union[float, np.ndarray]]:
    """
    Convert integrated magnetic field components (integral B_x ds, integral B_y ds) in T*m
    to transverse kick angles (Delta x', Delta y') in radians using Lorentz-force physics.
    
    Lorentz Force Derivation (Ultra-relativistic beam with v_z ≈ c):
      F_x = q (v_y B_z - v_z B_y) ≈ -q c B_y  =>  d(px)/ds = -q B_y  =>  Delta x' = (q / |q|) * (integral B_y ds / B_rho)
      F_y = q (v_z B_x - v_x B_z) ≈ +q c B_x  =>  d(py)/ds = -(q / |q|) * (integral B_x ds / B_rho)
      
    For electron beam (q = -e < 0):
      Delta x' = - (integral B_y ds) / B_rho
      Delta y' = + (integral B_x ds) / B_rho
      
    Args:
        int_bx_t_m: Integrated horizontal magnetic field component (integral B_x ds) in T*m.
        int_by_t_m: Integrated vertical magnetic field component (integral B_y ds) in T*m.
        beam_energy_eV: Beam energy in eV.
        particle_charge_C: Particle charge in Coulombs (default ELECTRON_CHARGE_C).
        coordinate_convention: Coordinate convention string (default 'AT').
        
    Returns:
        Tuple (delta_xp, delta_yp) in radians.
    """
    brho = compute_rigidity(beam_energy_eV, particle_charge_C)
    charge_sign = float(np.sign(particle_charge_C))  # -1.0 for electron
    
    delta_xp = charge_sign * (int_by_t_m / brho)
    delta_yp = -charge_sign * (int_bx_t_m / brho)
    
    return delta_xp, delta_yp


def transverse_kicks_to_integrated_field(
    delta_xp: Union[float, np.ndarray],
    delta_yp: Union[float, np.ndarray],
    *,
    beam_energy_eV: float,
    particle_charge_C: float = ELECTRON_CHARGE_C,
    coordinate_convention: str = "AT"
) -> Tuple[Union[float, np.ndarray], Union[float, np.ndarray]]:
    """
    Convert transverse kick angles (Delta x', Delta y') in radians back to integrated magnetic field
    components (integral B_x ds, integral B_y ds) in T*m.
    """
    brho = compute_rigidity(beam_energy_eV, particle_charge_C)
    charge_sign = float(np.sign(particle_charge_C))  # -1.0 for electron
    
    int_by_t_m = (delta_xp * brho) / charge_sign
    int_bx_t_m = (-delta_yp * brho) / charge_sign
    
    return int_bx_t_m, int_by_t_m


def integrated_field_to_kick(integrated_field: Union[float, np.ndarray],
                             metadata: KickMapMetadata,
                             beam_energy_eV: Optional[float] = None) -> Union[float, np.ndarray]:
    """
    Convert integrated field integral(B_y ds) to horizontal kick angle Delta x' in radians.
    Delegates to component-aware integrated_field_to_transverse_kicks.
    """
    energy = beam_energy_eV if beam_energy_eV is not None else metadata.beam_energy_eV
    if energy is None:
        raise ValueError("beam_energy_eV must be provided in metadata or as argument")

    int_field_Tm = convert_integrated_field(integrated_field, metadata.value_unit, "T_m")
    delta_xp, _ = integrated_field_to_transverse_kicks(
        int_bx_t_m=0.0,
        int_by_t_m=int_field_Tm,
        beam_energy_eV=energy,
        particle_charge_C=metadata.particle_charge_C,
        coordinate_convention=metadata.sign_convention
    )
    return delta_xp


def kick_to_integrated_field(kick_rad: Union[float, np.ndarray],
                             metadata: KickMapMetadata,
                             beam_energy_eV: Optional[float] = None) -> Union[float, np.ndarray]:
    """
    Convert horizontal kick angle Delta x' in radians to integrated field integral(B_y ds) in T*m.
    Delegates to component-aware transverse_kicks_to_integrated_field.
    """
    energy = beam_energy_eV if beam_energy_eV is not None else metadata.beam_energy_eV
    if energy is None:
        raise ValueError("beam_energy_eV must be provided in metadata or as argument")

    _, int_by_Tm = transverse_kicks_to_integrated_field(
        delta_xp=kick_rad,
        delta_yp=0.0,
        beam_energy_eV=energy,
        particle_charge_C=metadata.particle_charge_C,
        coordinate_convention=metadata.sign_convention
    )
    return convert_integrated_field(int_by_Tm, "T_m", metadata.value_unit)
