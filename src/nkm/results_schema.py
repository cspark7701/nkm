"""
NKM Paper Result Provenance & Cryptographic Schema Module

Defines result directory schemas, cryptographic input file hashing, environment logging,
and validation checks for fully data-driven publication reproduction.
"""

from dataclasses import dataclass, field
from pathlib import Path
import hashlib
import json
import os
import sys
import subprocess
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np


@dataclass
class PaperResultSchema:
    """Schema directory structure for publication artifacts."""
    run_id: str
    base_dir: Path

    def __post_init__(self):
        self.run_dir = self.base_dir / self.run_id
        self.figures_dir = self.run_dir / "figures"
        self.tables_dir = self.run_dir / "tables"

    def initialize_directories(self) -> None:
        """Create all required schema subdirectories."""
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        self.tables_dir.mkdir(parents=True, exist_ok=True)


def compute_file_hash(filepath: Union[str, Path]) -> str:
    """Compute SHA-256 hash of a file."""
    filepath = Path(filepath)
    if not filepath.is_file():
        raise FileNotFoundError(f"Required input file missing: {filepath}")

    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_input_data_hashes(repo_root: Path) -> Dict[str, str]:
    """Compute cryptographic hashes for authoritative scientific input data files."""
    data_files = [
        "By.txt",
        "kickmap_file.txt",
        "K4GSR_HBIv4-1.mat",
        "storage_ring_lattice_nkm.mat"
    ]
    hashes = {}
    for filename in data_files:
        p = repo_root / filename
        if p.is_file():
            hashes[filename] = compute_file_hash(p)
        else:
            hashes[filename] = "MISSING"
    return hashes


def record_environment_metadata(output_dir: Path) -> Dict[str, str]:
    """Record Python environment and Git commit hash for provenance."""
    try:
        git_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(output_dir.parent.parent),
            text=True
        ).strip()
    except Exception:
        git_commit = "UNKNOWN"

    env_info = {
        "python_version": sys.version,
        "platform": sys.platform,
        "git_commit": git_commit
    }

    with open(output_dir / "git_commit.txt", "w") as f:
        f.write(f"Git Commit: {git_commit}\n")

    with open(output_dir / "environment.txt", "w") as f:
        f.write(f"Python: {sys.version}\nPlatform: {sys.platform}\n")

    return env_info


def compute_rms_envelope(beta_m: np.ndarray,
                         disp_m: np.ndarray,
                         emit_mrad: float = 1.0e-7,
                         espread: float = 1.1e-3,
                         n_sigma: float = 3.0) -> np.ndarray:
    """
    Calculate statistically consistent total RMS envelope:
    
        sigma_x(s) = sqrt( emittance * beta_x(s) + [disp_x(s) * sigma_delta]^2 )
        Total_envelope(s) = n_sigma * sigma_x(s)
    """
    sigma_x_rms = np.sqrt(emit_mrad * beta_m + (disp_m * espread)**2)
    return n_sigma * sigma_x_rms
