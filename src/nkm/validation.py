"""
NKM Cross-Validation and Field Integration Module

Provides functions for cross-validating 1D field maps, 2D kick maps,
analytical 4-wire kicker models (nlk.py), and particle tracking integration.
"""

import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
import numpy as np

from .units import (
    KickMapMetadata,
    compute_rigidity,
    integrated_field_to_kick,
    ELECTRON_CHARGE_C
)
from .fieldmap import NKMFieldMap1D, load_1d_fieldmap, OutOfDomainError
from .kickmap import NKMKickMap2D
from .tracking import track_nkm_thin_kick, track_nkm_rk4
import nlk


def get_input_data_hashes(repo_root: Optional[Union[str, Path]] = None) -> Dict[str, str]:
    """
    Calculate SHA-256 hashes for all scientific source data files.
    """
    if repo_root is None:
        root = Path(__file__).resolve().parent.parent.parent
    else:
        root = Path(repo_root)

    target_files = [
        "By.txt",
        "nkm_field.xlsx",
        "kickmap_file.txt",
        "nlk.py"
    ]

    hashes = {}
    for filename in target_files:
        filepath = root / filename
        if filepath.is_file():
            hasher = hashlib.sha256()
            with open(filepath, 'rb') as f:
                hasher.update(f.read())
            hashes[filename] = hasher.hexdigest()
        else:
            hashes[filename] = "FILE_NOT_FOUND"

    return hashes


def compute_cross_validation(x_positions_m: np.ndarray,
                            repo_root: Optional[Union[str, Path]] = None,
                            energy_GeV: float = 4.0,
                            length_m: float = 0.525) -> Dict[str, Any]:
    """
    Perform cross-validation across 5 representation paths at specified transverse positions:
    1. 1D field map (By.txt) integrated field & kick
    2. Spreadsheet field map (nkm_field.xlsx) integrated field & kick
    3. 2D kick map (kickmap_file.txt)
    4. Analytical model (nlk.py)
    5. Single-particle tracking (RK4 and Thin Kick)

    Args:
        x_positions_m: Array of horizontal positions in meters.
        repo_root: Repository root path.
        energy_GeV: Beam energy in GeV.
        length_m: NKM length in meters.

    Returns:
        Dictionary containing comparison tables, residuals, and tolerances.
    """
    if repo_root is None:
        root = Path(__file__).resolve().parent.parent.parent
    else:
        root = Path(repo_root)

    energy_eV = energy_GeV * 1e9
    brho = compute_rigidity(energy_eV, ELECTRON_CHARGE_C)

    # 1. Load 1D field map (By.txt)
    by_path = root / "By.txt"
    x_by, by_vals = load_1d_fieldmap(by_path)
    fmap_1d = NKMFieldMap1D(x_by, by_vals)

    # 2. Load spreadsheet field map (nkm_field.xlsx)
    excel_path = root / "nkm_field.xlsx"
    x_ex, by_ex = load_1d_fieldmap(excel_path)
    fmap_excel = NKMFieldMap1D(x_ex, by_ex)

    # 3. Load 2D kick map (kickmap_file.txt)
    kick_path = root / "kickmap_file.txt"
    kmap_2d = NKMKickMap2D(kick_path)

    # 4. Initialize analytical model (nlk.py)
    wire_x = np.array([0.0053, -0.0053, -0.0053, 0.0053])
    wire_y = np.array([0.0053, 0.0053, -0.0053, -0.0053])
    wire_currents = np.array([-3000.0, -3000.0, -3000.0, -3000.0])
    nlk_model = nlk.Kicker(wire_x, wire_y, wire_currents)

    results_by_pos = []

    for x_m in x_positions_m:
        x_mm = x_m * 1e3

        # Path 1: 1D field map
        by_1d = float(fmap_1d.evaluate(x_m))
        int_field_1d = by_1d * length_m  # T*m
        kick_1d_mrad = float(fmap_1d.compute_integrated_kick(x_m, length_m, energy_GeV))

        # Path 2: Spreadsheet field map (nkm_field.xlsx domain [0, 24.3mm], even symmetry)
        try:
            abs_x = abs(x_m)
            if abs_x <= fmap_excel.x_max:
                by_ex_val = float(fmap_excel.evaluate(abs_x))
                kick_ex_mrad = float(fmap_excel.compute_integrated_kick(abs_x if x_m >= 0 else -abs_x, length_m, energy_GeV))
            else:
                kick_ex_mrad = None
        except OutOfDomainError:
            kick_ex_mrad = None

        # Path 3: 2D kick map
        kx_2d_rad, _ = kmap_2d.evaluate_kick(x_m, 0.0, energy_eV=energy_eV)
        kick_2d_mrad = float(kx_2d_rad * 1e3)

        # Path 4: Analytical nlk.py model
        _, by_nlk = nlk_model.get_field(x_m, 0.0)
        _, ky_nlk = nlk_model.get_kick(x_m, 0.0, brho, length_m)
        kick_nlk_mrad = float(ky_nlk * 1e3)

        # Path 5: Tracking (Thin kick & RK4)
        particle_in = np.zeros((6, 1))
        particle_in[0, 0] = x_m

        particle_thin = track_nkm_thin_kick(
            particle_in,
            kmap_2d.evaluate,
            scale_factor=1.0,
            length_m=length_m,
            energy_GeV=energy_GeV
        )
        kick_thin_mrad = float(particle_thin[1, 0] * 1e3)

        def field_fn_1d(x_arr):
            return fmap_1d.evaluate(x_arr)

        particle_rk4 = track_nkm_rk4(
            particle_in,
            field_fn_1d,
            length_m=length_m,
            n_steps=50,
            energy_GeV=energy_GeV
        )
        kick_rk4_mrad = float(particle_rk4[1, 0] * 1e3)

        res = {
            "x_mm": x_mm,
            "x_m": x_m,
            "kick_1d_mrad": kick_1d_mrad,
            "kick_excel_mrad": kick_ex_mrad,
            "kick_2d_mrad": kick_2d_mrad,
            "kick_nlk_mrad": kick_nlk_mrad,
            "kick_tracking_thin_mrad": kick_thin_mrad,
            "kick_tracking_rk4_mrad": kick_rk4_mrad,
            "diff_2d_vs_thin_mrad": abs(kick_2d_mrad - kick_thin_mrad),
            "diff_1d_vs_rk4_mrad": abs(kick_1d_mrad - kick_rk4_mrad),
            "diff_2d_vs_nlk_mrad": abs(kick_2d_mrad - kick_nlk_mrad)
        }
        results_by_pos.append(res)

    return {
        "energy_GeV": energy_GeV,
        "brho_Tm": brho,
        "length_m": length_m,
        "positions": results_by_pos,
        "hashes": get_input_data_hashes(root)
    }


