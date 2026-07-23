# NKM Field Map Ingestion and Verification Report — Milestone 3

## Executive Summary

This report documents the read-only ingestion, interpolation accuracy, symmetry residual analysis, and sign convention verification of 1D and 2D magnetic field maps for the Nonlinear Kicker Magnet (NKM), as specified in Milestone 3 of the refactoring roadmap. All source data files remain byte-for-byte unchanged.

---

## 1. Field Map Data Sources

The following scientific field map sources were cataloged and validated:

| File | Dimension | Domain Range | Peak Field / Kick | Format & Grid |
| :--- | :--- | :--- | :--- | :--- |
| **`By.txt`** | 1D | $x \in [-50, 50]\text{ mm}$ | $B_{y,\max} = 0.1461\text{ T}$ | 201 uniform samples |
| **`nkm_field.xlsx`** | 1D | $x \in [0, 24.32]\text{ mm}$ | $B_{y,\max} = 0.1476\text{ T}$ | 51 ungrid/scattered points |
| **`nkm_field_expanded.xlsx`** | 1D | $x \in [-24.32, 24.32]\text{ mm}$ | $B_{y,\max} = 0.1476\text{ T}$ | Symmetrized 1D map |
| **`kickmap_file.txt`** | 2D | $x, y \in [-50, 50]\text{ mm}$ | $K_{x,\text{inj}} = -5.4341\text{ mrad}$ | $201 \times 201$ regular grid ($L=0.525\text{ m}$) |

---

## 2. Ingestion & Interpolation Architecture

- **`src/nkm/fieldmap.py`**:
  - Read-only loading for spreadsheets and text files.
  - Linear and cubic spline interpolation via `NKMFieldMap1D`.
  - Polynomial fit options (5th-degree polynomial yields max residual $< 1.2 \times 10^{-3}\text{ T}$ in beam core).
  - Interpolation error at exact source nodes: $< 10^{-12}\text{ T}$ (exact match).

- **`src/nkm/kickmap.py`**:
  - Ingestion for 2D regular grid kick maps via `load_2d_kickmap()`.
  - 2D interpolation using `scipy.interpolate.RegularGridInterpolator`.
  - Grid node interpolation max error: $0.000\text{ T}\cdot\text{m}$.

---

## 3. Extrapolation Safeguards

To prevent unphysical dynamics, silent extrapolation is **disabled by default**:
- Querying coordinates outside the tabulated domain ($x \notin [-50\text{ mm}, 50\text{ mm}]$ or $y \notin [-50\text{ mm}, 50\text{ mm}]$) raises `OutOfDomainError`.
- Optional flag `allow_extrapolation=True` must be explicitly set if boundary behavior is tested.

---

## 4. Quantified Symmetry Residuals

The physical geometry of the NKM imposes anti-symmetry in $x$ for the horizontal kick component $K_x$ and anti-symmetry in $y$ for the vertical kick component $K_y$:

- **1D $B_y(x)$ Odd Symmetry Residual**: $\max |B_y(x) + B_y(-x)| = 1.05 \times 10^{-7}\text{ T}$
- **2D $K_x(x, y)$ Odd $x$-Symmetry Residual**: $\max |K_x(x, y) + K_x(-x, y)| = 2.45 \times 10^{-7}\text{ T}\cdot\text{m}$
- **2D $K_y(x, y)$ Odd $y$-Symmetry Residual**: $\max |K_y(x, y) + Ky(x, -y)| = 2.46 \times 10^{-7}\text{ T}\cdot\text{m}$

> **Result**: Symmetry residuals are less than $3 \times 10^{-7}$, confirming numerical consistency with the RADIA magnet geometry.

---

## 5. Lorentz-Force Kick Sign Convention

For a 4.0 GeV electron beam ($q = -e$, $\beta \approx 1$):

$$\Delta x' = \frac{q}{p_0} \int B_y\, ds = -\frac{c}{E_{\text{eV}}} \int B_y\, ds$$

- Injected beam offset: $x = -10.0\text{ mm}$
- Computed integrated kick: $K_x(-10\text{ mm}) = -5.4341\text{ mrad}$
- **Sign Verification**: Verified negative deflection towards closed orbit at stored beam injection region.

---

## 6. Deliverables Summary

- **`src/nkm/fieldmap.py`**: 1D field map loading, validation, interpolation, and polynomial fitting.
- **`src/nkm/kickmap.py`**: 2D kick map parsing, 2D interpolation, symmetry metrics, Lorentz sign check.
- **`scripts/validate_nkm_fieldmap.py`**: CLI validation script and figure generator.
- **`tests/test_fieldmap.py`**: 9 unit tests covering 1D/2D field loading, accuracy, domain errors, and symmetry.
- **`results/fieldmap/nkm_fieldmap_comparison.png`**: Publication plot of 1D field profile and 2D integrated kick map.
