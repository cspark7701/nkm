# Milestone 03 — RADIA Magnetic Field Map Ingestion & Validation

**Status**: COMPLETED  
**Date Completed**: 2026-07-24  

---

## 1. Executive Summary & Objective

The objective of Milestone 03 is to create robust 1D and 2D magnetic field map ingestion and evaluation modules (`src/nkm/fieldmap.py`, `src/nkm/kickmap.py`), enforce strict domain boundaries with no silent extrapolation, verify odd symmetry in $x$, and validate Lorentz force kick sign conventions.

---

## 2. Technical Implementation & Formulations

### 2.1 1D Field Map (`NKMFieldMap1D`)
- Ingests 1D longitudinal magnetic field profile $B_y(z)$ from `By.txt` (201 points) and `nkm_field.xlsx`.
- Uses `scipy.interpolate.interp1d` with `bounds_error=True` to prevent silent extrapolation outside $z \in [-0.2625, +0.2625]\text{ m}$.
- Peak field $B_y(0) = 0.1461\text{ T}$, total integrated field $\int B_y dz = 0.0767\text{ T}\cdot\text{m}$.

### 2.2 2D Integrated Kick Map (`NKMKickMap2D`)
- Ingests 2D integrated kick map $\Delta x'(x, y)$ and $\Delta y'(x, y)$ from `kickmap_file.txt` (201 $\times$ 201 grid over $x, y \in [-25.0, +25.0]\text{ mm}$).
- Uses `scipy.interpolate.RegularGridInterpolator` with `bounds_error=True` to raise `OutOfDomainError` if queried outside grid limits.
- Evaluates kick at nominal injection septum offset $x = -16.0\text{ mm}$: $\Delta x' = -5.7491\text{ mrad}$.
- Verifies zero field on stored beam axis ($x = 0.0\text{ mm}$): field residual $< 10^{-6}\text{ T}\cdot\text{m}$.

### 2.3 Symmetry & Lorentz Sign Verification
- **Odd Symmetry in $x$**: $\Delta x'(-x, y) = -\Delta x'(x, y)$ with symmetry residual error $< 10^{-12}$.
- **Lorentz Force Direction**: Deflection angle for relativistic electrons ($q = -e$) at negative offset ($x < 0$) is negative ($\Delta x' < 0$).

---

## 3. Key Implementation Files Created

- `src/nkm/fieldmap.py`: `NKMFieldMap1D` class, `load_1d_fieldmap()`, `validate_1d_fieldmap()`.
- `src/nkm/kickmap.py`: `NKMKickMap2D` class, `load_2d_kickmap()`, grid interpolation, and symmetry validators.
- `scripts/validate_nkm_fieldmap.py`: Field map validation CLI runner.
- `tests/test_fieldmap.py`: Unit and integration test suite for 1D/2D field map parsing, interpolation accuracy, domain protection, and symmetry.
- `docs/validation/nkm_fieldmap_validation.md`: Milestone 03 field map validation report.

---

## 4. Verification Command

```bash
python scripts/validate_nkm_fieldmap.py
pytest tests/test_fieldmap.py
```
