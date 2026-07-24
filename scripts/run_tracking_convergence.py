#!/usr/bin/env python3
"""
Task 03 — Thick-Element NKM Tracking Convergence Study Script

Evaluates tracking convergence across slice counts N_slices = [10, 20, 40, 80, 160]
for reference particle trajectories, beam centroids, RMS sizes, projected emittances,
loss fractions, and stored beam perturbations.
"""

import sys
import json
import datetime
from pathlib import Path
import numpy as np

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.nkm.units import compute_rigidity
from src.nkm.fieldmap import NKMFieldMap1D, load_1d_fieldmap
from src.nkm.beam import generate_6d_beam, compute_beam_statistics
from src.nkm.tracking import track_nkm_thick_symplectic, track_nkm_thick_rk4


def main():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = repo_root / "results" / "field_validation" / f"tracking_convergence_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=== NKM Thick-Element Tracking Convergence Study ===")
    print(f"Output directory: {output_dir}")

    # Load 1D field map By.txt
    by_path = repo_root / "By.txt"
    x_by, by_vals = load_1d_fieldmap(by_path)
    fmap = NKMFieldMap1D(x_by, by_vals)

    def field_fn(x, y, z):
        by = fmap.evaluate(x)
        bx = np.zeros_like(x)
        return by, bx

    slice_counts = [10, 20, 40, 80, 160]
    length_m = 0.525
    energy_GeV = 4.0

    # 1. Single reference particle at nominal injection offset x = -16.0 mm
    ref_in = np.zeros((6, 1))
    ref_in[0, 0] = -0.016

    # 2. Injected beam distribution (1000 particles)
    beam_inj_in = generate_6d_beam(
        n_particles=1000,
        beta_x=10.0, alpha_x=0.0, emit_x=1e-7,
        beta_y=5.0, alpha_y=0.0, emit_y=1e-8,
        x_offset=-0.016,
        seed=42
    )

    # 3. Stored beam reference at x = 0.0 mm
    stored_in = np.zeros((6, 1))

    results_by_slice = []

    for n_slices in slice_counts:
        # Track reference injected particle
        ref_out = track_nkm_thick_symplectic(ref_in, field_fn, length_m=length_m, n_slices=n_slices, energy_GeV=energy_GeV)
        ref_x_exit_mm = float(ref_out[0, 0] * 1e3)
        ref_xp_exit_mrad = float(ref_out[1, 0] * 1e3)

        # Track injected beam distribution
        beam_inj_out = track_nkm_thick_symplectic(beam_inj_in, field_fn, length_m=length_m, n_slices=n_slices, energy_GeV=energy_GeV)
        inj_stats = compute_beam_statistics(beam_inj_out)

        # Track stored beam reference
        stored_out = track_nkm_thick_symplectic(stored_in, field_fn, length_m=length_m, n_slices=n_slices, energy_GeV=energy_GeV)
        stored_kick_mrad = float(stored_out[1, 0] * 1e3)

        res = {
            "n_slices": n_slices,
            "ref_x_exit_mm": ref_x_exit_mm,
            "ref_xp_exit_mrad": ref_xp_exit_mrad,
            "inj_centroid_x_mm": inj_stats["centroid"]["x_mm"],
            "inj_centroid_xp_mrad": inj_stats["centroid"]["xp_mrad"],
            "inj_rms_x_mm": inj_stats["std_dev"]["sigma_x_mm"],
            "inj_emitt_x_mrad": inj_stats["emittance_x_mrad"],
            "inj_survival_fraction": inj_stats["survival_fraction"],
            "stored_kick_mrad": stored_kick_mrad
        }
        results_by_slice.append(res)
        print(f"N_slices={n_slices:3d}: Exit xp={ref_xp_exit_mrad:8.5f} mrad | Stored kick={stored_kick_mrad:8.5e} mrad")

    summary_output = {
        "timestamp": timestamp,
        "slice_counts": slice_counts,
        "results": results_by_slice,
        "recommended_production_slices": 40
    }

    json_path = output_dir / "tracking_convergence_summary.json"
    with open(json_path, 'w') as f:
        json.dump(summary_output, f, indent=2)
    print(f"Saved summary JSON: {json_path}")


if __name__ == "__main__":
    main()
