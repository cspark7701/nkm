#!/usr/bin/env python3
"""
Task 05 Validation Script — End-to-End BTS to Storage-Ring Coupling

Couples booster extraction distribution through BTS transport line to storage-ring multi-turn tracking.
Compares Baseline BTS vs. Optimized BTS vs. Local Twiss distribution injection performance.

Outputs machine-readable metrics and figures under results/end_to_end/task05_run_<timestamp>/.
"""

import sys
import json
import yaml
import datetime
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.nkm.end_to_end import (
    BoosterExtractionConfig,
    generate_booster_extraction_distribution,
    run_end_to_end_pipeline
)
from src.nkm.bts_lattice import BTSConfig, create_bts_lattice
from src.nkm.storage_ring_injection import StorageRingInjectionConfig
from src.nkm.kickmap import NKMKickMap2D
from src.nkm.paper import set_publication_style, PUBLICATION_COLORS


def run_task05_validation() -> dict:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = repo_root / "results" / "end_to_end" / f"task05_run_{timestamp}"
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    set_publication_style(font_size=10, dpi=300)

    # 1. Configs
    booster_cfg = BoosterExtractionConfig(n_particles=1000, seed=42)
    bts_baseline_cfg = BTSConfig()
    
    # Optimized BTS config (matching tuned quadrupole gradients)
    bts_opt_cfg = BTSConfig(
        k_q11=0.4850, k_q12=-1.0500, k_q13=0.9120,
        k_q21=-1.0200, k_q22=1.4200, k_q23=-0.6500,
        k_q31=0.5500, k_q32=-1.1200, k_q33=0.9100
    )
    ring_cfg = StorageRingInjectionConfig()

    kickmap_path = repo_root / "kickmap_file.txt"
    kmap_2d = NKMKickMap2D(kickmap_path) if kickmap_path.is_file() else None

    # 2. Run Baseline BTS End-to-End Pipeline
    pipe_baseline = run_end_to_end_pipeline(
        booster_config=booster_cfg,
        bts_config=bts_baseline_cfg,
        ring_config=ring_cfg,
        n_turns=10,
        kicker_model="fieldmap" if kmap_2d else "ideal",
        kickmap_obj=kmap_2d
    )

    # 3. Run Optimized BTS End-to-End Pipeline
    pipe_opt = run_end_to_end_pipeline(
        booster_config=booster_cfg,
        bts_config=bts_opt_cfg,
        ring_config=ring_cfg,
        n_turns=10,
        kicker_model="fieldmap" if kmap_2d else "ideal",
        kickmap_obj=kmap_2d
    )

    # 4. Save Config YAML & BTS Exit Distribution NPZ
    config_dict = {
        "timestamp": timestamp,
        "booster_extraction": booster_cfg.__dict__,
        "bts_baseline": bts_baseline_cfg.__dict__,
        "bts_optimized": bts_opt_cfg.__dict__,
        "storage_ring_injection": ring_cfg.__dict__
    }
    with open(output_dir / "config.yaml", "w") as f:
        yaml.dump(config_dict, f, default_flow_style=False)

    np.savez_compressed(
        output_dir / "bts_exit_distribution.npz",
        baseline_exit_beam=pipe_baseline["bts_exit_beam"],
        optimized_exit_beam=pipe_opt["bts_exit_beam"],
        handoff_s_position_m=28.5,
        coordinate_units="meters_radians"
    )

    # 5. Save BTS Metrics JSON
    bts_metrics = {
        "baseline_bts": {
            "transmission_fraction": pipe_baseline["bts_transmission"],
            "losses_count": pipe_baseline["bts_losses_count"],
            "exit_centroid_x_mm": pipe_baseline["bts_exit_stats"]["centroid"]["x_mm"] if pipe_baseline["bts_exit_stats"]["centroid"] else 0.0,
            "exit_emittance_x_mrad": pipe_baseline["bts_exit_stats"]["emittance_x_mrad"]
        },
        "optimized_bts": {
            "transmission_fraction": pipe_opt["bts_transmission"],
            "losses_count": pipe_opt["bts_losses_count"],
            "exit_centroid_x_mm": pipe_opt["bts_exit_stats"]["centroid"]["x_mm"] if pipe_opt["bts_exit_stats"]["centroid"] else 0.0,
            "exit_emittance_x_mrad": pipe_opt["bts_exit_stats"]["emittance_x_mrad"]
        }
    }
    with open(output_dir / "bts_metrics.json", "w") as f:
        json.dump(bts_metrics, f, indent=2)

    # 6. Save Injection Metrics JSON
    res_base_ring = pipe_baseline["ring_tracking_result"]
    res_opt_ring = pipe_opt["ring_tracking_result"]
    res_local_ring = pipe_baseline["local_tracking_result"]

    injection_metrics = {
        "baseline_bts_handoff": {
            "survived_particles": res_base_ring.survived_particles,
            "capture_efficiency": res_base_ring.survival_fraction,
            "end_to_end_efficiency": pipe_baseline["overall_end_to_end_efficiency"],
            "total_injection_losses": len(res_base_ring.loss_log)
        },
        "optimized_bts_handoff": {
            "survived_particles": res_opt_ring.survived_particles,
            "capture_efficiency": res_opt_ring.survival_fraction,
            "end_to_end_efficiency": pipe_opt["overall_end_to_end_efficiency"],
            "total_injection_losses": len(res_opt_ring.loss_log)
        },
        "idealized_local_twiss": {
            "survived_particles": res_local_ring.survived_particles,
            "capture_efficiency": res_local_ring.survival_fraction,
            "total_injection_losses": len(res_local_ring.loss_log)
        }
    }
    with open(output_dir / "injection_metrics.json", "w") as f:
        json.dump(injection_metrics, f, indent=2)

    # 7. Save Handoff Validation JSON
    handoff_validation = {
        "handoff_element": "SEPTUM / NKM_INLET",
        "handoff_s_position_m": 28.5,
        "coordinate_convention": "AT (x: meters, xp: radians, y: meters, yp: radians, delta: dp/p)",
        "septum_injection_offset_m": ring_cfg.septum_x_offset_m,
        "handoff_valid": bool(pipe_baseline["bts_transmission"] > 0.90 and res_opt_ring.survival_fraction > 0.90)
    }
    with open(output_dir / "handoff_validation.json", "w") as f:
        json.dump(handoff_validation, f, indent=2)

    # --------------------------------------------------------------------------
    # Figure 1: BTS Exit Phase Space Handoff (x-xp)
    # --------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x_base = pipe_baseline["bts_exit_beam"][0, :] * 1e3
    xp_base = pipe_baseline["bts_exit_beam"][1, :] * 1e3
    x_opt = pipe_opt["bts_exit_beam"][0, :] * 1e3
    xp_opt = pipe_opt["bts_exit_beam"][1, :] * 1e3

    ax.scatter(x_base, xp_base, s=10, color=PUBLICATION_COLORS["beta_y"], alpha=0.6, label="Baseline BTS Exit")
    ax.scatter(x_opt, xp_opt, s=10, color=PUBLICATION_COLORS["beta_x"], alpha=0.6, label="Optimized BTS Exit")
    ax.set_xlabel("Horizontal Position $x$ [mm]")
    ax.set_ylabel("Horizontal Angle $x'$ [mrad]")
    ax.set_title("BTS Exit Handoff Phase Space Distribution ($s = 28.5$ m)")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right")

    fig1_path = figures_dir / "fig1_bts_phase_space_handoff.png"
    fig.savefig(fig1_path, dpi=300)
    plt.close(fig)

    # --------------------------------------------------------------------------
    # Figure 2: Turn-by-Turn Multi-Turn Survival Comparison
    # --------------------------------------------------------------------------
    turns = list(range(1, 11))
    surv_base = res_base_ring.survival_history
    surv_opt = res_opt_ring.survival_history
    surv_local = res_local_ring.survival_history

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(turns, surv_base, "o-", color=PUBLICATION_COLORS["beta_y"], label="Baseline BTS Handoff")
    ax.plot(turns, surv_opt, "s--", color=PUBLICATION_COLORS["beta_x"], label="Optimized BTS Handoff")
    ax.plot(turns, surv_local, "^:", color=PUBLICATION_COLORS["stored"], label="Idealized Local Twiss")
    ax.set_xlabel("Storage Ring Turn Number")
    ax.set_ylabel("Surviving Particles")
    ax.set_title("Multi-Turn Storage Ring Particle Survival Comparison")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="lower left")

    fig2_path = figures_dir / "fig2_multiturn_survival_comparison.png"
    fig.savefig(fig2_path, dpi=300)
    plt.close(fig)

    # --------------------------------------------------------------------------
    # Figure 3: Storage Ring Phase Space Evolution Across Turns
    # --------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 4.5))
    beam_final = res_opt_ring.particles_6d
    valid_mask = ~np.isnan(beam_final[0, :])

    ax.scatter(beam_final[0, valid_mask] * 1e3, beam_final[1, valid_mask] * 1e3, s=12, color=PUBLICATION_COLORS["dispersion"], label=f"Turn 10 Captured Beam (N={int(np.sum(valid_mask))})")
    ax.axvline(-16.0, color="red", linestyle="--", label="Septum Sheet (-16 mm)")
    ax.set_xlabel("Horizontal Position $x$ [mm]")
    ax.set_ylabel("Horizontal Angle $x'$ [mrad]")
    ax.set_title("Captured Injected Beam Phase Space at Turn 10")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right")

    fig3_path = figures_dir / "fig3_storage_ring_phase_space_turns.png"
    fig.savefig(fig3_path, dpi=300)
    plt.close(fig)

    summary_metrics = {
        "output_directory": str(output_dir),
        "bts_baseline_transmission": pipe_baseline["bts_transmission"],
        "bts_optimized_transmission": pipe_opt["bts_transmission"],
        "injection_capture_baseline": res_base_ring.survival_fraction,
        "injection_capture_optimized": res_opt_ring.survival_fraction,
        "injection_capture_idealized": res_local_ring.survival_fraction,
        "end_to_end_efficiency_baseline": pipe_baseline["overall_end_to_end_efficiency"],
        "end_to_end_efficiency_optimized": pipe_opt["overall_end_to_end_efficiency"],
        "generated_figures": [str(fig1_path), str(fig2_path), str(fig3_path)],
        "all_checks_passed": bool(pipe_baseline["bts_transmission"] > 0.90 and res_opt_ring.survival_fraction > 0.90)
    }

    return summary_metrics


if __name__ == "__main__":
    res = run_task05_validation()
    print("=== Task 05 End-to-End BTS-to-Storage-Ring Validation Summary ===")
    print(f"Output Directory            : {res['output_directory']}")
    print(f"BTS Baseline Transmission  : {res['bts_baseline_transmission']:.2%}")
    print(f"BTS Optimized Transmission : {res['bts_optimized_transmission']:.2%}")
    print(f"Injection Capture (Base)   : {res['injection_capture_baseline']:.2%}")
    print(f"Injection Capture (Opt)    : {res['injection_capture_optimized']:.2%}")
    print(f"End-to-End Efficiency (Opt): {res['end_to_end_efficiency_optimized']:.2%}")
    print(f"All Checks Passed           : {res['all_checks_passed']}")
