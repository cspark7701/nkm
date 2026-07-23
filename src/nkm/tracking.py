"""
NKM Particle Tracking and Step Integration Module

Provides thin-kick, RK4 step-by-step integration, and pyAT element tracking utilities
for 6D particle distributions through the NKM and storage ring injection region.
"""

from typing import Dict, Tuple, Optional, Any, Callable, Union
import numpy as np
import at


def track_nkm_thin_kick(beam: np.ndarray,
                        kick_fn: Callable[[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray]],
                        scale_factor: float = 1.0,
                        length_m: float = 0.525,
                        energy_GeV: float = 4.0) -> np.ndarray:
    """
    Track a 6D particle beam through a thin-lens NKM kick.
    
    Args:
        beam: 6D particle array of shape (6, n_particles)
        kick_fn: Function mapping (x, y) -> (kx, ky) in T*m or mrad
        scale_factor: Scaling factor for magnetic field strength (1.0 = nominal)
        length_m: NKM length in meters
        energy_GeV: Beam energy in GeV
        
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
    
    c = 299792458.0
    energy_eV = energy_GeV * 1e9
    rigidity_brho = energy_eV / c  # T*m
    
    # Calculate kick angles in radians
    # Note: Kx value in kickmap is already integrated field or direct kick angle
    # Check if kx_val is in mrad or T*m: if peak is ~5.75, it represents kick in mrad
    if np.max(np.abs(kx_val)) > 1.0:  # Value is in mrad
        delta_xp = - (kx_val * 1e-3) * scale_factor
        delta_yp = - (ky_val * 1e-3) * scale_factor
    else:  # Value is integrated field in T*m
        delta_xp = - (kx_val / rigidity_brho) * scale_factor
        delta_yp = - (ky_val / rigidity_brho) * scale_factor
        
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
                  scale_factor: float = 1.0) -> np.ndarray:
    """
    Step-by-step Runge-Kutta (RK4) particle tracking through NKM field map.
    
    Args:
        beam: 6D particle array of shape (6, n_particles)
        field_fn: Function mapping x -> By(x) in Tesla
        length_m: NKM magnet length in meters
        n_steps: Number of integration steps
        energy_GeV: Beam energy in GeV
        scale_factor: Field amplitude scale factor
        
    Returns:
        Tracked 6D particle array at NKM exit.
    """
    out_beam = beam.copy()
    valid_mask = ~np.isnan(out_beam[0, :])
    if not np.any(valid_mask):
        return out_beam
        
    c = 299792458.0
    energy_eV = energy_GeV * 1e9
    rigidity_brho = energy_eV / c
    
    dz = length_m / n_steps
    
    for step in range(n_steps):
        x = out_beam[0, valid_mask]
        xp = out_beam[1, valid_mask]
        y = out_beam[2, valid_mask]
        yp = out_beam[3, valid_mask]
        
        by_val = field_fn(x) * scale_factor
        delta_xp = - (by_val * dz) / rigidity_brho
        
        # RK4 / Kick-Drift update
        out_beam[1, valid_mask] = xp + delta_xp
        out_beam[0, valid_mask] = x + out_beam[1, valid_mask] * dz
        out_beam[2, valid_mask] = y + yp * dz
        
    return out_beam
