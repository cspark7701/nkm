# Milestone 27 — Refactor #1: BaseFieldMap Unified Abstract Base Class

**Author**: Chong Shik Park  
**Affiliation**: Department of Accelerator Science and Center for Accelerator Research, Korea University, Sejong, 30019 Republic of Korea

---

## 1. Executive Summary

This refactoring milestone established the unified abstract base class `BaseFieldMap` in `src/nkm/fieldmap.py` for all 1D and 2D magnetic field and transverse kick map evaluators. Both `NKMFieldMap1D` and `NKMKickMap2D` now inherit from `BaseFieldMap`, eliminating code duplication in domain boundary checking, metadata handling, and file SHA-256 cryptographic hash verification.

## 2. Work Completed

1. **`BaseFieldMap` Abstract Base Class (`src/nkm/fieldmap.py`)**:
   - Encapsulated domain bounds attributes (`x_min`, `x_max`, `y_min`, `y_max`), `allow_extrapolation` flag, metadata handling (`KickMapMetadata`), and file path tracking.
   - Centralized 1D/2D domain bounds validation via `check_domain_bounds(x, y)` which raises `OutOfDomainError` when coordinates fall outside tabulated bounds and extrapolation is disabled.
   - Added `compute_file_hash()` and `verify_file_hash(expected_hash)` methods for SHA-256 cryptographic verification of map files.
   - Added `domain_bounds` property returning a dictionary of valid coordinate ranges.

2. **Class Refactoring (`src/nkm/fieldmap.py` & `src/nkm/kickmap.py`)**:
   - Refactored `NKMFieldMap1D` to inherit from `BaseFieldMap`.
   - Refactored `NKMKickMap2D` to inherit from `BaseFieldMap`.
   - Exported `BaseFieldMap` in package root `src/nkm/__init__.py`.

3. **Unit & Integration Test Suite (`tests/test_fieldmap.py`)**:
   - Added `test_base_fieldmap_inheritance_and_hashing` testing inheritance, `domain_bounds` property, and SHA-256 checksum verification against `By.txt` (`fa7be11a...`) and `kickmap_file.txt` (`5c1a3f14...`).
   - Verified 10/10 tests passing in `tests/test_fieldmap.py`.

## 3. Protected Files Status

- `NKM_radia.ipynb`: Unchanged
- `NKM_radia_y=0.ipynb`: Unchanged
- `nlk.py`: Unchanged
- `storage_ring.ipynb`: Unchanged
- `By.txt`, `kickmap_file.txt`, `K4GSR_HBIv4-1.mat`, `nkm_field.xlsx`: Unchanged
- All protected scientific files verified untouched via `git status`.

## 4. Verification & Results

- **`test_fieldmap.py` Pass Rate**: 10 / 10 passed (100%).
- **Backward Compatibility**: 100% non-breaking API compatibility across all existing tracking and optimization callers.
- **Rule Compliance**: Zero remote pushes, zero remote GitHub Actions checks, 100% local operation.
