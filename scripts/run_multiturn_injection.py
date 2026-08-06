#!/usr/bin/env python3
"""
Task 06 — Converged Multi-Turn Storage Ring Injection Study Script

Produces numerically defensible injected-beam capture and stored-beam perturbation
results for publication. Evaluates 4 NKM models across smoke / pilot / production tiers.

Usage:
    python3 scripts/run_multiturn_injection.py [--tier smoke|pilot|production] [--output-dir DIR]

Output directory layout:
    results/multiturn_injection/run_<timestamp>/
        config.json                        # full simulation configuration
        convergence_particle_count.json    # particle-count convergence scan
        convergence_turn_count.json        # turn-count convergence scan
        model_<name>_results.json          # per-model ensemble metrics
        injection_metrics_summary.json     # combined summary table
        figures/
            fig1_capture_efficiency_ci.png
            fig2_first_loss_turn_distribution.png
            fig3_turn_survival_curves.png
            fig4_stored_beam_perturbation.png
            fig5_injection_acceptance.png
"""

import argparse
import json
import sys
import datetime
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.nkm.convergence_study import (
    smoke_config,
    pilot_config,
    production_config,
    bootstrap_capture_ci,
    particle_count_convergence_scan,
    turn_count_convergence_scan,
    compute_first_loss_turn_distribution,
    compute_stored_beam_perturbation,
    compute_injection_acceptance,
    run_ensemble_study,
)
from src.nkm.storage_ring_injection import (
    StorageRingInjectionConfig,
    load_storage_ring_injection_lattice,
    track_multiturn_injection,
)
from src.nkm.beam import generate_6d_beam
from src.nkm.kickmap import NKMKickMap2D
from src.nkm.paper import set_publication_style, PUBLICATION_COLORS


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(description="NKM Multi-Turn Injection Convergence Study")
    parser.add_argument("--tier", choices=["smoke", "pilot", "production"], default="smoke",
                        help="Simulation tier: smoke (CI), pilot (dev), production (pub).")
    parser.add_argument("--output-dir", type=Path, default=None,
                        help="Override output directory path.")
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = parse_args()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    output_dir = args.output_dir or (
        repo_root / "results" / "multiturn_injection" / f"run_{timestamp}"
    )
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    # Select simulation tier
    if args.tier == "smoke":
        tier = smoke_config()
    elif args.tier == "pilot":
        tier = pilot_config()
    else:
        tier = production_config()

    print(f"=== NKM Multi-Turn Injection Convergence Study ===")
    print(f"Tier         : {tier.label}")
    print(f"Particles    : {tier.n_particles}")
    print(f"Turns        : {tier.n_turns}")
    print(f"NKM Slices   : {tier.n_slices}")
    print(f"Seeds        : {tier.seeds}")
    print(f"Output       : {output_dir}")

    set_publication_style(font_size=10, dpi=300)

    # Load lattice
    config = StorageRingInjectionConfig()
    ring, nkm_idx = load_storage_ring_injection_lattice(config)

    kick_path = repo_root / "kickmap_file.txt"
    kickmap_obj = NKMKickMap2D(kick_path) if kick_path.is_file() else None

    # Save config JSON
    config_dict = {
        "timestamp": timestamp,
        "tier": {
            "label": tier.label,
            "n_particles": tier.n_particles,
            "n_turns": tier.n_turns,
            "n_slices": tier.n_slices,
            "seeds": tier.seeds,
        },
        "injection_config": {
            "energy_eV": config.energy_eV,
            "nkm_length_m": config.nkm_length_m,
            "septum_x_offset_m": config.septum_x_offset_m,
            "septum_thickness_m": config.septum_thickness_m,
            "aperture_x_m": config.aperture_x_m,
            "aperture_y_m": config.aperture_y_m,
        },
        "lattice_elements": len(ring),
        "nkm_element_index": nkm_idx,
        "kickmap_available": kickmap_obj is not None,
    }
    with open(output_dir / "config.json", "w") as f:
        json.dump(config_dict, f, indent=2)

    # -----------------------------------------------------------------------
    # Convergence Scans (using pilot particle/turn counts as reference limits)
    # -----------------------------------------------------------------------
    print("\n--- Particle Count Convergence Scan ---")
    # Convergence scans use a small representative particle count (N=20) and turn count (N=5)
    # to detect capture-rate trends across the grid; physics claims are made from the
    # multi-seed ensemble below. Increase CONV_N_PARTICLES to 50+ for pilot/production tiers.
    if tier.label == "smoke":
        np_scan_values = [20, 50, 100]
        np_scan_turns = 5
        nt_scan_values = [2, 5, 10]
        conv_n_particles = 20
    elif tier.label == "pilot":
        np_scan_values = [100, 300, 500, 1000]
        np_scan_turns = 10
        nt_scan_values = [10, 50, 100]
        conv_n_particles = 100
    else:  # production
        np_scan_values = [500, 1000, 2000, 5000, 10000]
        np_scan_turns = 20
        nt_scan_values = [10, 50, 100, 200, 500]
        conv_n_particles = 200

    kicker_for_convergence = "fieldmap" if kickmap_obj else "ideal"

    np_conv = particle_count_convergence_scan(
        n_particle_values=np_scan_values,
        n_turns=np_scan_turns,
        ring=ring,
        kicker_model=kicker_for_convergence,
        kickmap_obj=kickmap_obj,
        config=config,
        seed=42
    )
    for row in np_conv:
        print(f"  N_part={row['n_particles']:6d}: capture = {row['capture_efficiency']:.4f}")
    with open(output_dir / "convergence_particle_count.json", "w") as f:
        json.dump(np_conv, f, indent=2)

    print("\n--- Turn Count Convergence Scan ---")
    nt_conv = turn_count_convergence_scan(
        n_turn_values=nt_scan_values,
        n_particles=conv_n_particles,
        ring=ring,
        kicker_model=kicker_for_convergence,
        kickmap_obj=kickmap_obj,
        config=config,
        seed=42
    )
    for row in nt_conv:
        print(f"  N_turns={row['n_turns']:5d}: capture = {row['capture_efficiency']:.4f}")
    with open(output_dir / "convergence_turn_count.json", "w") as f:
        json.dump(nt_conv, f, indent=2)

    # -----------------------------------------------------------------------
    # Multi-Seed Ensemble per Kicker Model
    # -----------------------------------------------------------------------
    models = ["off", "ideal", "linear", "fieldmap"]
    all_model_results: dict = {}

    print("\n--- Multi-Seed Ensemble Injection Study ---")
    for model in models:
        model_kmap = kickmap_obj if model == "fieldmap" else None
        print(f"  Running kicker model: {model} ...", flush=True)
        res = run_ensemble_study(
            tier=tier,
            ring=ring,
            kicker_model=model,
            kickmap_obj=model_kmap,
            config=config,
            stored_beam_n_particles=min(tier.n_particles, 1000)
        )
        all_model_results[model] = res
        ci = res["capture_efficiency_ci"]
        pert = res["mean_stored_perturbation"]
        print(f"    Capture: {ci['mean']:.4f} [{ci['ci_lo']:.4f}, {ci['ci_hi']:.4f}] 95% CI | "
              f"Stored osc: {pert.get('centroid_oscillation_x_mm', float('nan')):.4f} mm")

        with open(output_dir / f"model_{model}_results.json", "w") as f:
            json.dump(res, f, indent=2, default=str)

    # -----------------------------------------------------------------------
    # Injection Acceptance Scan
    # -----------------------------------------------------------------------
    print("\n--- Injection Acceptance Scan ---")
    x_off_scan = np.linspace(-0.022, -0.010, 7)
    acceptance_data = compute_injection_acceptance(
        x_offsets_m=x_off_scan,
        n_particles=min(tier.n_particles, 500),
        n_turns=min(tier.n_turns, 20),
        ring=ring,
        kicker_model=kicker_for_convergence,
        kickmap_obj=kickmap_obj,
        config=config,
        seed=42
    )
    for row in acceptance_data:
        print(f"  x_offset={row['x_offset_mm']:.1f} mm: capture = {row['capture_efficiency']:.4f}")
    with open(output_dir / "injection_acceptance.json", "w") as f:
        json.dump(acceptance_data, f, indent=2)

    # -----------------------------------------------------------------------
    # Combined Summary Metrics Table
    # -----------------------------------------------------------------------
    summary_rows = []
    for model, res in all_model_results.items():
        ci = res["capture_efficiency_ci"]
        pert = res["mean_stored_perturbation"]
        fld = res["first_loss_distribution"] or {}
        summary_rows.append({
            "kicker_model": model,
            "tier": tier.label,
            "n_particles": tier.n_particles,
            "n_turns": tier.n_turns,
            "n_seeds": len(tier.seeds),
            "capture_mean": ci["mean"],
            "capture_ci_lo": ci["ci_lo"],
            "capture_ci_hi": ci["ci_hi"],
            "capture_ci_level": ci["ci_level"],
            "stored_centroid_osc_mm": pert.get("centroid_oscillation_x_mm", float("nan")),
            "stored_emittance_growth_x_pct": pert.get("emittance_growth_x_percent", float("nan")),
            "stored_emittance_growth_y_pct": pert.get("emittance_growth_y_percent", float("nan")),
            "mean_first_loss_turn": fld.get("mean_first_loss_turn", float("nan")),
            "fraction_lost_turn1": fld.get("fraction_lost_on_turn_1", float("nan")),
        })
    with open(output_dir / "injection_metrics_summary.json", "w") as f:
        json.dump(summary_rows, f, indent=2, default=str)

    # -----------------------------------------------------------------------
    # Figures
    # -----------------------------------------------------------------------
    model_labels = list(all_model_results.keys())
    colors = [PUBLICATION_COLORS.get("beta_x"), PUBLICATION_COLORS.get("beta_y"),
               PUBLICATION_COLORS.get("stored"), PUBLICATION_COLORS.get("dispersion")]
    colors = colors[:len(model_labels)]

    # Fig 1: Capture efficiency + 95% CI bar chart
    fig, ax = plt.subplots(figsize=(7, 4))
    for i, (model, res) in enumerate(all_model_results.items()):
        ci = res["capture_efficiency_ci"]
        err_lo = ci["mean"] - ci["ci_lo"]
        err_hi = ci["ci_hi"] - ci["mean"]
        ax.bar(i, ci["mean"], color=colors[i], alpha=0.8,
               yerr=[[err_lo], [err_hi]], capsize=6, error_kw={"linewidth": 1.5})
        ax.text(i, ci["mean"] + err_hi + 0.01, f"{ci['mean']:.3f}", ha="center", fontsize=8)
    ax.set_xticks(range(len(model_labels)))
    ax.set_xticklabels(model_labels, fontsize=9)
    ax.set_ylabel("Capture Efficiency")
    ax.set_title(f"Injection Capture Efficiency ± 95% CI  [{tier.label} tier, {tier.n_particles} particles, {tier.n_turns} turns]")
    ax.set_ylim(0, 1.15)
    ax.grid(axis="y", linestyle=":", alpha=0.6)
    fig.tight_layout()
    fig.savefig(figures_dir / "fig1_capture_efficiency_ci.png", dpi=300)
    plt.close(fig)

    # Fig 2: First-loss turn distribution histogram (fieldmap or best-available model)
    best_model = "fieldmap" if kickmap_obj else "ideal"
    fld = all_model_results[best_model].get("first_loss_distribution") or {}
    hist = fld.get("turn_histogram", {})
    if hist:
        turns_all = sorted(int(k) for k in hist.keys())
        counts = [hist[str(t)] if str(t) in hist else hist.get(t, 0) for t in turns_all]
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(turns_all, counts, color=PUBLICATION_COLORS.get("beta_x"), alpha=0.75)
        ax.set_xlabel("Turn Number")
        ax.set_ylabel("Number of First Losses")
        ax.set_title(f"First-Loss Turn Distribution  [{best_model} model]")
        ax.grid(axis="y", linestyle=":", alpha=0.5)
        fig.tight_layout()
        fig.savefig(figures_dir / "fig2_first_loss_turn_distribution.png", dpi=300)
        plt.close(fig)

    # Fig 3: Turn-by-turn survival curves for all models (seed 0 only)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for i, (model, res) in enumerate(all_model_results.items()):
        seed0 = res["per_seed_results"][0]
        # Re-run seed 0 to get survival_history
        beam_fig = generate_6d_beam(
            n_particles=min(tier.n_particles, 500),
            beta_x=10.0, alpha_x=0.0, emit_x=1e-7,
            beta_y=5.0, alpha_y=0.0, emit_y=1e-8,
            x_offset=config.septum_x_offset_m, seed=tier.seeds[0]
        )
        track_res = track_multiturn_injection(
            beam_fig, ring, n_turns=tier.n_turns,
            kicker_model=model,
            kickmap_obj=(kickmap_obj if model == "fieldmap" else None),
            config=config
        )
        turns_axis = range(1, len(track_res.survival_history) + 1)
        ax.plot(turns_axis, track_res.survival_history, label=model, color=colors[i], linewidth=1.5)
    ax.set_xlabel("Storage Ring Turn")
    ax.set_ylabel("Surviving Particles")
    ax.set_title("Turn-by-Turn Particle Survival — NKM Model Comparison")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(linestyle=":", alpha=0.5)
    fig.tight_layout()
    fig.savefig(figures_dir / "fig3_turn_survival_curves.png", dpi=300)
    plt.close(fig)

    # Fig 4: Stored-beam centroid oscillation & emittance growth
    osc_vals = [all_model_results[m]["mean_stored_perturbation"].get("centroid_oscillation_x_mm", 0.0) for m in model_labels]
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(range(len(model_labels)), osc_vals, color=[PUBLICATION_COLORS.get("stored")] * len(model_labels), alpha=0.8)
    ax.set_xticks(range(len(model_labels)))
    ax.set_xticklabels(model_labels, fontsize=9)
    ax.set_ylabel("Max Stored Beam Centroid Oscillation [mm]")
    ax.set_title("Stored-Beam Horizontal Centroid Perturbation")
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    for bar, val in zip(bars, osc_vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.001,
                f"{val:.3f}", ha="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(figures_dir / "fig4_stored_beam_perturbation.png", dpi=300)
    plt.close(fig)

    # Fig 5: Injection acceptance scan
    x_off_mm = [row["x_offset_mm"] for row in acceptance_data]
    cap_eff = [row["capture_efficiency"] for row in acceptance_data]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(x_off_mm, cap_eff, "o-", color=PUBLICATION_COLORS.get("beta_x"), linewidth=2, markersize=7)
    ax.axvline(config.septum_x_offset_m * 1e3, color="red", linestyle="--", label="Design Injection Point")
    ax.set_xlabel("Injection x-offset [mm]")
    ax.set_ylabel("Capture Efficiency")
    ax.set_title(f"Injection Acceptance Window  [{kicker_for_convergence} model]")
    ax.legend(fontsize=9)
    ax.grid(linestyle=":", alpha=0.5)
    fig.tight_layout()
    fig.savefig(figures_dir / "fig5_injection_acceptance.png", dpi=300)
    plt.close(fig)

    # -----------------------------------------------------------------------
    # Print Final Summary
    # -----------------------------------------------------------------------
    print(f"\n=== Final Summary [{tier.label} tier] ===")
    print(f"{'Model':<12} {'Capture':>8} {'95%CI_Lo':>10} {'95%CI_Hi':>10} {'StorOsc(mm)':>12}")
    print("-" * 60)
    for row in summary_rows:
        print(f"{row['kicker_model']:<12} {row['capture_mean']:>8.4f} "
              f"{row['capture_ci_lo']:>10.4f} {row['capture_ci_hi']:>10.4f} "
              f"{row['stored_centroid_osc_mm']:>12.4f}")

    # Convergence evidence summary
    cap_values = [r["capture_efficiency"] for r in np_conv]
    if len(cap_values) >= 2:
        max_residual = abs(cap_values[-1] - cap_values[-2])
        print(f"\nConvergence evidence (N_part scan, last 2 steps): delta = {max_residual:.6f}")
        if max_residual < 0.001:
            print("  => CONVERGED (residual < 0.1 percentage point)")
        else:
            print("  => NOT YET CONVERGED — increase N_particles for final results")

    print(f"\nOutput directory : {output_dir}")
    print(f"Generated figures: {[f.name for f in sorted(figures_dir.glob('*.png'))]}")


if __name__ == "__main__":
    main()
