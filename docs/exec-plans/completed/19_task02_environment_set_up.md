# Milestone 19 — Task 02: Environment Setup & Installation Guide

**Author**: Chong Shik Park  
**Affiliation**: Department of Accelerator Science and Center for Accelerator Research, Korea University, Sejong, 30019 Republic of Korea

---

## 1. Executive Summary

Task 02 delivered a comprehensive setup procedure and installer instructions (`INSTALLATION.md`) targeting new users and clean environment deployments across different machines.

## 2. Work Completed

1. **Installation Documentation (`INSTALLATION.md`)**:
   - Detailed step-by-step instructions for repository cloning, virtual environment creation (`venv` / `conda`), dependency resolution, package installation in editable mode (`pip install -e .`), and running `pytest`.
2. **Environment Reproducibility**:
   - Included exact lockfile references (`requirements-lock.txt`) to guarantee deterministic package installation across platforms.
   - Tested environment initialization and package imports in clean virtual environments.

## 3. Protected Files Status

- Protected source files and scientific binary/data maps remained untouched and verified via `git status`.

## 4. Verification & Results

- Verified full installation workflow on Linux system environment.
- Pytest test runner executes cleanly with zero missing dependency errors.
