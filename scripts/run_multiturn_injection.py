#!/usr/bin/env python3
"""
Task 04 — Multi-Turn Storage Ring Injection Simulation Script

Simulates multi-turn storage ring injection dynamics across 4 kicker models
(NKM Off, Ideal Kicker, Linearized NKM, RADIA Fieldmap NKM), evaluates physical
capture efficiency, stored beam perturbation, and outputs JSON metrics under
results/multiturn_injection/run_<timestamp>/.
"""

import sys
import json
import datetime
from pathlib import Path
import numpy as np

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.nkm.storage_ring_injection import (
    StorageRingInjectionConfig,
    load_storage_ring_injection_lattice,
    track_multiturn_injection,
    compute_multiturn_injection_metrics
)
from src.nkm.beam import generate_6d_beam
from src.nkm.kickmap import NKMKickMap2D


def main():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = repo_root / "results" / "multiturn_injection" / f"run_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=== NKM Multi-Turn Storage Ring Injection Simulation ===")
    print(f"Output directory: {output_dir}")

    config = StorageRingInjectionConfig()
    ring, nkm_idx = load_storage_ring_injection_lattice(config)
    print(f"Loaded storage ring lattice: {len(ring)} elements, NKM at index {nkm_idx}")

    kick_path = repo_root / "kickmap_file.txt"
    kickmap_obj = NKMKickMap2D(kick_path)

    # 100 particles, 10 turns for fast verification
    n_particles = 100
    n_turns = 10

    injected_beam = generate_6d_beam(
        n_particles=n_particles,
        beta_x=10.0, alpha_x=0.0, emit_x=1e-7,
        beta_y=5.0, alpha_y=0.0, emit_y=1e-8,
        x_offset=-0.016,
        seed=42
    )

    stored_beam = generate_6d_beam(
        n_particles=n_particles,
        beta_x=10.0, alpha_x=0.0, emit_x=1e-8,
        beta_y=5.0, alpha_y=0.0, emit_y=1e-9,
        x_offset=0.0,
        seed=42
    )

    models = ["off", "ideal", "linear", "fieldmap"]
    model_summaries = {}

    for model in models:
        inj_res = track_multiturn_injection(
            injected_beam, ring, n_turns=n_turns,
            kicker_model=model, kickmap_obj=kickmap_obj,
            config=config
        )

        stored_res = track_multiturn_injection(
            stored_beam, ring, n_turns=n_turns,
            kicker_model=model, kickmap_obj=kickmap_obj,
            config=config
        )

        metrics = compute_multiturn_injection_metrics(inj_res, stored_res, config)
        model_summaries[model] = metrics

        print(f"Model [{model:8s}]: Capture Efficiency = {metrics['capture_efficiency']*100:.1f}%, Stored Osc = {metrics['stored_beam_centroid_oscillation_mm']:.4f} mm")

    # Injected offset scan (-20 mm to -10 mm)
    offset_scan_results = []
    offsets_mm = np.linspace(-20.0, -10.0, 5)

    for off_mm in offsets_mm:
        scan_beam = generate_6d_beam(
            n_particles=50,
            beta_x=10.0, alpha_x=0.0, emit_x=1e-7,
            beta_y=5.0, alpha_y=0.0, emit_y=1e-8,
            x_offset=off_mm * 1e-3,
            seed=42
        )
        scan_inj = track_multiturn_injection(
            scan_beam, ring, n_turns=n_turns,
            kicker_model="fieldmap", kickmap_obj=kickmap_obj,
            config=config
        )
        scan_stored = track_multiturn_injection(
            stored_beam[:50], ring, n_turns=n_turns,
            kicker_model="fieldmap", kickmap_obj=kickmap_obj,
            config=config
        )
        scan_metrics = compute_multiturn_injection_metrics(scan_inj, scan_stored, config)
        offset_scan_results.append({
            "offset_mm": float(off_mm),
            "capture_efficiency": scan_metrics["capture_efficiency"]
        })

    summary_data = {
        "timestamp": timestamp,
        "n_particles": n_particles,
        "n_turns": n_turns,
        "model_summaries": model_summaries,
        "offset_scan": offset_scan_results
    }

    json_path = output_dir / "multiturn_injection_summary.json"
    with open(json_path, 'w') as f:
        json.dump(summary_data, f, indent=2)
    print(f"Saved summary JSON: {json_path}")


if __name__ == "__main__":
    main()
