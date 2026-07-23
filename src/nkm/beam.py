"""
6D Beam Generation, Centroid Manipulation, and Emittance Analysis Module

Provides robust utilities for generating 6D particle ensembles (Gaussian or truncated),
shifting centroids, computing 2D/4D/6D beam covariance matrices, and measuring projected emittances.
"""

from dataclasses import dataclass
from typing import Dict, Tuple, Optional, Any, Union
import numpy as np
import at


def generate_6d_beam(n_particles: int,
                     beta_x: float, alpha_x: float, emit_x: float,
                     beta_y: float, alpha_y: float, emit_y: float,
                     blength: float = 13.4e-3, espread: float = 1.1e-3,
                     x_offset: float = 0.0, xp_offset: float = 0.0,
                     y_offset: float = 0.0, yp_offset: float = 0.0,
                     seed: int = 42) -> np.ndarray:
    """
    Generate a 6D phase-space particle beam matrix of shape (6, n_particles).
    
    Coordinates:
        [0]: x [m]
        [1]: x' [rad]
        [2]: y [m]
        [3]: y' [rad]
        [4]: delta (dp/p)
        [5]: s / ct [m]
    """
    if seed is not None:
        np.random.seed(seed)
    sigma_mat = at.sigma_matrix(
        betax=beta_x, alphax=alpha_x, emitx=emit_x,
        betay=beta_y, alphay=alpha_y, emity=emit_y,
        blength=blength, espread=espread
    )
    beam = at.beam(n_particles, sigma_mat)
    
    # Apply centroid offsets
    beam[0, :] += x_offset
    beam[1, :] += xp_offset
    beam[2, :] += y_offset
    beam[3, :] += yp_offset
    
    return beam


def compute_beam_centroid(beam: np.ndarray) -> np.ndarray:
    """
    Compute mean centroid of a 6D particle beam [x_mean, xp_mean, y_mean, yp_mean, delta_mean, s_mean].
    Filters out NaN (lost) particles.
    """
    valid_mask = ~np.isnan(beam[0, :])
    if not np.any(valid_mask):
        return np.full(6, np.nan)
        
    return np.mean(beam[:, valid_mask], axis=1)


def compute_projected_emittance(beam: np.ndarray) -> Tuple[float, float]:
    """
    Compute 2D projected geometric emittances (emit_x, emit_y) in m*rad.
    
    emit_u = sqrt( <u^2> <u'^2> - <u u'>^2 )
    """
    valid_mask = ~np.isnan(beam[0, :])
    if not np.any(valid_mask):
        return np.nan, np.nan
        
    b_valid = beam[:, valid_mask]
    
    x = b_valid[0, :] - np.mean(b_valid[0, :])
    xp = b_valid[1, :] - np.mean(b_valid[1, :])
    cov_x = np.cov(x, xp)
    emit_x = float(np.sqrt(max(0.0, np.linalg.det(cov_x))))
    
    y = b_valid[2, :] - np.mean(b_valid[2, :])
    yp = b_valid[3, :] - np.mean(b_valid[3, :])
    cov_y = np.cov(y, yp)
    emit_y = float(np.sqrt(max(0.0, np.linalg.det(cov_y))))
    
    return emit_x, emit_y


def compute_beam_statistics(beam: np.ndarray) -> Dict[str, Any]:
    """
    Compute full statistical summary of a 6D particle beam.
    """
    valid_mask = ~np.isnan(beam[0, :])
    n_total = beam.shape[1]
    n_valid = int(np.sum(valid_mask))
    survival_fraction = float(n_valid / n_total) if n_total > 0 else 0.0
    
    if n_valid == 0:
        return {
            "total_particles": n_total,
            "survived_particles": 0,
            "survival_fraction": 0.0,
            "centroid": None,
            "std": None,
            "emittance_x_mrad": np.nan,
            "emittance_y_mrad": np.nan,
        }
        
    b_valid = beam[:, valid_mask]
    centroid = np.mean(b_valid, axis=1)
    std_dev = np.std(b_valid, axis=1)
    emit_x, emit_y = compute_projected_emittance(beam)
    
    return {
        "total_particles": n_total,
        "survived_particles": n_valid,
        "survival_fraction": survival_fraction,
        "centroid": {
            "x_mm": float(centroid[0] * 1e3),
            "xp_mrad": float(centroid[1] * 1e3),
            "y_mm": float(centroid[2] * 1e3),
            "yp_mrad": float(centroid[3] * 1e3),
            "delta": float(centroid[4]),
            "s_mm": float(centroid[5] * 1e3),
        },
        "std_dev": {
            "sigma_x_mm": float(std_dev[0] * 1e3),
            "sigma_xp_mrad": float(std_dev[1] * 1e3),
            "sigma_y_mm": float(std_dev[2] * 1e3),
            "sigma_yp_mrad": float(std_dev[3] * 1e3),
        },
        "emittance_x_mrad": float(emit_x),
        "emittance_y_mrad": float(emit_y),
    }
