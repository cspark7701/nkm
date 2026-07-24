#!/usr/bin/env python3
"""
Task 06 — Publication Error Model & Tolerance Budget Simulation Script

Runs Monte Carlo ensemble simulations across 5 physical error categories,
evaluates percentiles (p50, p68, p95, p99), computes bootstrap confidence intervals,
ranks dominant error contributors via OAT sensitivity scans, and outputs JSON metrics under
results/publication_tolerances/run_<timestamp>/.
"""

import sys
import json
import datetime
from pathlib import Path
import numpy as np

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.nkm.bts_lattice import BTSConfig
from src.nkm.errors import ErrorBudgetConfig, sample_error_ensemble
from src.nkm.robust_optimization import (
    evaluate_robustness_statistics,
    compute_one_at_a_time_sensitivity
)


def main():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = repo_root / "results" / "publication_tolerances" / f"run_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=== NKM Publication Error Model & Tolerance Budget ===")
    print(f"Output directory: {output_dir}")

    config = ErrorBudgetConfig()
    nominal_bts = BTSConfig()
    target_twiss = {"beta": [2.336495, 4.256241], "alpha": [-0.016335, 0.017772]}

    # 1. Fast Monte Carlo Ensemble (N=50 for verification)
    n_samples = 50
    print(f"Sampling Monte Carlo ensemble (N={n_samples})...")
    samples = sample_error_ensemble(config, n_samples=n_samples, seed=42)

    stats = evaluate_robustness_statistics(nominal_bts, target_twiss, samples)

    print("\n--- Monte Carlo Robustness Percentiles ---")
    print(f"Failure Probability: {stats['failure_probability']*100:.1f}%")
    print(f"Horizontal Mismatch Mx: p50={stats['mismatch_x']['p50_median']:.4f}, p68={stats['mismatch_x']['p68']:.4f}, p95={stats['mismatch_x']['p95']:.4f}, p99={stats['mismatch_x']['p99']:.4f}")
    print(f"Vertical Mismatch My:   p50={stats['mismatch_y']['p50_median']:.4f}, p68={stats['mismatch_y']['p68']:.4f}, p95={stats['mismatch_y']['p95']:.4f}, p99={stats['mismatch_y']['p99']:.4f}")
    print(f"Bootstrap 95% CI for Median Mx: [{stats['mismatch_x']['bootstrap_95ci_median'][0]:.4f}, {stats['mismatch_x']['bootstrap_95ci_median'][1]:.4f}]")

    # 2. One-At-A-Time Sensitivity Ranking
    print("\n--- One-At-A-Time (OAT) Sensitivity Ranking ---")
    rankings = compute_one_at_a_time_sensitivity(nominal_bts, target_twiss, n_samples=30, seed=42)
    for rank, (label, val) in enumerate(rankings.items(), start=1):
        print(f"{rank}. {label:35s}: Delta Merit = {val:.6f}")

    summary_data = {
        "timestamp": timestamp,
        "n_samples": n_samples,
        "robustness_statistics": stats,
        "sensitivity_ranking": rankings
    }

    json_path = output_dir / "publication_tolerances_summary.json"
    with open(json_path, 'w') as f:
        json.dump(summary_data, f, indent=2)
    print(f"\nSaved summary JSON: {json_path}")


if __name__ == "__main__":
    main()
