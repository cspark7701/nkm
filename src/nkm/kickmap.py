"""
NKM 2D Kick Map Processing and Interpolation Module

Provides read-only ingestion, 2D interpolation, symmetry quantification,
and Lorentz-force kick verification for 2D field/kick maps (e.g. kickmap_file.txt).
"""

from pathlib import Path
from typing import Dict, Tuple, Optional, Any, Union
import numpy as np
from scipy.interpolate import RegularGridInterpolator
from .fieldmap import OutOfDomainError


def load_2d_kickmap(filepath: Union[str, Path]) -> Tuple[float, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Parse a 2D kick map text file (e.g. kickmap_file.txt).
    
    Format:
        Length (m)
        Nx, Ny
        START
        x_grid values
        y_coord, row_values... (Section 1: Vertical Kick Map Ky / By integral)
        START
        x_grid values
        y_coord, row_values... (Section 2: Horizontal Kick Map Kx / Bx integral)
        
    Returns:
        Tuple of (length_m, x_grid, y_grid, kx_map, ky_map)
    """
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(f"Kick map file not found: {path}")
        
    with open(path, 'r') as f:
        lines = [line.split('#')[0].strip() for line in f if line.split('#')[0].strip()]
        
    tokens = ' '.join(lines).split()
    
    length_m = float(tokens[0])
    nx = int(tokens[1])
    ny = int(tokens[2])
    
    start_indices = [i for i, t in enumerate(tokens) if t == 'START']
    if len(start_indices) < 2:
        raise ValueError(f"Expected at least 2 'START' tokens in kickmap file, found {len(start_indices)}")
        
    s1, s2 = start_indices[0], start_indices[1]
    
    # Section 1 (Vertical kick map Ky / integrated field component)
    map1_tokens = [float(t) for t in tokens[s1 + 1 : s2]]
    x_grid = np.array(map1_tokens[:nx])
    map1_arr = np.array(map1_tokens[nx:]).reshape(ny, nx + 1)
    y_grid = map1_arr[:, 0]
    ky_map = map1_arr[:, 1:]
    
    # Section 2 (Horizontal kick map Kx / integrated field component)
    map2_tokens = [float(t) for t in tokens[s2 + 1 :]]
    map2_arr = np.array(map2_tokens[nx:]).reshape(ny, nx + 1)
    kx_map = map2_arr[:, 1:]
    
    return length_m, x_grid, y_grid, kx_map, ky_map


class NKMKickMap2D:
    """
    2D Interpolator for NKM kick maps with strict bounds checking and symmetry analytics.
    """
    def __init__(self, filepath: Union[str, Path], allow_extrapolation: bool = False):
        self.filepath = Path(filepath)
        self.length_m, self.x_grid, self.y_grid, self.kx_map, self.ky_map = load_2d_kickmap(self.filepath)
        
        self.x_min, self.x_max = float(self.x_grid.min()), float(self.x_grid.max())
        self.y_min, self.y_max = float(self.y_grid.min()), float(self.y_grid.max())
        self.allow_extrapolation = allow_extrapolation
        
        fill_val = None if allow_extrapolation else np.nan
        bounds_err = not allow_extrapolation
        
        # RegularGridInterpolator expects points as (y_grid, x_grid) matching matrix shape (ny, nx)
        self._interp_kx = RegularGridInterpolator((self.y_grid, self.x_grid), self.kx_map,
                                                   bounds_error=bounds_err, fill_value=fill_val)
        self._interp_ky = RegularGridInterpolator((self.y_grid, self.x_grid), self.ky_map,
                                                   bounds_error=bounds_err, fill_value=fill_val)

    def evaluate(self, x: Union[float, np.ndarray], y: Union[float, np.ndarray]) -> Tuple[Union[float, np.ndarray], Union[float, np.ndarray]]:
        """
        Evaluate (Kx, Ky) kick values at (x, y).
        
        Args:
            x: horizontal position in m
            y: vertical position in m
            
        Returns:
            Tuple of (Kx, Ky) kick values.
        """
        x_arr = np.atleast_1d(x)
        y_arr = np.atleast_1d(y)
        
        pts = np.column_stack([y_arr, x_arr])
        try:
            kx_eval = self._interp_kx(pts)
            ky_eval = self._interp_ky(pts)
        except ValueError as err:
            raise OutOfDomainError(f"Points out of 2D grid domain x∈[{self.x_min}, {self.x_max}], y∈[{self.y_min}, {self.y_max}]: {err}")
        
        if np.ndim(x) == 0 and np.ndim(y) == 0:
            return float(kx_eval[0]), float(ky_eval[0])
        return kx_eval, ky_eval

    def verify_grid_interpolation(self) -> float:
        """
        Verify interpolation accuracy at exact grid nodes.
        
        Returns:
            Maximum absolute error between interpolated and original matrix values.
        """
        Y, X = np.meshgrid(self.y_grid, self.x_grid, indexing='ij')
        pts = np.column_stack([Y.ravel(), X.ravel()])
        
        kx_interp = self._interp_kx(pts).reshape(self.kx_map.shape)
        ky_interp = self._interp_ky(pts).reshape(self.ky_map.shape)
        
        err_x = float(np.max(np.abs(kx_interp - self.kx_map)))
        err_y = float(np.max(np.abs(ky_interp - self.ky_map)))
        return max(err_x, err_y)

    def compute_symmetry_residuals(self) -> Dict[str, float]:
        """
        Quantify 2D symmetry and antisymmetry residuals across the x-y grid.
        
        - Kx exhibits odd symmetry in x: Kx(-x, y) = -Kx(x, y) -> Kx(-x, y) + Kx(x, y) = 0
        - Ky exhibits odd symmetry in y: Ky(x, -y) = -Ky(x, y) -> Ky(x, -y) + Ky(x, y) = 0
        """
        kx_flipped_x = np.fliplr(self.kx_map)
        ky_flipped_y = np.flipud(self.ky_map)
        
        odd_sym_kx = float(np.max(np.abs(self.kx_map + kx_flipped_x)))
        odd_sym_ky = float(np.max(np.abs(self.ky_map + ky_flipped_y)))
        
        return {
            "kx_odd_x_symmetry_residual": odd_sym_kx,
            "ky_odd_y_symmetry_residual": odd_sym_ky,
            "kx_peak_value": float(np.max(np.abs(self.kx_map))),
            "ky_peak_value": float(np.max(np.abs(self.ky_map))),
        }

    def verify_lorentz_kick_sign(self, x_offset_m: float = -0.010, energy_GeV: float = 4.0) -> Dict[str, Any]:
        """
        Verify the sign convention of Lorentz-force kick on a relativistic electron beam.
        """
        kx_val, ky_val = self.evaluate(x_offset_m, 0.0)
        c = 299792458.0
        energy_eV = energy_GeV * 1e9
        rigidity_brho = energy_eV / c
        
        return {
            "x_offset_mm": x_offset_m * 1e3,
            "kx_value": float(kx_val),
            "ky_value": float(ky_val),
            "sign_verified": bool(kx_val < 0 if x_offset_m < 0 else kx_val > 0),
        }
