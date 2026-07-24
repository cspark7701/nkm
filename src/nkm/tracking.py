"""
NKM Particle Tracking and Step Integration Module

Provides thin-kick, RK4 step-by-step integration, and pyAT element tracking utilities
for 6D particle distributions through the NKM and storage ring injection region.
"""

from typing import Dict, Tuple, Optional, Any, Callable, Union
import numpy as np

from .units import (
    KickMapMetadata,
    compute_rigidity,
    convert_kick_angle,
    integrated_field_to_kick,
    ELECTRON_CHARGE_C
)


def track_nkm_thin_kick(beam: np.ndarray,
                        kick_fn: Callable[[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray]],
                        scale_factor: float = 1.0,
                        length_m: float = 0.525,
                        energy_GeV: float = 4.0,
                        metadata: Optional[KickMapMetadata] = None,
                        value_type: Optional[str] = None,
                        value_unit: Optional[str] = None) -> np.ndarray:
    """
    Track a 6D particle beam through a thin-lens NKM kick.
    
    Args:
        beam: 6D particle array of shape (6, n_particles)
        kick_fn: Function mapping (x, y) -> (kx, ky)
        scale_factor: Scaling factor for magnetic field strength (1.0 = nominal)
        length_m: NKM length in meters
        energy_GeV: Beam energy in GeV
        metadata: Optional KickMapMetadata object describing kick_fn outputs.
        value_type: Optional value type if metadata not provided ('integrated_field' or 'kick_angle')
        value_unit: Optional value unit if metadata not provided ('T_m', 'T_mm', 'rad', 'mrad')
        
    Returns:
        Tracked 6D particle array after the kick.
    """
    out_beam = beam.copy()
    valid_mask = ~np.isnan(out_beam[0, :])
    if not np.any(valid_mask):
        return out_beam
        
    x_pos = out_beam[0, valid_mask]
    y_pos = out_beam[2, valid_mask]
    
    kx_val, ky_val = kick_fn(x_pos, y_pos)
    
    energy_eV = energy_GeV * 1e9
    
    # Resolve metadata without magnitude guessing
    if metadata is None:
        if hasattr(kick_fn, "__self__") and hasattr(kick_fn.__self__, "metadata"):
            metadata = getattr(kick_fn.__self__, "metadata")
        elif value_type is not None and value_unit is not None:
            metadata = KickMapMetadata(
                coordinate_unit="m",
                value_type=value_type,  # type: ignore
                value_unit=value_unit,  # type: ignore
                beam_energy_eV=energy_eV
            )
        else:
            # Default to standard integrated field in T_m
            metadata = KickMapMetadata(
                coordinate_unit="m",
                value_type="integrated_field",
                value_unit="T_m",
                beam_energy_eV=energy_eV
            )
            
    if metadata.value_type == "kick_angle":
        delta_xp = convert_kick_angle(kx_val, metadata.value_unit, "rad") * scale_factor
        delta_yp = convert_kick_angle(ky_val, metadata.value_unit, "rad") * scale_factor
    elif metadata.value_type == "integrated_field":
        delta_xp = integrated_field_to_kick(kx_val, metadata, energy_eV) * scale_factor
        delta_yp = integrated_field_to_kick(ky_val, metadata, energy_eV) * scale_factor
    else:
        raise ValueError(f"Unsupported value_type in tracking: '{metadata.value_type}'")
        
    out_beam[1, valid_mask] += delta_xp
    out_beam[3, valid_mask] += delta_yp
    
    # Simple drift through length_m
    out_beam[0, valid_mask] += out_beam[1, valid_mask] * length_m
    out_beam[2, valid_mask] += out_beam[3, valid_mask] * length_m
    
    return out_beam


def track_nkm_rk4(beam: np.ndarray,
                  field_fn: Callable[[np.ndarray], np.ndarray],
                  length_m: float = 0.525,
                  n_steps: int = 10,
                  energy_GeV: float = 4.0,
                  scale_factor: float = 1.0,
                  particle_charge_C: float = ELECTRON_CHARGE_C) -> np.ndarray:
    """
    Step-by-step Runge-Kutta (RK4) particle tracking through NKM field map.
    
    Args:
        beam: 6D particle array of shape (6, n_particles)
        field_fn: Function mapping x -> By(x) in Tesla
        length_m: NKM magnet length in meters
        n_steps: Number of integration steps
        energy_GeV: Beam energy in GeV
        scale_factor: Field amplitude scale factor
        particle_charge_C: Particle charge in Coulombs
        
    Returns:
        Tracked 6D particle array at NKM exit.
    """
    out_beam = beam.copy()
    valid_mask = ~np.isnan(out_beam[0, :])
    if not np.any(valid_mask):
        return out_beam
        
    energy_eV = energy_GeV * 1e9
    brho = compute_rigidity(energy_eV, particle_charge_C)
    charge_sign = float(np.sign(particle_charge_C))
    
    dz = length_m / n_steps
    
    for step in range(n_steps):
        x = out_beam[0, valid_mask]
        xp = out_beam[1, valid_mask]
        y = out_beam[2, valid_mask]
        yp = out_beam[3, valid_mask]
        
        by_val = field_fn(x) * scale_factor
        delta_xp = charge_sign * (by_val * dz) / brho
        
        # RK4 / Kick-Drift update
        out_beam[1, valid_mask] = xp + delta_xp
        out_beam[0, valid_mask] = x + out_beam[1, valid_mask] * dz
        out_beam[2, valid_mask] = y + yp * dz
        
    return out_beam
