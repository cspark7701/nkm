#!/usr/bin/env python3
"""
Protected Files Hash Inventory Script

Computes and verifies SHA256 checksums for all protected source data files in the NKM repository.
Saves manifest to results/baseline/protected_files_manifest.json.
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, List

PROTECTED_EXACT_FILES = [
    "NKM_radia.ipynb",
    "NKM_radia_y=0.ipynb",
    "nlk.py",
    "storage_ring.ipynb",
]

PROTECTED_EXTENSIONS = [
    ".xls", ".xlsx", ".xlsm",
    ".npy", ".npz",
    ".txt"
]

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_MANIFEST = REPO_ROOT / "results" / "baseline" / "protected_files_manifest.json"


def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def find_protected_files(root: Path) -> List[Path]:
    """Find all protected files in the repository root."""
    protected_files = []
    
    # 1. Exact match files in repo root
    for fname in PROTECTED_EXACT_FILES:
        fpath = root / fname
        if fpath.is_file():
            protected_files.append(fpath)
            
    # 2. Extension matches in repo root (non-recursive to avoid outputs under results/)
    for item in root.iterdir():
        if item.is_file() and item.suffix.lower() in PROTECTED_EXTENSIONS:
            if item not in protected_files:
                protected_files.append(item)
                
    return sorted(protected_files, key=lambda p: p.name)


def create_hash_manifest() -> Dict[str, str]:
    """Build a manifest dictionary mapping relative path to SHA256 hash."""
    manifest = {}
    protected_files = find_protected_files(REPO_ROOT)
    
    for fpath in protected_files:
        rel_path = fpath.relative_to(REPO_ROOT).as_posix()
        manifest[rel_path] = compute_sha256(fpath)
        
    return manifest


def verify_hash_manifest(manifest_path: Path = OUTPUT_MANIFEST) -> bool:
    """Verify that protected files match recorded SHA256 manifest."""
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
        
    with open(manifest_path, "r") as f:
        recorded_manifest = json.load(f)
        
    all_matched = True
    for rel_path, expected_hash in recorded_manifest.items():
        fpath = REPO_ROOT / rel_path
        if not fpath.is_file():
            print(f"[MISSING] Protected file missing: {rel_path}")
            all_matched = False
            continue
            
        current_hash = compute_sha256(fpath)
        if current_hash != expected_hash:
            print(f"[MISMATCH] Protected file hash mismatch for {rel_path}!")
            print(f"  Expected: {expected_hash}")
            print(f"  Actual:   {current_hash}")
            all_matched = False
            
    return all_matched


def main():
    OUTPUT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    manifest = create_hash_manifest()
    
    with open(OUTPUT_MANIFEST, "w") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"Protected files hash manifest saved to {OUTPUT_MANIFEST}")
    print(f"Total protected files cataloged: {len(manifest)}")
    for path, h in manifest.items():
        print(f"  {path:30s} -> {h[:12]}...")
        
    # Self-verify
    if verify_hash_manifest(OUTPUT_MANIFEST):
        print("Verification SUCCESS: All protected file hashes match!")
    else:
        print("Verification FAILURE: One or more protected files do not match!")


if __name__ == "__main__":
    main()
