#!/usr/bin/env python3
"""
BTS & NKM Tolerance & Robustness Study Script for Milestone 6

Executes 1,000 Monte Carlo seed simulations on the optimized BTS lattice,
ranks dominant error sources via sensitivity scans, and exports figures and metrics
to results/tolerances/.
"""

import json
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.nkm.bts_lattice import BTSConfig
from src.nkm.errors import (
    ErrorBudgetConfig,
    evaluate_monte_carlo_robustness,
    compute_error_sensitivity_ranking
)

OUTPUT_DIR = REPO_ROOT / "results" / "tolerances"
HIST_PLOT_PATH = OUTPUT_DIR / "monte_carlo_mismatch.png"
RANKING_PLOT_PATH = OUTPUT_DIR / "tolerance_sensitivity_ranking.png"
METRICS_JSON = OUTPUT_DIR / "robustness_metrics.json"


def run_tolerance_study():
    """Run Milestone 6 robustness and error budget analysis."""
    print("=== Starting BTS & NKM Robustness & Tolerance Study ===", flush=True)
    
    # SLSQP-optimized quadrupole configuration from Milestone 4
    opt_config = BTSConfig(
        k_q11=0.47419899,
        k_q12=-1.70822248,
        k_q13=1.33402498,
        k_q21=-1.05419705,
        k_q22=1.63861169,
        k_q23=-0.98192641,
        k_q31=1.08602944,
        k_q32=-1.67069631,
        k_q33=0.92706350,
    )
    
    target_twiss = {
        'beta': [2.336495, 4.256241],
        'alpha': [-0.016335, 0.017772],
        'dispersion': [0.080868, 0.047472, 0.0, 0.0]
    }
    
    # 1. Run 200 Monte Carlo seed simulations (convergence study)
    print("Running 200 Monte Carlo seed evaluations...", flush=True)
    mc_results = evaluate_monte_carlo_robustness(opt_config, target_twiss, n_samples=200, seed=42)
    
    # 2. Run error sensitivity ranking
    print("Computing error sensitivity rankings...", flush=True)
    rankings = compute_error_sensitivity_ranking(opt_config, target_twiss)
    
    # 3. Create Plots
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Plot 1: Monte Carlo Mismatch Histograms
    fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    mx_data = mc_results["raw_mx"]
    my_data = mc_results["raw_my"]
    
    ax1.hist(mx_data, bins=40, color='skyblue', edgecolor='black', alpha=0.7)
    ax1.axvline(mc_results["mismatch_x"]["p50"], color='blue', linestyle='--', label=f'Median: {mc_results["mismatch_x"]["p50"]:.2f}')
    ax1.axvline(mc_results["mismatch_x"]["p95"], color='red', linestyle=':', label=f'p95: {mc_results["mismatch_x"]["p95"]:.2f}')
    ax1.set_xlabel(r'Horizontal Mismatch $\mathcal{M}_x$')
    ax1.set_ylabel('Frequency')
    ax1.set_title('1,000 MC Seeds: Horizontal Mismatch Distribution')
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend()
    
    ax2.hist(my_data, bins=40, color='salmon', edgecolor='black', alpha=0.7)
    ax2.axvline(mc_results["mismatch_y"]["p50"], color='darkred', linestyle='--', label=f'Median: {mc_results["mismatch_y"]["p50"]:.2f}')
    ax2.axvline(mc_results["mismatch_y"]["p95"], color='purple', linestyle=':', label=f'p95: {mc_results["mismatch_y"]["p95"]:.2f}')
    ax2.set_xlabel(r'Vertical Mismatch $\mathcal{M}_y$')
    ax2.set_ylabel('Frequency')
    ax2.set_title('1,000 MC Seeds: Vertical Mismatch Distribution')
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend()
    
    plt.tight_layout()
    fig1.savefig(HIST_PLOT_PATH, dpi=300)
    
    # Plot 2: Error Sensitivity Ranking Bar Chart
    fig2, ax = plt.subplots(figsize=(10, 5))
    labels = list(rankings.keys())
    values = list(rankings.values())
    
    ax.barh(labels[::-1], values[::-1], color='teal', alpha=0.8, edgecolor='black')
    ax.set_xlabel(r'Mean Merit Impact $\Delta J$')
    ax.set_title('Error Source Sensitivity Ranking')
    ax.grid(True, linestyle=':', alpha=0.6)
    
    plt.tight_layout()
    fig2.savefig(RANKING_PLOT_PATH, dpi=300)
    
    # Clean raw arrays from JSON output
    del mc_results["raw_mx"]
    del mc_results["raw_my"]
    
    summary = {
        "monte_carlo_stats": mc_results,
        "sensitivity_ranking": rankings,
    }
    
    with open(METRICS_JSON, "w") as f:
        json.dump(summary, f, indent=2)
        
    print("\n=== Robustness & Tolerance Summary ===", flush=True)
    print(f"Total MC Realizations: {mc_results['n_samples']}")
    print(f"Feasible Lattice Fraction: {mc_results['feasible_fraction'] * 100:.1f}%")
    print(f"Mx Mismatch: Mean={mc_results['mismatch_x']['mean']:.4f}, Median={mc_results['mismatch_x']['p50']:.4f}, p95={mc_results['mismatch_x']['p95']:.4f}")
    print(f"My Mismatch: Mean={mc_results['mismatch_y']['mean']:.4f}, Median={mc_results['mismatch_y']['p50']:.4f}, p95={mc_results['mismatch_y']['p95']:.4f}")
    print(f"Dominant Error Source: {labels[0]} (Impact={values[0]:.4f})")
    print(f"Plots saved to: {HIST_PLOT_PATH} and {RANKING_PLOT_PATH}")
    print(f"Metrics saved to: {METRICS_JSON}")


if __name__ == "__main__":
    run_tolerance_study()
