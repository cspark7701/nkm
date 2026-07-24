#!/usr/bin/env python3
"""
Task 02 — Independent NKM Field and Kick Cross-Validation Script

Performs cross-validation across all NKM field map, kick map, analytical,
and tracking representations, generates diagnostic plots, and saves results
to results/field_validation/<run-id>/.
"""

import sys
import json
import datetime
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.nkm.units import compute_rigidity
from src.nkm.fieldmap import NKMFieldMap1D, load_1d_fieldmap
from src.nkm.kickmap import NKMKickMap2D
from src.nkm.validation import (
    get_input_data_hashes,
    compute_cross_validation,
    perform_interpolation_study,
    perform_grid_convergence_study,
    perform_linearity_study
)


def main():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = repo_root / "results" / "field_validation" / f"run_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== NKM Field & Kick Cross-Validation ===")
    print(f"Output directory: {output_dir}")

    # Positions to compare
    x_positions = np.array([0.0, -0.010, -0.016, 0.016, 0.040])
    x_dense = np.linspace(-0.048, 0.048, 201)

    # 1. Compute cross-validation metrics
    cross_val = compute_cross_validation(x_positions, repo_root=repo_root)

    # 2. Perform numerical studies
    by_path = repo_root / "By.txt"
    interp_study = perform_interpolation_study(by_path, x_dense)
    grid_study = perform_grid_convergence_study(by_path)

    kick_path = repo_root / "kickmap_file.txt"
    kmap_2d = NKMKickMap2D(kick_path)
    linearity_study = perform_linearity_study(kmap_2d, x_test_m=-0.016)
    sym_study = kmap_2d.compute_symmetry_residuals()

    # Save JSON summary
    summary_data = {
        "timestamp": timestamp,
        "hashes": cross_val["hashes"],
        "cross_validation": cross_val,
        "interpolation_study": {
            "max_diff_T": interp_study["max_diff_T"],
            "mean_diff_T": interp_study["mean_diff_T"]
        },
        "grid_convergence": {
            "grid_sizes": grid_study["grid_sizes"],
            "errors_Tm": grid_study["errors_Tm"]
        },
        "linearity_study": linearity_study,
        "symmetry_residuals": sym_study
    }

    json_path = output_dir / "field_validation_summary.json"
    with open(json_path, 'w') as f:
        json.dump(summary_data, f, indent=2)
    print(f"Saved summary JSON: {json_path}")

    # 3. Generate plots
    # Figure 1: Field profiles & Kick profiles comparison across x
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Evaluate profiles over x_dense
    fmap_1d = NKMFieldMap1D(*load_1d_fieldmap(by_path))
    by_1d_dense = fmap_1d.evaluate(x_dense)
    kick_1d_dense = [fmap_1d.compute_integrated_kick(x) for x in x_dense]
    kick_2d_dense = [kmap_2d.evaluate_kick(x, 0.0)[0] * 1e3 for x in x_dense]

    ax1.plot(x_dense * 1e3, by_1d_dense, 'b-', label='1D Field B_y (By.txt)')
    ax1.set_xlabel('x [mm]')
    ax1.set_ylabel('B_y [T]')
    ax1.set_title('Vertical Field Profile B_y(x)')
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend()

    ax2.plot(x_dense * 1e3, kick_1d_dense, 'b-', label='1D Integrated Kick')
    ax2.plot(x_dense * 1e3, kick_2d_dense, 'r--', label='2D Kick Map (kickmap_file.txt)')
    ax2.axvline(-16.0, color='g', linestyle=':', label='Injected Beam (-16mm)')
    ax2.axvline(0.0, color='k', linestyle=':', label='Stored Beam Axis (0mm)')
    ax2.set_xlabel('x [mm]')
    ax2.set_ylabel('Kick Angle [mrad]')
    ax2.set_title('Horizontal Deflection Kick Profile \Delta x\'(x)')
    ax2.grid(True, linestyle='--', alpha=0.6)
    ax2.legend()

    fig.tight_layout()
    fig1_path = output_dir / "kick_profile_comparison.png"
    fig.savefig(fig1_path, dpi=300)
    plt.close(fig)
    print(f"Saved figure: {fig1_path}")

    # Figure 2: Convergence & Linearity
    fig2, (ax3, ax4) = plt.subplots(1, 2, figsize=(14, 5))

    ax3.plot(grid_study["grid_sizes"], grid_study["errors_Tm"], 'bo-')
    ax3.set_xscale('log')
    ax3.set_yscale('log')
    ax3.set_xlabel('Grid Resolution N')
    ax3.set_ylabel('Integration Error [T m]')
    ax3.set_title('Longitudinal Grid Integration Convergence')
    ax3.grid(True, which='both', linestyle='--', alpha=0.6)

    ax4.plot(linearity_study["scale_factors"], linearity_study["kicks_mrad"], 'ro-', label='Tracked Kick')
    ax4.plot(linearity_study["scale_factors"], linearity_study["expected_kicks_mrad"], 'k--', label='Linear Scaling')
    ax4.set_xlabel('Field Scaling Factor')
    ax4.set_ylabel('Kick Angle [mrad]')
    ax4.set_title('Field-Scale Linearity at x = -16 mm')
    ax4.grid(True, linestyle='--', alpha=0.6)
    ax4.legend()

    fig2.tight_layout()
    fig2_path = output_dir / "convergence_and_linearity.png"
    fig2.savefig(fig2_path, dpi=300)
    plt.close(fig2)
    print(f"Saved figure: {fig2_path}")

    print("Validation script completed successfully.")


if __name__ == "__main__":
    main()
