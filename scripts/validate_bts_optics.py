#!/usr/bin/env python3
"""
BTS Lattice & Optics Validation Script for Milestone 2

Executes lattice health checks, transfer matrix symplecticity calculations,
uncoupled Twiss propagation, plane-by-plane mismatch metrics, and generates optics plots.
Saves outputs to results/optics_validation/ and docs/validation/.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.nkm.bts_lattice import BTSConfig, create_bts_lattice, validate_bts_lattice
from src.nkm.optics import (
    compute_bts_optics_metrics,
    compute_mismatch_metric,
    plot_bts_optics
)

OUTPUT_DIR = REPO_ROOT / "results" / "optics_validation"
PLOT_PATH = OUTPUT_DIR / "bts_optics_functions.png"
METRICS_JSON = OUTPUT_DIR / "optics_validation_metrics.json"


def run_validation():
    """Run Milestone 2 optics validation."""
    config = BTSConfig()
    lattice = create_bts_lattice(config)
    
    # 1. Lattice health and symplecticity check
    lattice_val = validate_bts_lattice(lattice)
    
    # 2. Optics propagation and mismatch calculation
    initial_twiss = {
        'beta': [7.560000, 12.269000],
        'alpha': [1.5231000, -1.654700],
        'dispersion': [0.2762000, -0.0657000, 0.0, 0.0]
    }
    
    # Storage ring injection target optics (from storage ring lattice at NKM reference point)
    # Target values from bts.ipynb cell 35/36:
    # Scale modified target used in notebook test:
    # betax_inj = 23.3, betay_inj = 4.25 (approx storage ring values)
    # mod target: betax = 0.1 * betax_inj = 2.33, alphax = 0.1 * alphax_inj
    target_twiss = {
        'beta': [2.336495, 4.256241],
        'alpha': [-0.016335, 0.017772],
        'dispersion': [0.080868, 0.047472, 0.0, 0.0]
    }
    
    optics_res = compute_bts_optics_metrics(lattice, initial_twiss, target_twiss)
    
    # 3. Generate optics plot
    plot_bts_optics(lattice, initial_twiss, output_path=PLOT_PATH)
    
    # 4. Save JSON metrics
    summary_data = {
        "lattice_validation": lattice_val,
        "optics_metrics": {
            "mismatch_x": optics_res["mismatch_x"],
            "mismatch_y": optics_res["mismatch_y"],
            "dispersion_x_residual_m": optics_res["dispersion_x_residual_m"],
            "final_beta_x_m": optics_res["final_beta_x"],
            "final_beta_y_m": optics_res["final_beta_y"],
            "target_beta_x_m": optics_res["target_beta_x"],
            "target_beta_y_m": optics_res["target_beta_y"],
            "max_beta_x_m": optics_res["propagation"]["max_beta_x"],
            "max_beta_y_m": optics_res["propagation"]["max_beta_y"],
            "max_dispersion_x_m": optics_res["propagation"]["max_dispersion_x"],
        }
    }
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(METRICS_JSON, "w") as f:
        json.dump(summary_data, f, indent=2)
        
    print("=== BTS Optics Validation Summary ===")
    print(f"All Lattice Health Checks Passed: {lattice_val['all_checks_passed']}")
    print(f"Total BTS Length: {lattice_val['total_length_m']:.3f} m")
    print(f"Total Bend Angle: {lattice_val['total_bend_angle_deg']:.3f} deg")
    print(f"Symplecticity Error M44: {lattice_val['symplecticity_error_m44']:.3e}")
    print(f"Symplecticity Error M66: {lattice_val['symplecticity_error_m66']:.3e}")
    print(f"Horizontal Mismatch Mx: {optics_res['mismatch_x']:.4f}")
    print(f"Vertical Mismatch My:   {optics_res['mismatch_y']:.4f}")
    print(f"Plot saved to: {PLOT_PATH}")
    print(f"Metrics saved to: {METRICS_JSON}")


if __name__ == "__main__":
    run_validation()
