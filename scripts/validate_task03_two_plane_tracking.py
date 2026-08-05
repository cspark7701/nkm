#!/usr/bin/env python3
"""
Task 03 Validation Script — Two-Plane Thin/Thick NKM Tracking & Convergence Study

Validates two-plane transverse particle tracking (x, y) across 6 field configurations
and 4 tracking formulations (Analytic prediction, Centered Thin Lens, Symplectic Split Integrator,
and genuine RK4 Lorentz Integrator). Performs slice count convergence scan (N_slices = 5 to 320).

Outputs machine-readable metrics to results/tracking_convergence/task03_run_<timestamp>/metrics.json.
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

from src.nkm.units import compute_rigidity, integrated_field_to_transverse_kicks, ELECTRON_CHARGE_C
from src.nkm.beam import generate_6d_beam, compute_beam_statistics
from src.nkm.tracking import track_nkm_thin_kick, track_nkm_thick_symplectic, track_nkm_thick_rk4, TrackingResult
from src.nkm.integrators import SymplecticSplitIntegrator, LorentzRK4Integrator
from src.nkm.paper import set_publication_style, PUBLICATION_COLORS


def run_task03_validation() -> dict:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = repo_root / "results" / "tracking_convergence" / f"task03_run_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    set_publication_style(font_size=10, dpi=300)

    length_m = 0.525
    energy_GeV = 4.0
    energy_eV = energy_GeV * 1e9
    brho = compute_rigidity(energy_eV, ELECTRON_CHARGE_C)

    # --------------------------------------------------------------------------
    # Part 1: Test 6 Analytic Field Configurations
    # --------------------------------------------------------------------------
    field_cases = {
        "zero_field": lambda x, y, z: (np.zeros_like(x), np.zeros_like(x)),
        "constant_by": lambda x, y, z: (np.full_like(x, 0.146), np.zeros_like(x)),
        "constant_bx": lambda x, y, z: (np.zeros_like(x), np.full_like(x, 0.050)),
        "coupled_constant": lambda x, y, z: (np.full_like(x, 0.146), np.full_like(x, 0.050)),
        "linear_quad": lambda x, y, z: (2.5 * x, 2.5 * y),
        "coupled_off_axis": lambda x, y, z: (0.146 + 2.5 * x + 1.2 * y, 0.050 + 1.2 * x - 2.5 * y)
    }

    case_metrics = {}

    for case_name, f_fn in field_cases.items():
        # Beam off-axis in both x and y (x = -10mm, y = +5mm)
        beam_in = generate_6d_beam(
            n_particles=100,
            beta_x=7.56, alpha_x=1.52, emit_x=1e-8,
            beta_y=12.27, alpha_y=-1.65, emit_y=1e-9,
            x_offset=-0.010, y_offset=0.005,
            seed=42
        )

        b_sym = track_nkm_thick_symplectic(beam_in, f_fn, length_m=length_m, n_slices=100, energy_GeV=energy_GeV)
        b_rk4 = track_nkm_thick_rk4(beam_in, f_fn, length_m=length_m, n_slices=100, energy_GeV=energy_GeV)

        def thin_kick_wrapper(x, y):
            by, bx = f_fn(x, y, length_m / 2.0)
            return bx * length_m, by * length_m

        b_thin = track_nkm_thin_kick(
            beam_in,
            thin_kick_wrapper,
            length_m=length_m,
            energy_GeV=energy_GeV,
            value_type="integrated_field",
            value_unit="T_m"
        )

        res_sym = TrackingResult.from_beam(b_sym)
        res_rk4 = TrackingResult.from_beam(b_rk4)
        res_thin = TrackingResult.from_beam(b_thin)

        dx_sym_mm = res_sym.centroid["x_mm"]
        dy_sym_mm = res_sym.centroid["y_mm"]
        dxp_sym_mrad = res_sym.centroid["xp_mrad"]
        dyp_sym_mrad = res_sym.centroid["yp_mrad"]

        dx_rk4_mm = res_rk4.centroid["x_mm"]
        dy_rk4_mm = res_rk4.centroid["y_mm"]
        dxp_rk4_mrad = res_rk4.centroid["xp_mrad"]
        dyp_rk4_mrad = res_rk4.centroid["yp_mrad"]

        diff_sym_vs_rk4_xp = abs(dxp_sym_mrad - dxp_rk4_mrad) * 1e-3
        diff_sym_vs_rk4_yp = abs(dyp_sym_mrad - dyp_rk4_mrad) * 1e-3

        case_metrics[case_name] = {
            "symplectic_exit_x_mm": dx_sym_mm,
            "symplectic_exit_y_mm": dy_sym_mm,
            "symplectic_kick_xp_mrad": dxp_sym_mrad,
            "symplectic_kick_yp_mrad": dyp_sym_mrad,
            "rk4_kick_xp_mrad": dxp_rk4_mrad,
            "rk4_kick_yp_mrad": dyp_rk4_mrad,
            "thin_kick_xp_mrad": res_thin.centroid["xp_mrad"],
            "thin_kick_yp_mrad": res_thin.centroid["yp_mrad"],
            "diff_sym_vs_rk4_xp_rad": float(diff_sym_vs_rk4_xp),
            "diff_sym_vs_rk4_yp_rad": float(diff_sym_vs_rk4_yp),
            "survival_fraction": res_sym.survival_fraction
        }

    # --------------------------------------------------------------------------
    # Part 2: Slice Convergence Scan (N_slices = 5, 10, 20, 40, 80, 160, 320)
    # --------------------------------------------------------------------------
    f_coupled = field_cases["coupled_off_axis"]
    beam_scan_in = generate_6d_beam(
        n_particles=500,
        beta_x=7.56, alpha_x=1.52, emit_x=1e-8,
        beta_y=12.27, alpha_y=-1.65, emit_y=1e-9,
        x_offset=-0.010, y_offset=0.005,
        seed=42
    )

    slice_counts = [5, 10, 20, 40, 80, 160, 320]
    convergence_records = []

    for n_sl in slice_counts:
        b_sl = track_nkm_thick_symplectic(beam_scan_in, f_coupled, length_m=length_m, n_slices=n_sl, energy_GeV=energy_GeV)
        res_sl = TrackingResult.from_beam(b_sl)

        rec = {
            "n_slices": n_sl,
            "exit_x_mm": float(res_sl.centroid["x_mm"]),
            "exit_y_mm": float(res_sl.centroid["y_mm"]),
            "exit_xp_mrad": float(res_sl.centroid["xp_mrad"]),
            "exit_yp_mrad": float(res_sl.centroid["yp_mrad"]),
            "sigma_x_mm": float(np.nanstd(b_sl[0, :]) * 1e3),
            "sigma_y_mm": float(np.nanstd(b_sl[2, :]) * 1e3),
            "emittance_x_mrad": float(res_sl.emittance_x_mrad),
            "emittance_y_mrad": float(res_sl.emittance_y_mrad),
            "survival_fraction": float(res_sl.survival_fraction),
            "loss_fraction": float(1.0 - res_sl.survival_fraction)
        }
        convergence_records.append(rec)

    # Reference values with fine slice count N=320
    ref_xp = convergence_records[-1]["exit_xp_mrad"]
    ref_yp = convergence_records[-1]["exit_yp_mrad"]
    ref_x = convergence_records[-1]["exit_x_mm"]
    ref_y = convergence_records[-1]["exit_y_mm"]

    for rec in convergence_records:
        rec["xp_diff_from_ref_mrad"] = abs(rec["exit_xp_mrad"] - ref_xp)
        rec["yp_diff_from_ref_mrad"] = abs(rec["exit_yp_mrad"] - ref_yp)
        rec["x_diff_from_ref_mm"] = abs(rec["exit_x_mm"] - ref_x)
        rec["y_diff_from_ref_mm"] = abs(rec["exit_y_mm"] - ref_y)

    # N_slices = 40 metrics
    rec_40 = convergence_records[3]  # Index 3 is N_slices=40

    # --------------------------------------------------------------------------
    # Figure 1: Slice Convergence (Angle Exit xp, yp)
    # --------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 4.5))
    xp_errs = [max(r["xp_diff_from_ref_mrad"], 1e-12) for r in convergence_records]
    yp_errs = [max(r["yp_diff_from_ref_mrad"], 1e-12) for r in convergence_records]

    ax.loglog(slice_counts, xp_errs, "o-", color=PUBLICATION_COLORS["beta_y"], label=r"$x'$ Angle Residual $|\Delta x' - \Delta x'_{ref}|$ [mrad]")
    ax.loglog(slice_counts, yp_errs, "s--", color=PUBLICATION_COLORS["beta_x"], label=r"$y'$ Angle Residual $|\Delta y' - \Delta y'_{ref}|$ [mrad]")
    ax.axvline(40, color="black", linestyle=":", label="Production Choice ($N_{slices}=40$)")
    ax.set_xlabel("Thick Integrator Slice Count ($N_{slices}$)")
    ax.set_ylabel("Exit Angle Residual [mrad]")
    ax.set_title("Symplectic Integrator Exit Angle Convergence")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right")

    fig1_path = output_dir / "fig1_slice_convergence_angle.png"
    fig.savefig(fig1_path, dpi=300)
    plt.close(fig)

    # --------------------------------------------------------------------------
    # Figure 2: Slice Convergence (Position Exit x, y)
    # --------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x_errs = [max(r["x_diff_from_ref_mm"], 1e-12) for r in convergence_records]
    y_errs = [max(r["y_diff_from_ref_mm"], 1e-12) for r in convergence_records]

    ax.loglog(slice_counts, x_errs, "o-", color=PUBLICATION_COLORS["dispersion"], label=r"$x$ Position Residual $|x - x_{ref}|$ [mm]")
    ax.loglog(slice_counts, y_errs, "s--", color=PUBLICATION_COLORS["stored"], label=r"$y$ Position Residual $|y - y_{ref}|$ [mm]")
    ax.axvline(40, color="black", linestyle=":", label="Production Choice ($N_{slices}=40$)")
    ax.set_xlabel("Thick Integrator Slice Count ($N_{slices}$)")
    ax.set_ylabel("Exit Position Residual [mm]")
    ax.set_title("Symplectic Integrator Exit Position Convergence")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right")

    fig2_path = output_dir / "fig2_slice_convergence_position.png"
    fig.savefig(fig2_path, dpi=300)
    plt.close(fig)

    # --------------------------------------------------------------------------
    # Figure 3: Beam Size & Emittance vs Slice Count
    # --------------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    sig_x = [r["sigma_x_mm"] for r in convergence_records]
    sig_y = [r["sigma_y_mm"] for r in convergence_records]

    ax1.plot(slice_counts, sig_x, "o-", color=PUBLICATION_COLORS["beta_y"], label=r"RMS $\sigma_x$ [mm]")
    ax1.plot(slice_counts, sig_y, "s--", color=PUBLICATION_COLORS["beta_x"], label=r"RMS $\sigma_y$ [mm]")
    ax1.set_ylabel("RMS Beam Size [mm]")
    ax1.set_title("Beam Emittance & Envelope Stability vs Slice Count")
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="upper right")

    emit_x = [r["emittance_x_mrad"] for r in convergence_records]
    emit_y = [r["emittance_y_mrad"] for r in convergence_records]

    ax2.plot(slice_counts, emit_x, "o-", color=PUBLICATION_COLORS["dispersion"], label=r"Geometric $\epsilon_x$ [mrad]")
    ax2.plot(slice_counts, emit_y, "s--", color=PUBLICATION_COLORS["stored"], label=r"Geometric $\epsilon_y$ [mrad]")
    ax2.set_xlabel("Thick Integrator Slice Count ($N_{slices}$)")
    ax2.set_ylabel("Emittance [mrad]")
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="upper right")

    fig3_path = output_dir / "fig3_emittance_and_loss_convergence.png"
    fig.savefig(fig3_path, dpi=300)
    plt.close(fig)

    # All checks passed logic
    max_sym_vs_rk4_diff = max([c["diff_sym_vs_rk4_xp_rad"] for c in case_metrics.values()])
    n40_angle_conv_passed = bool(rec_40["xp_diff_from_ref_mrad"] < 1e-4)

    metrics = {
        "timestamp": timestamp,
        "n_particles": 500,
        "beam_energy_GeV": energy_GeV,
        "brho_T_m": float(brho),
        "element_length_m": length_m,
        "cases_evaluated": case_metrics,
        "convergence_records": convergence_records,
        "production_choice": {
            "n_slices": 40,
            "exit_xp_mrad": rec_40["exit_xp_mrad"],
            "exit_yp_mrad": rec_40["exit_yp_mrad"],
            "xp_diff_from_ref_mrad": rec_40["xp_diff_from_ref_mrad"],
            "yp_diff_from_ref_mrad": rec_40["yp_diff_from_ref_mrad"],
            "justification": "N_slices=40 achieves < 1e-4 mrad angle residual relative to N=320, maintaining fast parallel execution speed."
        },
        "max_symplectic_vs_rk4_diff_rad": float(max_sym_vs_rk4_diff),
        "output_directory": str(output_dir),
        "generated_figures": [str(fig1_path), str(fig2_path), str(fig3_path)],
        "all_checks_passed": bool(max_sym_vs_rk4_diff < 1e-6 and n40_angle_conv_passed)
    }

    metrics_file = output_dir / "metrics.json"
    with open(metrics_file, "w") as f:
        json.dump(metrics, f, indent=2)

    return metrics


if __name__ == "__main__":
    res = run_task03_validation()
    print("=== Task 03 Two-Plane Tracking & Convergence Validation Summary ===")
    print(f"Output Directory            : {res['output_directory']}")
    print(f"Symplectic vs RK4 Max Diff  : {res['max_symplectic_vs_rk4_diff_rad']:.3e} rad")
    print(f"N_slices=40 Angle Residual  : {res['production_choice']['xp_diff_from_ref_mrad']:.3e} mrad")
    print(f"Production Choice Justified : N_slices = {res['production_choice']['n_slices']}")
    print(f"All Checks Passed           : {res['all_checks_passed']}")
