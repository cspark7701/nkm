#!/usr/bin/env python3
"""
Task 02 Validation Script — Longitudinal RADIA Field Integration & Quadrature

Performs 1D numerical quadrature of longitudinal field profiles By(z; x0, y0),
evaluates grid resolution convergence along z, compares direct longitudinal quadrature
with 2D kick map (kickmap_file.txt), analytical 4-wire model (nlk.py), and thick symplectic/RK4 tracking.

Saves figures and machine-readable metrics under results/field_validation/task02_run/.
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

from src.nkm.fieldmap import load_1d_fieldmap, NKMFieldMap1D, integrate_longitudinal_field, OutOfDomainError
from src.nkm.kickmap import NKMKickMap2D
from src.nkm.units import compute_rigidity, integrated_field_to_transverse_kicks, ELECTRON_CHARGE_C
from src.nkm.integrators import SymplecticSplitIntegrator, LorentzRK4Integrator
from src.nkm.paper import set_publication_style, PUBLICATION_COLORS
import nlk


def run_task02_validation() -> dict:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = repo_root / "results" / "field_validation" / f"task02_run_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    set_publication_style(font_size=10, dpi=300)

    # 1. Load transverse field map By(x) at y=0 from By.txt
    by_txt_path = repo_root / "By.txt"
    x_coords, by_transverse = load_1d_fieldmap(by_txt_path)
    fmap_transverse = NKMFieldMap1D(x_coords, by_transverse)

    # Peak vertical field at x = -10mm
    x_eval_m = -0.010
    by_peak_T = float(fmap_transverse.evaluate(x_eval_m))  # ~ -0.146109 T

    # Construct longitudinal profile By(z) along z in [-0.2625, +0.2625] m for x = -10mm
    length_m = 0.525
    z_coords = np.linspace(-length_m / 2.0, length_m / 2.0, 201)
    
    # Flat-top longitudinal profile with smooth fringe roll-off matching magnetic length L=0.525m
    fringe_w = 0.025  # 25 mm fringe length
    longitudinal_shape = 0.5 * (np.tanh((z_coords + length_m/2.0)/fringe_w) - np.tanh((z_coords - length_m/2.0)/fringe_w))
    by_longitudinal = by_peak_T * longitudinal_shape

    # 2. Direct 1D Numerical Quadrature along z (Simpson & Trapezoid)
    int_simpson_Tm = integrate_longitudinal_field(z_coords, by_longitudinal, method="simpson")
    int_trapz_Tm = integrate_longitudinal_field(z_coords, by_longitudinal, method="trapezoid")
    quadrature_diff_Tm = float(abs(int_simpson_Tm - int_trapz_Tm))

    # 3. Longitudinal Grid Resolution Convergence Scan along z
    grid_sizes = [21, 51, 101, 201, 401, 1001]
    convergence_int_Tm = []
    for n in grid_sizes:
        z_grid = np.linspace(-length_m / 2.0, length_m / 2.0, n)
        shape_g = 0.5 * (np.tanh((z_grid + length_m/2.0)/fringe_w) - np.tanh((z_grid - length_m/2.0)/fringe_w))
        by_g = by_peak_T * shape_g
        c_int = integrate_longitudinal_field(z_grid, by_g, method="simpson")
        convergence_int_Tm.append(c_int)

    ref_int_Tm = convergence_int_Tm[-1]
    grid_errors_Tm = [float(abs(val - ref_int_Tm)) for val in convergence_int_Tm]

    # 4. Transverse Kick Angle Conversion (4.0 GeV electron)
    energy_eV = 4.0e9
    brho = compute_rigidity(energy_eV, ELECTRON_CHARGE_C)
    dx_simpson_rad, _ = integrated_field_to_transverse_kicks(0.0, int_simpson_Tm, beam_energy_eV=energy_eV)
    dx_simpson_mrad = float(dx_simpson_rad * 1e3)

    # 5. Compare with 2D Kick Map (kickmap_file.txt at x=-10mm, y=0)
    kick_path = repo_root / "kickmap_file.txt"
    kmap_2d = NKMKickMap2D(kick_path)
    kx_2d_rad, _ = kmap_2d.evaluate_kick(x_eval_m, 0.0, energy_eV=energy_eV)
    dx_2d_mrad = float(kx_2d_rad * 1e3)

    # 6. Compare with Analytical 4-Wire Model (nlk.py)
    wire_x = np.array([0.0053, -0.0053, -0.0053, 0.0053])
    wire_y = np.array([0.0053, 0.0053, -0.0053, -0.0053])
    wire_currents = np.array([-3000.0, -3000.0, -3000.0, -3000.0])
    nlk_model = nlk.Kicker(wire_x, wire_y, wire_currents)
    _, ky_nlk = nlk_model.get_kick(x_eval_m, 0.0, brho, length_m)
    dx_nlk_mrad = float(ky_nlk * 1e3)

    # 7. Compare with Symplectic Thick Integrator Tracking along z in [0, L]
    z_center = length_m / 2.0
    def field_fn_longitudinal(x, y, z):
        z_rel = z - z_center
        if z_rel < -length_m/2.0 or z_rel > length_m/2.0:
            shape_z = 0.0
        else:
            shape_z = 0.5 * (np.tanh((z_rel + length_m/2.0)/fringe_w) - np.tanh((z_rel - length_m/2.0)/fringe_w))
        by_z = fmap_transverse.evaluate(x) * shape_z
        return by_z, np.zeros_like(x)

    beam_in = np.zeros((6, 1))
    beam_in[0, 0] = x_eval_m  # -10 mm offset

    sym_integrator = SymplecticSplitIntegrator(field_fn_longitudinal, length_m=length_m, n_slices=100, energy_GeV=4.0)
    rk4_integrator = LorentzRK4Integrator(field_fn_longitudinal, length_m=length_m, n_slices=100, energy_GeV=4.0)

    beam_sym = sym_integrator.track(beam_in)
    beam_rk4 = rk4_integrator.track(beam_in)

    dx_sym_mrad = float(beam_sym[1, 0] * 1e3)
    dx_rk4_mrad = float(beam_rk4[1, 0] * 1e3)

    tracking_vs_quadrature_err_rad = float(abs(beam_sym[1, 0] - dx_simpson_rad))

    # 8. Verify OutOfDomainError
    domain_guard_passed = False
    try:
        fmap_transverse.evaluate(0.50)  # Outside transverse bounds [-0.05, 0.05] m
    except OutOfDomainError:
        domain_guard_passed = True

    # --------------------------------------------------------------------------
    # Figure 1: Longitudinal Field Profile By(z) & Cumulative Integral
    # --------------------------------------------------------------------------
    cum_int_Tm = np.cumsum(by_longitudinal) * np.gradient(z_coords)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    ax1.plot(z_coords * 1e2, by_longitudinal, color=PUBLICATION_COLORS["beta_y"], linestyle="-", label=r"$B_y(z)$ at $x=-10$ mm [T]")
    ax1.set_ylabel(r"$B_y$ [T]")
    ax1.set_title("Longitudinal Magnetic Field Profile $B_y(z)$")
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="upper right")

    ax2.plot(z_coords * 1e2, cum_int_Tm, color=PUBLICATION_COLORS["beta_x"], linestyle="-", label=r"Cumulative $\int B_y\,dz$ [T$\cdot$m]")
    ax2.set_xlabel("Longitudinal Position $z$ [cm]")
    ax2.set_ylabel(r"Integrated Field [T$\cdot$m]")
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="lower right")

    fig1_path = output_dir / "fig1_longitudinal_field_profile.png"
    fig.savefig(fig1_path, dpi=300)
    plt.close(fig)

    # --------------------------------------------------------------------------
    # Figure 2: Longitudinal Quadrature Convergence
    # --------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 4.5))
    plot_errors = [max(e, 1e-16) for e in grid_errors_Tm]
    ax.loglog(grid_sizes, plot_errors, "o-", color=PUBLICATION_COLORS["dispersion"], label=r"Quadrature Residual $|I_N - I_{ref}|$")
    ax.set_xlabel("Longitudinal Grid Points ($N_z$)")
    ax.set_ylabel("Integration Residual [T$\cdot$m]")
    ax.set_title("Longitudinal Numerical Quadrature Convergence")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right")

    fig2_path = output_dir / "fig2_longitudinal_quadrature_convergence.png"
    fig.savefig(fig2_path, dpi=300)
    plt.close(fig)

    # --------------------------------------------------------------------------
    # Figure 3: Field Map vs Analytical Model Comparison
    # --------------------------------------------------------------------------
    x_scan_m = np.linspace(-0.018, 0.018, 100)
    kick_2d_mrad_scan = [float(kmap_2d.evaluate_kick(x_i, 0.0, energy_eV=energy_eV)[0] * 1e3) for x_i in x_scan_m]
    kick_nlk_mrad_scan = [float(nlk_model.get_kick(x_i, 0.0, brho, length_m)[1] * 1e3) for x_i in x_scan_m]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(x_scan_m * 1e3, kick_2d_mrad_scan, color=PUBLICATION_COLORS["beta_y"], linestyle="-", label="RADIA 2D Kick Map ($K_x$)")
    ax.plot(x_scan_m * 1e3, kick_nlk_mrad_scan, color=PUBLICATION_COLORS["stored"], linestyle="--", label="Analytical 4-Wire NLK Model")
    ax.set_xlabel("Horizontal Position $x$ [mm]")
    ax.set_ylabel(r"Transverse Kick $\Delta x'$ [mrad]")
    ax.set_title("NKM Transverse Kick Profile Comparison")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="lower center")

    fig3_path = output_dir / "fig3_fieldmap_vs_analytical_comparison.png"
    fig.savefig(fig3_path, dpi=300)
    plt.close(fig)

    metrics = {
        "timestamp": timestamp,
        "source_data_file": "By.txt",
        "transverse_domain_m": [float(x_coords.min()), float(x_coords.max())],
        "longitudinal_bounds_m": [float(z_coords.min()), float(z_coords.max())],
        "n_longitudinal_points": len(z_coords),
        "peak_field_x_minus_10mm_T": by_peak_T,
        "integrated_field_simpson_Tm": int_simpson_Tm,
        "integrated_field_trapz_Tm": int_trapz_Tm,
        "simpson_vs_trapz_diff_Tm": quadrature_diff_Tm,
        "on_axis_kick_simpson_mrad": dx_simpson_mrad,
        "kickmap_2d_kick_x_minus_10mm_mrad": dx_2d_mrad,
        "nlk_analytical_kick_x_minus_10mm_mrad": dx_nlk_mrad,
        "symplectic_tracking_kick_mrad": dx_sym_mrad,
        "rk4_tracking_kick_mrad": dx_rk4_mrad,
        "tracking_vs_quadrature_err_rad": tracking_vs_quadrature_err_rad,
        "out_of_domain_guard_verified": domain_guard_passed,
        "output_directory": str(output_dir),
        "generated_figures": [str(fig1_path), str(fig2_path), str(fig3_path)],
        "all_checks_passed": bool(
            tracking_vs_quadrature_err_rad < 1e-3 and
            domain_guard_passed and
            quadrature_diff_Tm < 1e-5
        )
    }

    metrics_file = output_dir / "task02_longitudinal_integration_metrics.json"
    with open(metrics_file, "w") as f:
        json.dump(metrics, f, indent=2)

    return metrics


if __name__ == "__main__":
    res = run_task02_validation()
    print("=== Task 02 Longitudinal Field Integration Validation Summary ===")
    print(f"Output Directory            : {res['output_directory']}")
    print(f"Integrated Field (Simpson)  : {res['integrated_field_simpson_Tm']:.6f} T*m")
    print(f"Integrated Field (Trapz)    : {res['integrated_field_trapz_Tm']:.6f} T*m")
    print(f"Direct Quadrature Kick      : {res['on_axis_kick_simpson_mrad']:.4f} mrad")
    print(f"RADIA 2D Kick (x=-10mm)    : {res['kickmap_2d_kick_x_minus_10mm_mrad']:.4f} mrad")
    print(f"Analytical NLK Model Kick   : {res['nlk_analytical_kick_x_minus_10mm_mrad']:.4f} mrad")
    print(f"Symplectic Integrator Kick  : {res['symplectic_tracking_kick_mrad']:.4f} mrad")
    print(f"RK4 Integrator Kick         : {res['rk4_tracking_kick_mrad']:.4f} mrad")
    print(f"Tracking vs Quadrature Err  : {res['tracking_vs_quadrature_err_rad']:.3e} rad")
    print(f"Domain Guard Enforcement    : {res['out_of_domain_guard_verified']}")
    print(f"All Checks Passed           : {res['all_checks_passed']}")
