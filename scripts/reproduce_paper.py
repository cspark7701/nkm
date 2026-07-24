#!/usr/bin/env python3
"""
Publication Paper Results & Artifacts Reproduction Script for Milestone 8

Verifies input file integrity, runs the complete paper pipeline, and generates
LaTeX tables, publication-quality figures (300 DPI PNG & vector PDF), and summary metrics.
"""

import argparse
import os
import sys
import subprocess
import time

# Add src to path if running directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from nkm.paper import run_paper_pipeline


def main():
    parser = argparse.ArgumentParser(description="Reproduce Publication Paper Results and Artifacts (Milestone 8)")
    parser.add_argument("--output-dir", type=str, default="results/paper", help="Output directory for paper artifacts (default: results/paper)")
    parser.add_argument("--skip-hash-check", action="store_true", help="Skip protected input hash inventory check")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("      PUBLICATION PAPER REPRODUCTION PIPELINE (MILESTONE 8)")
    print("=" * 80)
    print(f"Output Directory: {args.output_dir}")
    print("-" * 80)
    
    # 1. Verify protected input hashes
    if not args.skip_hash_check:
        print("\n[Step 1/3] Verifying Protected Scientific Input File Hashes...")
        hash_script = os.path.join(os.path.dirname(__file__), "inventory_protected_hashes.py")
        res = subprocess.run([sys.executable, hash_script], capture_output=True, text=True)
        if res.returncode == 0:
            print("  [OK] Input file hash integrity verified.")
        else:
            print(f"  [WARNING] Hash check output: {res.stdout.strip()}")
    else:
        print("\n[Step 1/3] Skipping input hash check (--skip-hash-check).")
        
    # 2. Run paper pipeline
    print(f"\n[Step 2/3] Executing Paper Pipeline into '{args.output_dir}'...")
    start_time = time.time()
    summary = run_paper_pipeline(output_dir=args.output_dir)
    runtime = time.time() - start_time
    
    # 3. Print Summary
    print("\n[Step 3/3] Paper Reproduction Completed Successfully.")
    print("-" * 80)
    print(f"Execution Time:    {runtime:.2f} seconds")
    print(f"LaTeX/MD Tables:   {len(summary['tables_generated'])} exported to '{args.output_dir}/tables/'")
    print(f"Figures (PNG/PDF): {len(summary['figures_generated'])} exported to '{args.output_dir}/figures/'")
    print(f"Summary Metrics:   Saved to '{args.output_dir}/paper_summary_metrics.json'")
    print("=" * 80)
    print("\nPaper reproduction finished cleanly.")


if __name__ == "__main__":
    main()
