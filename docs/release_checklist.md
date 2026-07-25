# NKM Reproducible Publication Release Checklist

## Pre-Release Verification

- [x] **Clean Checkout Test**: Verified repository clones cleanly and installs dependencies.
- [x] **Test Suite**: Run `pytest -v` (all 68 tests passing 100%).
- [x] **Input Hashes**: Verified SHA-256 hashes of protected scientific input files (`By.txt`, `kickmap_file.txt`, `K4GSR_HBIv4-1.mat`).
- [x] **Single-Command Pipeline**: Run `python3 scripts/reproduce_paper.py` to confirm figure/table generation.
- [x] **Protected Files Integrity**: Verified all protected files (`NKM_radia.ipynb`, `nlk.py`, `storage_ring.ipynb`, etc.) are 100% clean and unmodified via `git status` and `git diff`.
- [x] **Metadata Alignment**: `LICENSE` (MIT), `CITATION.cff`, `README.md`, and `pyproject.toml` aligned.
- [x] **CI Workflows**: GitHub Actions workflows `.github/workflows/ci.yml` and `.github/workflows/paper-regression.yml` created.

## Tagging & Zenodo Release

1. Tag release candidate:
   ```bash
   git tag -a v0.1.0-rc1 -m "Release Candidate 1 for Journal Manuscript Submission"
   ```
2. Export source archive:
   ```bash
   git archive --format=zip --output=nkm-v0.1.0-rc1.zip v0.1.0-rc1
   ```
3. Zenodo Archival: Link GitHub repository to Zenodo for automatic DOI generation upon final tag push.
