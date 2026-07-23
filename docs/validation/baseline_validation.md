# Baseline Validation Report — Milestone 1

## Overview

This report documents the baseline physics metrics, lattice configuration, and protected file integrity manifest for the NKM and BTS simulation repository prior to optics optimization and tracking refactoring.

---

## 1. Protected File Verification

All scientific source files, pre-calculated field maps, and reference notebooks are protected against unintended modification. Checksums are recorded in `results/baseline/protected_files_manifest.json`.

| File | Type | SHA256 Prefix | Verification Status |
| :--- | :--- | :--- | :--- |
| `By.txt` | Text | `fa7be11ac01a` | Passed |
| `NKM_radia.ipynb` | Jupyter Notebook | `fd5baecc9c09` | Passed |
| `NKM_radia_y=0.ipynb` | Jupyter Notebook | `539fac23a122` | Passed |
| `acceptance.npy` | NumPy Binary | `98c3956f0fda` | Passed |
| `kickmap_file.txt` | Text | `5c1a3f1437ce` | Passed |
| `nkm_field.xlsx` | Excel Spreadsheet | `5f33595443c6` | Passed |
| `nkm_field_expanded.xlsx` | Excel Spreadsheet | `046033b23824` | Passed |
| `nlk.py` | Python Script | `0e0f0610c71e` | Passed |
| `storage_ring.ipynb` | Jupyter Notebook | `a1f404a2e192` | Passed |

---

## 2. BTS Baseline Lattice & Optics

- **Total Lattice Length**: $21.789$ m
- **Element Count**: 36 elements across 32 unique families
- **Beam Energy**: $4.0$ GeV ($\gamma \approx 7827.8$)

### Linear Optics Metrics

| Parameter | Initial (BTS Entrance) | Final (BTS Exit) | Peak Maximum |
| :--- | :--- | :--- | :--- |
| $\beta_x$ | $7.5600$ m | $44.9808$ m | $52.2480$ m |
| $\beta_y$ | $12.2690$ m | $242.6069$ m | $242.6069$ m |
| $\alpha_x$ | $1.5231$ | $0.6248$ | — |
| $\alpha_y$ | $-1.6547$ | $-10.2146$ | — |
| $D_x$ | $0.2762$ m | $0.0809$ m | $0.3541$ m |
| $D_x'$ | $-0.0657$ rad | $0.0475$ rad | — |

---

## 3. Particle Tracking & NKM Field Metrics

- **Particle Ensemble**: 1,000 particles tracked through 1 turn of the BTS lattice.
- **Particle Survival Rate**: $100.0\%$ (1,000 / 1,000 survived).
- **Minimum Horizontal Aperture Margin**: $95.97\%$
- **Minimum Vertical Aperture Margin**: $91.60\%$
- **NKM Magnet Length**: $0.525$ m
- **NKM Peak Field ($B_y$)**: $0.1461$ T
- **NKM Integrated Field ($\int B_y ds$)**: $0.0767$ T·m
- **NKM Nominal Horizontal Kick ($\Delta x'$)**: $5.7491$ mrad

---

## 4. Reproducibility

To re-verify the baseline metrics and protected file hashes from a clean environment:

```bash
# 1. Verify protected files hash manifest
python scripts/inventory_protected_hashes.py

# 2. Record baseline metrics
python scripts/record_baseline_metrics.py

# 3. Run automated tests
pytest
```
