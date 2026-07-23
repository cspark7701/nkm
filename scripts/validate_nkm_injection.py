#!/usr/bin/env python3
"""
NKM Injection Simulation & Validation Script for Milestone 5

Simulates 6D injected and circulating beam tracking through the BTS exit,
into the NKM, and evaluates 3 models (NKM Off, Idealized, Field-Map NKM).
Performs field scale and offset scans, and exports figures/metrics to results/injection/.
"""

import json
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.nkm.beam import generate_6d_beam, compute_beam_statistics
from src.nkm.kickmap import NKMKickMap2D
from src.nkm.injection import simulate_nkm_models

OUTPUT_DIR = REPO_ROOT / "results" / "injection"
PLOT_PATH = OUTPUT_DIR / "nkm_injection_phasespace.png"
METRICS_JSON = OUTPUT_DIR / "injection_validation_metrics.json"


def run_injection_validation():
    """Run Milestone 5 injection tracking validation."""
    print("=== Starting NKM Injection Tracking Validation ===", flush=True)
    
    # 1. Load validated 2D Kick Map
    kick_path = REPO_ROOT / "kickmap_file.txt"
    kmap_2d = NKMKickMap2D(kick_path)
    
    # 2. Generate 6D Circulating Beam (centered at x=0, y=0)
    # Storage ring Twiss parameters at NKM: beta_x = 2.336 m, beta_y = 4.256 m
    circ_beam = generate_6d_beam(
        n_particles=1000,
        beta_x=2.336495, alpha_x=-0.016335, emit_x=10.89e-9,
        beta_y=4.256241, alpha_y=0.017772, emit_y=10.89e-9,
        x_offset=0.0, xp_offset=0.0, seed=42
    )
    
    # 3. Generate 6D Injected Beam (offset at x = -5.7 mm, xp = +3.0 mrad)
    inj_beam = generate_6d_beam(
        n_particles=1000,
        beta_x=7.560000, alpha_x=1.523100, emit_x=10.89e-9,
        beta_y=12.26900, alpha_y=-1.65470, emit_y=10.89e-9,
        x_offset=-5.7e-3, xp_offset=3.0e-3, seed=42
    )
    
    # 4. Simulate 3 Models
    sim_res = simulate_nkm_models(inj_beam, circ_beam, kmap_2d, energy_GeV=4.0)
    
    # 5. Field Scale Scan (Limiting cases check: scale=0.0, 0.5, 1.0, 1.2)
    scale_scan_results = []
    for scale in [0.0, 0.5, 1.0, 1.2]:
        res_scale = simulate_nkm_models(inj_beam, circ_beam, kmap_2d, scale_factor=scale)
        scale_scan_results.append({
            "scale_factor": scale,
            "injected_kick_mrad": res_scale["performance_metrics"]["injected_kick_mrad"],
            "stored_beam_kick_mrad": res_scale["performance_metrics"]["stored_beam_kick_mrad"],
            "beam_separation_mm": res_scale["performance_metrics"]["beam_separation_mm"],
        })
        
    # 6. Generate Phase-Space Plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    inj_out = sim_res["beams"]["inj_fieldmap"]
    circ_out = sim_res["beams"]["circ_fieldmap"]
    
    # Horizontal Phase Space
    ax1.scatter(inj_beam[0, :] * 1e3, inj_beam[1, :] * 1e3, s=3, c='red', alpha=0.4, label='Injected Beam @ Entrance')
    ax1.scatter(inj_out[0, :] * 1e3, inj_out[1, :] * 1e3, s=3, c='darkred', alpha=0.7, label='Injected Beam @ Exit')
    ax1.scatter(circ_beam[0, :] * 1e3, circ_beam[1, :] * 1e3, s=3, c='blue', alpha=0.4, label='Circulating Beam @ Entrance')
    ax1.scatter(circ_out[0, :] * 1e3, circ_out[1, :] * 1e3, s=3, c='navy', alpha=0.7, label='Circulating Beam @ Exit')
    
    ax1.set_xlabel('x [mm]')
    ax1.set_ylabel(r"x' [mrad]")
    ax1.set_title('Horizontal Phase Space through NKM')
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='upper right')
    
    # Vertical Phase Space
    ax2.scatter(inj_beam[2, :] * 1e3, inj_beam[3, :] * 1e3, s=3, c='orange', alpha=0.4, label='Injected Beam @ Entrance')
    ax2.scatter(inj_out[2, :] * 1e3, inj_out[3, :] * 1e3, s=3, c='darkorange', alpha=0.7, label='Injected Beam @ Exit')
    ax2.scatter(circ_beam[2, :] * 1e3, circ_beam[3, :] * 1e3, s=3, c='cyan', alpha=0.4, label='Circulating Beam @ Entrance')
    ax2.scatter(circ_out[2, :] * 1e3, circ_out[3, :] * 1e3, s=3, c='teal', alpha=0.7, label='Circulating Beam @ Exit')
    
    ax2.set_xlabel('y [mm]')
    ax2.set_ylabel(r"y' [mrad]")
    ax2.set_title('Vertical Phase Space through NKM')
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='upper right')
    
    plt.tight_layout()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(PLOT_PATH, dpi=300)
    
    # 7. Save JSON Metrics
    metrics_summary = {
        "models_summary": sim_res["models"],
        "performance_metrics": sim_res["performance_metrics"],
        "field_scale_scan": scale_scan_results,
    }
    
    # Remove large beam array objects from JSON export
    if "beams" in metrics_summary:
        del metrics_summary["beams"]
        
    with open(METRICS_JSON, "w") as f:
        json.dump(metrics_summary, f, indent=2)
        
    print("\n=== NKM Injection Tracking Validation Summary ===")
    print(f"Injected Beam Kick: {sim_res['performance_metrics']['injected_kick_mrad']:.4f} mrad")
    print(f"Stored Beam Perturbation: {sim_res['performance_metrics']['stored_beam_kick_mrad']:.4f} mrad")
    print(f"Beam Separation at NKM Exit: {sim_res['performance_metrics']['beam_separation_mm']:.4f} mm")
    print(f"Injected Particle Survival: {sim_res['performance_metrics']['injected_survival_fraction'] * 100:.1f}%")
    print(f"Plot saved to: {PLOT_PATH}")
    print(f"Metrics saved to: {METRICS_JSON}")


if __name__ == "__main__":
    run_injection_validation()
