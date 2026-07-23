#!/usr/bin/env python3
"""
BTS Quadrupole Optics Optimization Script for Milestone 4

Executes constrained deterministic optimization of 9 BTS quadrupole strengths,
re-tracks particle beam through candidate finalists, computes sensitivity matrix,
and exports results to results/bts_optimization/.
"""

import json
import sys
import time
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import at

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.nkm.bts_lattice import BTSConfig, create_bts_lattice, validate_bts_lattice
from src.nkm.optics import compute_twiss_propagation, compute_mismatch_metric, plot_bts_optics
from src.nkm.optimization import (
    BTSOptimizationConfig,
    optimize_bts_quadrupoles,
    compute_sensitivity_matrix
)

OUTPUT_DIR = REPO_ROOT / "results" / "bts_optimization"
PLOT_PATH = OUTPUT_DIR / "bts_optimized_optics.png"
METRICS_JSON = OUTPUT_DIR / "bts_optimization_results.json"


def run_bts_optimization():
    """Execute complete BTS optimization pipeline."""
    print("=== Starting BTS Quadrupole Optimization ===", flush=True)
    config = BTSOptimizationConfig(random_seed=42)
    
    # 1. Run primary optimizer (SLSQP)
    print("Running SLSQP optimizer...", flush=True)
    res_slsqp = optimize_bts_quadrupoles(method="SLSQP", config=config, n_starts=1)
    print(f"SLSQP finished. Merit: {res_slsqp.initial_merit:.2f} -> {res_slsqp.final_merit:.4f}", flush=True)
    
    # 2. Run independent comparison optimizer (Nelder-Mead with fast iterations)
    print("Running Nelder-Mead comparison optimizer...", flush=True)
    res_nm = optimize_bts_quadrupoles(method="Nelder-Mead", config=config, n_starts=1)
    print(f"Nelder-Mead finished. Merit: {res_nm.initial_merit:.2f} -> {res_nm.final_merit:.4f}", flush=True)
    
    # Select best solution
    best_res = res_slsqp if res_slsqp.final_merit <= res_nm.final_merit else res_nm
    print(f"Selected best method: {best_res.method}", flush=True)
    
    # 3. Create optimized lattice and re-verify optics
    opt_config = BTSConfig(
        k_q11=best_res.optimized_strengths[0],
        k_q12=best_res.optimized_strengths[1],
        k_q13=best_res.optimized_strengths[2],
        k_q21=best_res.optimized_strengths[3],
        k_q22=best_res.optimized_strengths[4],
        k_q23=best_res.optimized_strengths[5],
        k_q31=best_res.optimized_strengths[6],
        k_q32=best_res.optimized_strengths[7],
        k_q33=best_res.optimized_strengths[8],
    )
    opt_lattice = create_bts_lattice(opt_config)
    lat_val = validate_bts_lattice(opt_lattice)
    
    # 4. Particle tracking verification (1000 particles)
    initial_twiss = {
        'beta': [config.init_beta_x, config.init_beta_y],
        'alpha': [config.init_alpha_x, config.init_alpha_y],
        'dispersion': [config.init_disp_x, config.init_disp_px, 0.0, 0.0]
    }
    
    beam_sigma = at.sigma_matrix(
        betax=config.init_beta_x, alphax=config.init_alpha_x, emitx=10.89e-9,
        betay=config.init_beta_y, alphay=config.init_alpha_y, emity=10.89e-9,
        blength=13.4e-3, espread=1e-3
    )
    init_beam = at.beam(1000, beam_sigma)
    track_res = at.lattice_track(opt_lattice, init_beam.copy(), nturns=1)
    survived = int(np.sum(~np.isnan(track_res[1]['rout'][0, :])))
    survival_fraction = float(survived / 1000)
    
    # 5. Sensitivity matrix computation
    sens_matrix = compute_sensitivity_matrix(best_res.optimized_strengths, config=config)
    
    # 6. Save plot
    plot_bts_optics(opt_lattice, initial_twiss, output_path=PLOT_PATH)
    
    # 7. Save JSON results
    summary = {
        "slsqp_result": {
            "success": res_slsqp.success,
            "final_merit": res_slsqp.final_merit,
            "mismatch_x": res_slsqp.final_mismatch_x,
            "mismatch_y": res_slsqp.final_mismatch_y,
            "max_beta_x_m": res_slsqp.final_max_beta_x,
            "max_beta_y_m": res_slsqp.final_max_beta_y,
            "runtime_s": res_slsqp.runtime_seconds,
            "strengths": [float(k) for k in res_slsqp.optimized_strengths]
        },
        "nelder_mead_result": {
            "success": res_nm.success,
            "final_merit": res_nm.final_merit,
            "mismatch_x": res_nm.final_mismatch_x,
            "mismatch_y": res_nm.final_mismatch_y,
            "max_beta_x_m": res_nm.final_max_beta_x,
            "max_beta_y_m": res_nm.final_max_beta_y,
            "runtime_s": res_nm.runtime_seconds,
            "strengths": [float(k) for k in res_nm.optimized_strengths]
        },
        "best_solution": {
            "method": best_res.method,
            "initial_merit": best_res.initial_merit,
            "final_merit": best_res.final_merit,
            "initial_mismatch_x": best_res.initial_mismatch_x,
            "initial_mismatch_y": best_res.initial_mismatch_y,
            "final_mismatch_x": best_res.final_mismatch_x,
            "final_mismatch_y": best_res.final_mismatch_y,
            "max_beta_x_m": best_res.final_max_beta_x,
            "max_beta_y_m": best_res.final_max_beta_y,
            "tracking_survival_fraction": survival_fraction,
            "lattice_checks_passed": lat_val["all_checks_passed"],
            "optimized_strengths": [float(k) for k in best_res.optimized_strengths]
        },
        "sensitivity": {
            "observable_names": sens_matrix["observable_names"],
            "quad_names": sens_matrix["quad_names"],
            "jacobian_matrix": [[float(v) for v in row] for row in sens_matrix["jacobian_matrix"]]
        }
    }
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(METRICS_JSON, "w") as f:
        json.dump(summary, f, indent=2)
        
    print("\n=== BTS Optimization Summary ===", flush=True)
    print(f"Initial Merit: {best_res.initial_merit:.4f} -> Final Merit: {best_res.final_merit:.4f}", flush=True)
    print(f"Initial Mx: {best_res.initial_mismatch_x:.4f} -> Final Mx: {best_res.final_mismatch_x:.4f}", flush=True)
    print(f"Initial My: {best_res.initial_mismatch_y:.4f} -> Final My: {best_res.final_mismatch_y:.4f}", flush=True)
    print(f"Max Beta X: {best_res.final_max_beta_x:.2f} m | Max Beta Y: {best_res.final_max_beta_y:.2f} m", flush=True)
    print(f"Tracking Particle Survival: {survival_fraction * 100:.1f}%", flush=True)
    print(f"Optimized Quad Strengths (q11..q33):", flush=True)
    print(" ", np.round(best_res.optimized_strengths, 5), flush=True)
    print(f"Plot saved to: {PLOT_PATH}", flush=True)
    print(f"Metrics saved to: {METRICS_JSON}", flush=True)


if __name__ == "__main__":
    run_bts_optimization()