def perform_interpolation_study(by_txt_path: Union[str, Path], x_test: np.ndarray) -> Dict[str, Any]:
    """
    Compare linear vs. cubic interpolation on 1D field map across x_test positions.
    """
    x_by, by_vals = load_1d_fieldmap(by_txt_path)
    fmap = NKMFieldMap1D(x_by, by_vals)

    by_linear = fmap.evaluate(x_test, method='linear')
    by_cubic = fmap.evaluate(x_test, method='cubic')

    diff = np.abs(by_linear - by_cubic)

    return {
        "max_diff_T": float(np.max(diff)),
        "mean_diff_T": float(np.mean(diff)),
        "x_test_mm": (x_test * 1e3).tolist(),
        "diff_T": diff.tolist()
    }


def perform_grid_convergence_study(by_txt_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Study convergence of trapezoidal field integration over varying sampling resolutions.
    """
    x_by, by_vals = load_1d_fieldmap(by_txt_path)
    fmap = NKMFieldMap1D(x_by, by_vals)

    grid_sizes = [21, 51, 101, 201, 401, 1001]
    int_fields = []

    for n in grid_sizes:
        x_grid = np.linspace(fmap.x_min, fmap.x_max, n)
        by_grid = fmap.evaluate(x_grid)
        trapz = getattr(np, "trapezoid", getattr(np, "trapz", None))
        int_val = float(trapz(by_grid, x_grid))
        int_fields.append(int_val)

    # Reference value with fine grid
    ref_val = int_fields[-1]
    errors = [abs(val - ref_val) for val in int_fields]

    return {
        "grid_sizes": grid_sizes,
        "integrated_fields_Tm": int_fields,
        "errors_Tm": errors,
        "converged_ref_Tm": ref_val
    }


def perform_linearity_study(kmap_2d: NKMKickMap2D, x_test_m: float = -0.016) -> Dict[str, Any]:
    """
    Verify field-scale linearity of kicks under amplitude scaling factors.
    """
    scale_factors = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5]
    particle_in = np.zeros((6, 1))
    particle_in[0, 0] = x_test_m

    kicks_mrad = []
    for scale in scale_factors:
        tracked = track_nkm_thin_kick(
            particle_in,
            kmap_2d.evaluate,
            scale_factor=scale,
            length_m=kmap_2d.length_m,
            energy_GeV=4.0
        )
        kicks_mrad.append(float(tracked[1, 0] * 1e3))

    nominal_kick = kicks_mrad[4]  # scale = 1.0
    expected_kicks = [scale * nominal_kick for scale in scale_factors]
    max_linearity_error = float(np.max(np.abs(np.array(kicks_mrad) - np.array(expected_kicks))))

    return {
        "scale_factors": scale_factors,
        "kicks_mrad": kicks_mrad,
        "expected_kicks_mrad": expected_kicks,
        "max_linearity_error_mrad": max_linearity_error
    }
