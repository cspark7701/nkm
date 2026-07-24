#!/usr/bin/env python3
"""
Task 05 — Deterministic BTS Quadrupole Optimization Script

Performs physically-constrained 2-stage optimization (Least-Squares + SLSQP),
multi-start search, Jacobian sensitivity analysis, and saves results under
results/bts_publication_optimization/run_<timestamp>/.
"""

import sys
import json
import datetime
from pathlib import Path
import numpy as np

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.nkm.optimization import (
    BTSOptimizationConfig,
    optimize_bts_quadrupoles,
    compute_sensitivity_matrix,
    round_strengths
)


def main():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = repo_root / "results" / "bts_publication_optimization" / f"run_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=== Deterministic BTS Quadrupole Optimization ===")
    print(f"Output directory: {output_dir}")

    config = BTSOptimizationConfig(random_seed=42, max_iter=20)

    # 1. Multi-start Optimization (Fast verification run)
    print("Running 2-stage optimization (Least-Squares + SLSQP)...")
    res = optimize_bts_quadrupoles(method="least_squares", config=config, n_starts=1)

    print(f"Optimization Success: {res.success}")
    print(f"Initial Merit J: {res.initial_merit:.4f} -> Final Merit J: {res.final_merit:.4f}")
    print(f"Final Mismatch X: {res.final_mismatch_x:.6f}, Y: {res.final_mismatch_y:.6f}")
    print(f"Peak Beta X: {res.final_max_beta_x:.2f} m, Y: {res.final_max_beta_y:.2f} m")

    rounded_k = round_strengths(res.optimized_strengths, decimals=6)
    print(f"Optimized Quad Strengths K (m^-2):\n{rounded_k}")

    # 2. Jacobian Sensitivity Matrix Analysis
    sens = compute_sensitivity_matrix(res.optimized_strengths, config=config)
    print(f"Jacobian Condition Number: {sens['condition_number']:.2f}")
    print(f"Singular Values: {sens['singular_values']}")

    summary_data = {
        "timestamp": timestamp,
        "method": res.method,
        "success": res.success,
        "initial_merit": res.initial_merit,
        "final_merit": res.final_merit,
        "final_mismatch_x": res.final_mismatch_x,
        "final_mismatch_y": res.final_mismatch_y,
        "final_max_beta_x": res.final_max_beta_x,
        "final_max_beta_y": res.final_max_beta_y,
        "final_disp_x_residual": res.final_disp_x_residual,
        "optimized_strengths_raw": res.optimized_strengths.tolist(),
        "optimized_strengths_rounded": rounded_k.tolist(),
        "sensitivity": {
            "condition_number": sens["condition_number"],
            "singular_values": sens["singular_values"].tolist(),
            "jacobian_matrix": sens["jacobian_matrix"].tolist()
        },
        "violations": res.violations
    }

    json_path = output_dir / "bts_optimization_summary.json"
    with open(json_path, 'w') as f:
        json.dump(summary_data, f, indent=2)
    print(f"Saved summary JSON: {json_path}")


if __name__ == "__main__":
    main()
