#!/usr/bin/env python3
"""
BTS Quadrupole MOGA Pareto Optimization Script for Milestone 7

Executes multi-objective genetic algorithm (NSGA-II) optimization for the 9 BTS quadrupole strengths.
Evaluates Pareto trade-offs between optical mismatch, peak beta function (aperture margin),
and residual dispersion. Saves history, Pareto front CSV, representative designs, and diagnostic plots.
"""

import argparse
import os
import sys
import time
import numpy as np

# Add src to path if running directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from nkm.moga import (
    BTSMOGAConfig,
    run_bts_moga,
    save_moga_results,
    plot_moga_summary
)


def main():
    parser = argparse.ArgumentParser(description="BTS Quadrupole MOGA Pareto Optimization (Milestone 7)")
    parser.add_argument("--pop-size", type=int, default=50, help="Population size for NSGA-II (default: 50)")
    parser.add_argument("--n-gen", type=int, default=40, help="Number of generations (default: 40)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--output-dir", type=str, default="results/moga", help="Output directory for results (default: results/moga)")
    parser.add_argument("--mc-seeds", type=int, default=50, help="Number of Monte Carlo seeds for finalist re-evaluation (default: 50)")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("      BTS QUADRUPOLE MOGA PARETO OPTIMIZATION (MILESTONE 7)")
    print("=" * 80)
    print(f"Population Size: {args.pop_size}")
    print(f"Generations:     {args.n_gen}")
    print(f"Random Seed:     {args.seed}")
    print(f"Output Dir:      {args.output_dir}")
    print(f"MC Re-eval Seeds:{args.mc_seeds}")
    print("-" * 80)
    
    cfg = BTSMOGAConfig(
        pop_size=args.pop_size,
        n_gen=args.n_gen,
        seed=args.seed,
        eval_n_mc_seeds=args.mc_seeds
    )
    
    start_time = time.time()
    result = run_bts_moga(cfg)
    total_time = time.time() - start_time
    
    print("\n" + "=" * 80)
    print("                     MOGA OPTIMIZATION COMPLETED")
    print("=" * 80)
    print(f"Success Status:    {result.success}")
    print(f"Total Evaluations: {result.n_evals}")
    print(f"Pareto Set Size:   {len(result.pareto_x)}")
    print(f"Runtime:           {total_time:.2f} seconds")
    print("-" * 80)
    
    print("\nREPRESENTATIVE PARETO SOLUTIONS:")
    print("-" * 80)
    header = f"{'Design Name':<22} | {'Mismatch (Mx+My)':<16} | {'Peak Beta [m]':<13} | {'Res. Disp [m]':<13} | {'MC Feasible %':<13}"
    print(header)
    print("-" * len(header))
    
    reps = result.representative_solutions
    evals = result.finalist_evaluations
    
    for name, sol in reps.items():
        ev = evals[name]
        f_mismatch = sol['total_mismatch']
        f_beta = sol['peak_beta']
        f_disp = sol['residual_dispersion']
        mc_feas = ev['mc_feasible_fraction'] * 100.0
        
        print(f"{name:<22} | {f_mismatch:<16.4f} | {f_beta:<13.4f} | {f_disp:<13.4f} | {mc_feas:<13.1f}%")
        
    print("-" * 80)
    
    # Save outputs and plots
    print(f"\nSaving results to '{args.output_dir}'...")
    save_moga_results(result, output_dir=args.output_dir)
    plot_moga_summary(result, save_dir=args.output_dir)
    
    print(f"Outputs successfully generated in '{args.output_dir}/':")
    print(f"  - moga_pareto_front.csv")
    print(f"  - representative_solutions.json")
    print(f"  - moga_result.pkl")
    print(f"  - moga_pareto_front_2d.png")
    print(f"  - moga_convergence.png")
    print(f"  - moga_parallel_coordinates.png")
    print("\nDone.")


if __name__ == "__main__":
    main()
