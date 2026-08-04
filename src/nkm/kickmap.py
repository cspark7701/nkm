"""
NKM 2D Kick Map Processing and Interpolation Module

Provides read-only ingestion, 2D interpolation, symmetry quantification,
and Lorentz-force kick verification for 2D field/kick maps (e.g. kickmap_file.txt).
"""

from pathlib import Path
from typing import Dict, Tuple, Optional, Any, Union
import numpy as np
from scipy.interpolate import RegularGridInterpolator

from .fieldmap import OutOfDomainError, BaseFieldMap
from .units import (
    KickMapMetadata,
    convert_kick_angle,
    convert_integrated_field,
    integrated_field_to_kick,
    integrated_field_to_transverse_kicks,
    ELECTRON_CHARGE_C
)


def load_2d_kickmap(filepath: Union[str, Path]) -> Tuple[float, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Parse a 2D kick map text file (e.g. kickmap_file.txt).
    
    Format:
        Length (m)
        Nx, Ny
        START
        x_grid values
        y_coord, row_values... (Section 1: Ky map / vertical field integral By ds)
        START
        x_grid values
        y_coord, row_values... (Section 2: Kx map / horizontal field integral Bx ds)
        
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
    
    # Section 1 (Vertical kick / By field integral map Ky)
    map1_tokens = [float(t) for t in tokens[s1 + 1 : s2]]
    x_grid = np.array(map1_tokens[:nx])
    map1_arr = np.array(map1_tokens[nx:]).reshape(ny, nx + 1)
    y_grid = map1_arr[:, 0]
    ky_map = map1_arr[:, 1:]
    
    # Section 2 (Horizontal kick / Bx field integral map Kx)
    map2_tokens = [float(t) for t in tokens[s2 + 1 :]]
    map2_arr = np.array(map2_tokens[nx:]).reshape(ny, nx + 1)
    kx_map = map2_arr[:, 1:]
    
    return length_m, x_grid, y_grid, kx_map, ky_map


class NKMKickMap2D(BaseFieldMap):
    """
    2D Interpolator for NKM kick maps with strict bounds checking, explicit metadata, and symmetry analytics.
    """
    def __init__(self, filepath: Union[str, Path],
                 allow_extrapolation: bool = False,
                 metadata: Optional[KickMapMetadata] = None):
        fp = Path(filepath)
        length_m, x_grid, y_grid, kx_map, ky_map = load_2d_kickmap(fp)
        
        meta = metadata or KickMapMetadata(
            coordinate_unit="m",
            value_type="kick_angle",
            value_unit="mrad",
            beam_energy_eV=4.0e9,
            particle_charge_C=ELECTRON_CHARGE_C,
            longitudinal_unit="m",
            sign_convention="AT"
        )

        super().__init__(
            x_min=float(x_grid.min()),
            x_max=float(x_grid.max()),
            y_min=float(y_grid.min()),
            y_max=float(y_grid.max()),
            allow_extrapolation=allow_extrapolation,
            metadata=meta,
            filepath=fp
        )

        self.length_m = length_m
        self.x_grid = x_grid
        self.y_grid = y_grid
        self.kx_map = kx_map
        self.ky_map = ky_map
        
        fill_val = None if allow_extrapolation else np.nan
        bounds_err = not allow_extrapolation
        
        # RegularGridInterpolator expects points as (y_grid, x_grid) matching matrix shape (ny, nx)
        self._interp_kx = RegularGridInterpolator((self.y_grid, self.x_grid), self.kx_map,
                                                   bounds_error=bounds_err, fill_value=fill_val)
        self._interp_ky = RegularGridInterpolator((self.y_grid, self.x_grid), self.ky_map,
                                                   bounds_error=bounds_err, fill_value=fill_val)

    def evaluate(self, x: Union[float, np.ndarray], y: Union[float, np.ndarray]) -> Tuple[Union[float, np.ndarray], Union[float, np.ndarray]]:
        """
        Evaluate raw map values (Kx, Ky) at (x, y) as stored in map file.
        
        Args:
            x: horizontal position in m
            y: vertical position in m
            
        Returns:
            Tuple of raw (Kx, Ky) values.
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

    def evaluate_kick(self, x: Union[float, np.ndarray],
                      y: Union[float, np.ndarray],
                      energy_eV: Optional[float] = None) -> Tuple[Union[float, np.ndarray], Union[float, np.ndarray]]:
        """
        Evaluate (kick_x, kick_y) kick angles in radians at position (x, y).
        
        Uses self.metadata to perform unit-safe conversion to radians.
        """
        kx_raw, ky_raw = self.evaluate(x, y)
        if self.metadata.value_type == "kick_angle":
            kick_x = convert_kick_angle(kx_raw, self.metadata.value_unit, "rad")
            kick_y = convert_kick_angle(ky_raw, self.metadata.value_unit, "rad")
        elif self.metadata.value_type == "integrated_field":
            int_bx = convert_integrated_field(kx_raw, self.metadata.value_unit, "T_m")
            int_by = convert_integrated_field(ky_raw, self.metadata.value_unit, "T_m")
            energy = energy_eV if energy_eV is not None else self.metadata.beam_energy_eV
            if energy is None:
                raise ValueError("beam_energy_eV must be provided in metadata or as argument")
            kick_x, kick_y = integrated_field_to_transverse_kicks(
                int_bx_t_m=int_bx,
                int_by_t_m=int_by,
                beam_energy_eV=energy,
                particle_charge_C=self.metadata.particle_charge_C,
                coordinate_convention=self.metadata.sign_convention
            )
        else:
            raise ValueError(f"Cannot evaluate kick angle directly from value_type '{self.metadata.value_type}'")
        return kick_x, kick_y

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
        
        - Kx (Section 1 in kickmap_file) exhibits odd symmetry in x: Kx(-x, y) = -Kx(x, y)
        - Ky (Section 2 in kickmap_file) exhibits odd symmetry in y: Ky(x, -y) = -Ky(x, y)
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
        energy_eV = energy_GeV * 1e9
        kx_rad, ky_rad = self.evaluate_kick(x_offset_m, 0.0, energy_eV=energy_eV)
        kx_raw, ky_raw = self.evaluate(x_offset_m, 0.0)
        
        return {
            "x_offset_mm": x_offset_m * 1e3,
            "kx_value": float(kx_raw),
            "ky_value": float(ky_raw),
            "kx_rad": float(kx_rad),
            "ky_rad": float(ky_rad),
            "kx_mrad": float(kx_rad * 1e3),
            "ky_mrad": float(ky_rad * 1e3),
            "sign_verified": bool(kx_rad < 0 if x_offset_m < 0 else kx_rad > 0),
        }
