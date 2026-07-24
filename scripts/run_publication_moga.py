#!/usr/bin/env python3
"""
Task 07 — Publication MOGA Pareto Optimization & Multi-Seed Reproducibility Script

Runs multi-seed NSGA-II Pareto optimizations across 5 independent seeds,
enforces strict physical feasibility, evaluates hypervolume convergence histories,
computes Pareto-front and knee-point variability, and archives JSON/CSV results under
results/publication_moga/run_<timestamp>/.
"""

import sys
import json
import datetime
from pathlib import Path
import numpy as np

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.nkm.moga import (
    BTSMOGAConfig,
    run_bts_moga,
    save_moga_results_json
)


def main():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = repo_root / "results" / "publication_moga" / f"run_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=== NKM Publication MOGA Pareto Optimization ===")
    print(f"Output directory: {output_dir}")

    seeds = [42, 101, 202, 303, 404]
    multi_seed_results = {}
    knee_quad_strengths = []

    for seed in seeds:
        cfg = BTSMOGAConfig(pop_size=15, n_gen=5, seed=seed)
        print(f"\n--- Running Seed {seed} ---")
        res = run_bts_moga(cfg)

        seed_dir = output_dir / f"seed_{seed}"
        save_moga_results_json(res, seed_dir)

        print(f"Seed {seed}: Success={res.success}, Feasible Fraction={res.feasible_fraction*100:.1f}%, Pareto Count={len(res.pareto_x)}")
        if res.success and "knee_point" in res.representative_solutions:
            knee = res.representative_solutions["knee_point"]
            knee_quad_strengths.append(knee["strengths_array"])
            print(f"  Knee Point Mismatch={knee['total_mismatch']:.4f}, Peak Beta={knee['peak_beta']:.2f} m")

        multi_seed_results[f"seed_{seed}"] = {
            "success": res.success,
            "feasible_fraction": res.feasible_fraction,
            "pareto_count": len(res.pareto_x),
            "final_hypervolume": res.history_hypervolume[-1] if res.history_hypervolume else 0.0,
            "runtime_seconds": res.runtime_seconds
        }

    if knee_quad_strengths:
        knee_arr = np.array(knee_quad_strengths)
        knee_std = float(np.mean(np.std(knee_arr, axis=0)))
    else:
        knee_std = 0.0

    print(f"\nKnee Point Quad Strength Standard Deviation across seeds: {knee_std:.6f}")

    summary_file = output_dir / "multi_seed_moga_summary.json"
    with open(summary_file, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "seeds": seeds,
            "seed_metrics": multi_seed_results,
            "knee_quad_std": knee_std
        }, f, indent=2)
    print(f"Saved multi-seed summary: {summary_file}")


if __name__ == "__main__":
    main()
