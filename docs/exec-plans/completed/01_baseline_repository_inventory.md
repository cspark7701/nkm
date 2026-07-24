# Milestone 01 — Baseline Repository Safeguards & Inventory

**Status**: COMPLETED  
**Date Completed**: 2026-07-24  

---

## 1. Executive Summary & Objective

The objective of Milestone 01 is to establish a rigorous, reproducible baseline for the NKM (Nonlinear Kicker Magnet) and BTS (Booster-to-Storage Ring) beam transport line codebase. This includes creating a protected scientific input file hash inventory, establishing unit conversion and physics standards, and computing unoptimized reference baseline optics and field metrics.

---

## 2. Protected Source Data Manifest

All scientific source input files, RADIA calculations, and reference notebooks are protected against modification. SHA256 hashes are recorded in `results/baseline/protected_files_manifest.json`.

| Source File | Type | SHA256 Prefix | Status |
| :--- | :--- | :--- | :--- |
| `By.txt` | Text Source | `fa7be11ac01a` | Verified |
| `NKM_radia.ipynb` | Jupyter Notebook | `fd5baecc9c09` | Verified |
| `NKM_radia_y=0.ipynb` | Jupyter Notebook | `539fac23a122` | Verified |
| `acceptance.npy` | NumPy Binary | `98c3956f0fda` | Verified |
| `kickmap_file.txt` | Text Source | `5c1a3f1437ce` | Verified |
| `nkm_field.xlsx` | Excel Spreadsheet | `5f33595443c6` | Verified |
| `nkm_field_expanded.xlsx` | Excel Spreadsheet | `046033b23824` | Verified |
| `nlk.py` | Python Reference | `0e0f0610c71e` | Verified |
| `storage_ring.ipynb` | Jupyter Notebook | `a1f404a2e192` | Verified |

---

## 3. Baseline Unoptimized Metrics

- **Beam Energy**: $4.0\text{ GeV}$ ($\gamma \approx 7827.79$)
- **BTS Lattice Length**: $21.789\text{ m}$ (36 elements)
- **Entrance Twiss Parameters**: $(\beta_{x0}, \beta_{y0}) = (7.5600, 12.2690)\text{ m}$, $(\alpha_{x0}, \alpha_{y0}) = (1.5231, -1.6547)$, $(D_{x0}, D_{px0}) = (0.2762\text{ m}, -0.0657\text{ rad})$
- **Baseline Exit Twiss Parameters**: $(\beta_{x}, \beta_{y}) = (44.9808, 242.6069)\text{ m}$
- **Baseline Optical Mismatch**: $\mathcal{M}_x = 8.6746$, $\mathcal{M}_y = 28.6147$ ($\text{Total } \mathcal{M}_x + \mathcal{M}_y = 37.2893$)
- **Peak Beta Violation**: Vertical peak $\beta_{y,\max} = 242.6069\text{ m}$ (violates physical aperture limit of $60.0\text{ m}$)
- **NKM RADIA Parameters**: Length $L_{\text{NKM}} = 0.525\text{ m}$, peak field $B_y = 0.1461\text{ T}$, integrated field $\int B_y ds = 0.0767\text{ T}\cdot\text{m}$, nominal kick $\Delta x' = -5.7491\text{ mrad}$ at $x = -16.0\text{ mm}$.

---

## 4. Key Implementation Files Created

- `scripts/inventory_protected_hashes.py`: Script to generate and verify SHA256 manifest.
- `scripts/record_baseline_metrics.py`: Script to extract and record baseline metrics.
- `src/nkm/units.py`: Internal canonical physics units definition (m, rad, eV, T, T·m).
- `tests/test_baseline.py`: Unit test verifying protected hashes and baseline values.

---

## 5. Verification Command

```bash
python scripts/inventory_protected_hashes.py
python scripts/record_baseline_metrics.py
pytest tests/test_baseline.py
```
