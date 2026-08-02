# Milestone 30 — Refactor #4: Centralized Publication Plotting Theme (`set_publication_style`)

**Author**: Chong Shik Park  
**Affiliation**: Department of Accelerator Science and Center for Accelerator Research, Korea University, Sejong, 30019 Republic of Korea

---

## 1. Executive Summary

This refactoring milestone implemented the centralized `set_publication_style()` function and `PUBLICATION_COLORS` color dictionary in `src/nkm/paper.py`. This ensures consistent font sizes, DPI, line widths, grid transparency, and color palettes across all publication figure generation routines.

## 2. Work Completed

1. **Centralized Style Configurator (`src/nkm/paper.py`)**:
   - Implemented `set_publication_style(font_size=10, dpi=300, use_latex_fonts=False)` which configures Matplotlib `rc_params` globally.
   - Defined `PUBLICATION_COLORS` dictionary specifying standard colors for optics functions (`beta_x`, `beta_y`, `dispersion`), aperture limits (`aperture`), and beam distributions (`injected`, `stored`, `ideal`, `fieldmap`).
   - Refactored `generate_paper_figures()` in `src/nkm/paper.py` to use `set_publication_style()` and `PUBLICATION_COLORS`.

2. **Package Exports (`src/nkm/__init__.py`)**:
   - Exported `set_publication_style` and `PUBLICATION_COLORS` in package root `src/nkm/__init__.py`.

3. **Unit Tests & Integration Validation (`tests/test_paper_pipeline.py`)**:
   - Added `test_set_publication_style` verifying `set_publication_style()` configuration of font sizes, DPI, and color palette definitions.
   - Verified 4/4 tests passing in `tests/test_paper_pipeline.py`.

## 3. Protected Files Status

- `NKM_radia.ipynb`: Unchanged
- `NKM_radia_y=0.ipynb`: Unchanged
- `nlk.py`: Unchanged
- `storage_ring.ipynb`: Unchanged
- `By.txt`, `kickmap_file.txt`, `K4GSR_HBIv4-1.mat`, `nkm_field.xlsx`: Unchanged
- All protected scientific data files verified untouched via `git status`.

## 4. Verification & Results

- **`test_paper_pipeline.py` Pass Rate**: 4 / 4 passed (100%).
- **Rule Compliance**: Zero remote pushes, zero remote GitHub Actions checks, 100% local operation.
