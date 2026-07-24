#!/usr/bin/env python3
"""
Task 08 — Dynamic Paper Figure and Table Reproduction Script

Single-command script to verify input data hashes, execute the data-driven paper pipeline,
generate publication figures/tables, and log environment/git provenance under
results/paper/paper_run_<timestamp>/.
"""

import sys
import json
import datetime
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.nkm.paper import run_paper_pipeline


def main():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"paper_run_{timestamp}"

    print("=== Fully Data-Driven Paper Pipeline Reproduction ===")
    print(f"Run ID: {run_id}")

    try:
        summary = run_paper_pipeline(repo_root=repo_root, run_id=run_id)
        print("\n--- Reproduction Pipeline Completed Successfully ---")
        print(f"Input Hashes Verified: {summary['input_hashes_verified']}")
        print(f"Tables Generated: {summary['tables_count']}")
        print(f"Figures Generated: {summary['figures_count']}")
        print(f"Output Directory: {repo_root / 'results' / 'paper' / run_id}")
    except Exception as e:
        print(f"\n[ERROR] Paper reproduction pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
