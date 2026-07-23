#!/usr/bin/env python3
"""
NKM Field Map Validation & Processing Script for Milestone 3

Loads NKM field map spreadsheets and text files, validates finite bounds,
quantifies symmetry residuals, fits polynomial field profiles, and generates validation plots.
Outputs saved to results/fieldmap/ and docs/validation/.
"""

import json
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.nkm.fieldmap import (
    load_1d_fieldmap,
    validate_1d_fieldmap,
    NKMFieldMap1D,
    OutOfDomainError
)
from src.nkm.kickmap import (
    load_2d_kickmap,
    NKMKickMap2D
)

OUTPUT_DIR = REPO_ROOT / "results" / "fieldmap"
PLOT_PATH = OUTPUT_DIR / "nkm_fieldmap_comparison.png"
METRICS_JSON = OUTPUT_DIR / "fieldmap_validation_metrics.json"


def run_fieldmap_validation():
    """Execute field map validation pipeline."""
    # 1. Load and validate 1D By.txt
    by_txt_path = REPO_ROOT / "By.txt"
    x_1d, by_1d = load_1d_fieldmap(by_txt_path)
    val_1d = validate_1d_fieldmap(x_1d, by_1d)
    
    fmap_1d = NKMFieldMap1D(x_1d, by_1d)
    coeffs, fit_residual = fmap_1d.fit_polynomial(degree=5)
    
    # 2. Load and validate 2D kickmap_file.txt
    kick_txt_path = REPO_ROOT / "kickmap_file.txt"
    kmap_2d = NKMKickMap2D(kick_txt_path)
    grid_interp_err = kmap_2d.verify_grid_interpolation()
    sym_2d = kmap_2d.compute_symmetry_residuals()
    lorentz_test = kmap_2d.verify_lorentz_kick_sign(x_offset_m=-0.010)
    
    # 3. Create plots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Plot 1: 1D field profile along x
    x_dense = np.linspace(fmap_1d.x_min, fmap_1d.x_max, 500)
    by_dense = fmap_1d.evaluate(x_dense, method='cubic')
    
    ax1.plot(x_1d * 1e3, by_1d, 'ro', label='Source Data (By.txt)', markersize=4, alpha=0.6)
    ax1.plot(x_dense * 1e3, by_dense, 'b-', label='Cubic Interpolation', linewidth=1.5)
    ax1.set_xlabel('x [mm]')
    ax1.set_ylabel(r'$B_y$ [T]')
    ax1.set_title('NKM Horizontal Field Profile')
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend()
    
    # Plot 2: 2D integrated kick contour
    X_grid, Y_grid = np.meshgrid(kmap_2d.x_grid * 1e3, kmap_2d.y_grid * 1e3)
    cs = ax2.contourf(X_grid, Y_grid, kmap_2d.kx_map, levels=20, cmap='Spectral_r')
    fig.colorbar(cs, ax=ax2, label=r'$\int B_y ds$ [T$\cdot$m]')
    ax2.set_xlabel('x [mm]')
    ax2.set_ylabel('y [mm]')
    ax2.set_title('NKM 2D Integrated Kick Map')
    ax2.grid(True, linestyle=':', alpha=0.4)
    
    plt.tight_layout()
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(PLOT_PATH, dpi=300)
    
    # 4. Save metrics JSON
    metrics_summary = {
        "1d_fieldmap_validation": val_1d,
        "1d_polyfit": {
            "degree": 5,
            "coefficients": [float(c) for c in coeffs],
            "max_residual_T": float(fit_residual)
        },
        "2d_kickmap_validation": {
            "length_m": kmap_2d.length_m,
            "grid_size": [len(kmap_2d.x_grid), len(kmap_2d.y_grid)],
            "x_range_mm": [kmap_2d.x_min * 1e3, kmap_2d.x_max * 1e3],
            "y_range_mm": [kmap_2d.y_min * 1e3, kmap_2d.y_max * 1e3],
            "grid_interpolation_max_err": float(grid_interp_err),
            "symmetry_residuals": sym_2d,
            "lorentz_kick_test": lorentz_test
        }
    }
    
    with open(METRICS_JSON, "w") as f:
        json.dump(metrics_summary, f, indent=2)
        
    print("=== NKM Field Map Validation Summary ===")
    print(f"1D Field Map Valid: {val_1d['valid']}")
    print(f"1D Peak By: {val_1d['peak_by_T']:.6f} T")
    print(f"2D Grid Interp Max Error: {grid_interp_err:.3e}")
    print(f"2D Kx Odd Symmetry Residual: {sym_2d['kx_odd_x_symmetry_residual']:.3e}")
    print(f"Lorentz Kick at x=-10mm Kx: {lorentz_test['kx_value']:.4f}")
    print(f"Plot saved to: {PLOT_PATH}")
    print(f"Metrics saved to: {METRICS_JSON}")


if __name__ == "__main__":
    run_fieldmap_validation()
