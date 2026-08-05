"""
NKM 1D Field Map Ingestion and Validation Module

Provides read-only loading, validation, interpolation, and symmetry analysis
for 1D magnetic field maps (e.g. nkm_field.xlsx, nkm_field_expanded.xlsx, By.txt).
"""

from pathlib import Path
from typing import Dict, Tuple, Optional, Any, Union
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from .units import KickMapMetadata, compute_rigidity, convert_coordinate, convert_kick_angle


import hashlib


class OutOfDomainError(ValueError):
    """Raised when querying field values outside tabulated bounds."""
    pass


class BaseFieldMap:
    """
    Abstract Base Class for 1D and 2D Magnetic Field & Kick Map Evaluators.
    
    Provides common domain bounds checking, file integrity verification (SHA-256),
    metadata handling, and symmetry evaluation interfaces.
    """
    def __init__(self,
                 x_min: float,
                 x_max: float,
                 y_min: Optional[float] = None,
                 y_max: Optional[float] = None,
                 allow_extrapolation: bool = False,
                 metadata: Optional[KickMapMetadata] = None,
                 filepath: Optional[Union[str, Path]] = None):
        self.x_min = float(x_min)
        self.x_max = float(x_max)
        self.y_min = float(y_min) if y_min is not None else None
        self.y_max = float(y_max) if y_max is not None else None
        self.allow_extrapolation = allow_extrapolation
        self.metadata = metadata
        self.filepath = Path(filepath) if filepath else None

    def check_domain_bounds(self,
                            x: Union[float, np.ndarray],
                            y: Optional[Union[float, np.ndarray]] = None) -> None:
        """
        Validate whether (x, y) coordinates fall within tabulated map domain bounds.
        
        Raises OutOfDomainError if points fall outside domain bounds and allow_extrapolation is False.
        """
        if self.allow_extrapolation:
            return

        x_arr = np.asarray(x)
        out_x = (x_arr < self.x_min) | (x_arr > self.x_max)
        if np.any(out_x):
            raise OutOfDomainError(
                f"x values out of range [{self.x_min}, {self.x_max}]: {x_arr[out_x]}"
            )

        if y is not None and self.y_min is not None and self.y_max is not None:
            y_arr = np.asarray(y)
            out_y = (y_arr < self.y_min) | (y_arr > self.y_max)
            if np.any(out_y):
                raise OutOfDomainError(
                    f"y values out of range [{self.y_min}, {self.y_max}]: {y_arr[out_y]}"
                )

    def compute_file_hash(self, filepath: Optional[Union[str, Path]] = None, algorithm: str = "sha256") -> str:
        """
        Compute cryptographic hash (default SHA-256) of the map file.
        """
        target_path = Path(filepath) if filepath else self.filepath
        if not target_path or not target_path.is_file():
            raise FileNotFoundError(f"Map file path not found: {target_path}")

        hasher = hashlib.new(algorithm)
        with open(target_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def verify_file_hash(self, expected_hash: str, algorithm: str = "sha256") -> bool:
        """
        Verify that map file hash matches an expected hash checksum string.
        """
        computed = self.compute_file_hash(algorithm=algorithm)
        return computed.lower() == expected_hash.lower()

    @property
    def domain_bounds(self) -> Dict[str, Tuple[float, float]]:
        """Return dict of domain bounds for x (and y if applicable)."""
        bounds = {"x": (self.x_min, self.x_max)}
        if self.y_min is not None and self.y_max is not None:
            bounds["y"] = (self.y_min, self.y_max)
        return bounds


def integrate_longitudinal_field(z: np.ndarray,
                                 by: np.ndarray,
                                 method: str = "simpson") -> float:
    """
    Perform direct 1D numerical quadrature along longitudinal axis z (in meters)
    to calculate integrated magnetic field I_y = integral B_y(z) dz in T*m.
    
    Args:
        z: Longitudinal position array in meters (must be sorted).
        by: Magnetic field component array B_y(z) in Tesla.
        method: Numerical integration method ('simpson' or 'trapezoid').
        
    Returns:
        Integrated field I_y in T*m.
    """
    if len(z) != len(by):
        raise ValueError("z and by arrays must have equal length")
    if len(z) < 2:
        raise ValueError("At least 2 points required for numerical quadrature")

    z_arr = np.asarray(z, dtype=float)
    by_arr = np.asarray(by, dtype=float)

    if method == "simpson":
        try:
            from scipy.integrate import simpson
            int_val = float(simpson(y=by_arr, x=z_arr))
        except ImportError:
            from scipy.integrate import simps
            int_val = float(simps(y=by_arr, x=z_arr))
    elif method == "trapezoid":
        try:
            from scipy.integrate import trapezoid
            int_val = float(trapezoid(y=by_arr, x=z_arr))
        except ImportError:
            int_val = float(np.trapz(y=by_arr, x=z_arr))
    else:
        raise ValueError(f"Unsupported numerical integration method: '{method}'")

    return int_val


def load_1d_fieldmap(filepath: Union[str, Path],
                    x_col: str = "x",
                    by_col: str = "By") -> Tuple[np.ndarray, np.ndarray]:
    """
    Load a 1D field map from an Excel or text file in read-only mode.
    
    Args:
        filepath: Path to spreadsheet (.xlsx) or CSV/text (.txt) file.
        x_col: Name or index of horizontal position column (m).
        by_col: Name or index of vertical magnetic field column (T).
        
    Returns:
        Tuple of (x_array, by_array) in meters and Tesla.
    """
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(f"Field map file not found: {path}")
        
    ext = path.suffix.lower()
    if ext in ('.xlsx', '.xls'):
        df = pd.read_excel(path)
        if x_col in df.columns and by_col in df.columns:
            x = df[x_col].values.astype(float)
            by = df[by_col].values.astype(float)
        else:
            x = df.iloc[:, 0].values.astype(float)
            by = df.iloc[:, 1].values.astype(float)
    elif ext in ('.txt', '.csv'):
        # Attempt space/csv delimiter
        try:
            df = pd.read_csv(path, sep=r'\s+', header=None)
        except Exception:
            df = pd.read_csv(path, header=None)
        x = df.iloc[:, 0].values.astype(float)
        by = df.iloc[:, 1].values.astype(float)
    else:
        raise ValueError(f"Unsupported field map extension: {ext}")
        
    # Sort by x coordinate
    sort_idx = np.argsort(x)
    return x[sort_idx], by[sort_idx]


def validate_1d_fieldmap(x: np.ndarray, by: np.ndarray) -> Dict[str, Any]:
    """
    Perform rigorous numerical and symmetry checks on a 1D field map.
    
    Returns:
        Dictionary of validation metrics.
    """
    is_finite_x = bool(np.all(np.isfinite(x)))
    is_finite_by = bool(np.all(np.isfinite(by)))
    
    # Check duplicates
    has_duplicates = bool(len(x) != len(np.unique(x)))
    
    # Check monotonicity
    dx = np.diff(x)
    is_strictly_monotonic = bool(np.all(dx > 0))
    
    # Range
    x_min, x_max = float(np.min(x)), float(np.max(x))
    by_min, by_max = float(np.min(by)), float(np.max(by))
    peak_by = float(np.max(np.abs(by)))
    
    # Symmetry metric (odd or even symmetry check around x=0)
    if x_min < 0 and x_max > 0:
        pos_mask = (x > 0) & (x <= min(abs(x_min), abs(x_max)))
        x_pos = x[pos_mask]
        by_pos = by[pos_mask]
        
        by_neg_interp = np.interp(-x_pos, x, by)
        odd_sym_residual = float(np.max(np.abs(by_pos + by_neg_interp)))
        even_sym_residual = float(np.max(np.abs(by_pos - by_neg_interp)))
    else:
        odd_sym_residual = None
        even_sym_residual = None
        
    all_passed = is_finite_x and is_finite_by and is_strictly_monotonic and not has_duplicates
    
    return {
        "valid": all_passed,
        "n_samples": len(x),
        "x_range_m": [x_min, x_max],
        "by_range_T": [by_min, by_max],
        "peak_by_T": peak_by,
        "is_strictly_monotonic": is_strictly_monotonic,
        "has_duplicates": has_duplicates,
        "odd_symmetry_residual_T": odd_sym_residual,
        "even_symmetry_residual_T": even_sym_residual,
    }


class NKMFieldMap1D(BaseFieldMap):
    """
    1D NKM Field Map Interpolator with strict domain checking, explicit metadata, and integrated kick utilities.
    """
    def __init__(self, x: np.ndarray, by: np.ndarray,
                 allow_extrapolation: bool = False,
                 metadata: Optional[KickMapMetadata] = None,
                 filepath: Optional[Union[str, Path]] = None):
        val = validate_1d_fieldmap(x, by)
        if not val["valid"]:
            raise ValueError(f"Invalid 1D field map data: {val}")
            
        meta = metadata or KickMapMetadata(
            coordinate_unit="m",
            value_type="field",
            value_unit="T",
            beam_energy_eV=4.0e9
        )

        super().__init__(
            x_min=float(x.min()),
            x_max=float(x.max()),
            allow_extrapolation=allow_extrapolation,
            metadata=meta,
            filepath=filepath
        )
        
        self.x = x
        self.by = by
        
        fill_val = "extrapolate" if allow_extrapolation else np.nan
        self._interp_linear = interp1d(x, by, kind='linear', bounds_error=False, fill_value=fill_val)
        self._interp_cubic = interp1d(x, by, kind='cubic', bounds_error=False, fill_value=fill_val)

    def evaluate(self, x_eval: Union[float, np.ndarray], method: str = 'linear') -> Union[float, np.ndarray]:
        """
        Evaluate interpolated field B_y at x_eval.
        
        Raises OutOfDomainError if points are outside bounds and allow_extrapolation is False.
        """
        self.check_domain_bounds(x_eval)
            
        interp_fn = self._interp_cubic if method == 'cubic' else self._interp_linear
        res = interp_fn(x_eval)
        
        if np.ndim(x_eval) == 0:
            return float(res)
        return res

    def compute_integrated_kick(self, x_pos: float, length_m: float = 0.525, energy_GeV: float = 4.0) -> float:
        """
        Calculate horizontal kick angle Delta x' in mrad for a particle at position x_pos.
        
        Delta x' = (q / p0) * B_y(x) * L
        """
        by_val = self.evaluate(x_pos)
        energy_eV = energy_GeV * 1e9
        charge_C = self.metadata.particle_charge_C if self.metadata else -1.602176634e-19
        brho = compute_rigidity(energy_eV, charge_C)
        charge_sign = float(np.sign(charge_C))
        kick_rad = charge_sign * (by_val * length_m) / brho
        return float(kick_rad * 1e3)  # mrad

    def fit_polynomial(self, degree: int = 5) -> Tuple[np.ndarray, float]:
        """
        Fit a polynomial of given degree to B_y(x) and return coefficients and max residual.
        """
        coeffs = np.polyfit(self.x, self.by, degree)
        fit_vals = np.polyval(coeffs, self.x)
        max_residual = float(np.max(np.abs(self.by - fit_vals)))
        return coeffs, max_residual
