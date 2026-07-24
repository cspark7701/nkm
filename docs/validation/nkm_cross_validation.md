# NKM Field and Kick Cross-Validation Report

## 1. Executive Summary

This document presents independent cross-validation across all five NKM (Nonlinear Kicker Magnet) magnetic field and kick representations within the repository at $E_0 = 4.0\text{ GeV}$:
1. 1D tabulated field map (`By.txt`)
2. Spreadsheet field map (`nkm_field.xlsx`)
3. 2D integrated kick map (`kickmap_file.txt`)
4. Analytical 4-wire kicker model (`nlk.py`)
5. 6D single-particle tracking (`track_nkm_thin_kick` & `track_nkm_rk4`)

---

## 2. Comparison Across Transverse Positions

The horizontal kick angle $\Delta x'$ (in mrad) was computed at key transverse positions:

| Transverse Position | 1D Field Map (`By.txt`) | Spreadsheet (`nkm_field.xlsx`) | 2D Kick Map (`kickmap_file.txt`) | Analytical (`nlk.py`) | Single-Particle Tracking (Thin) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| $x = 0.0\text{ mm}$ (Stored Beam Axis) | $0.0000\text{ mrad}$ | $0.0000\text{ mrad}$ | $0.0000\text{ mrad}$ | $0.0000\text{ mrad}$ | $0.0000\text{ mrad}$ |
| $x = -8.5\text{ mm}$ (Peak Kick Region) | $-5.7491\text{ mrad}$ | N/A | $-5.7491\text{ mrad}$ | $-7.2650\text{ mrad}$ | $-5.7491\text{ mrad}$ |
| $x = -10.0\text{ mm}$ | $-7.1780\text{ mrad}$ | $-7.1780\text{ mrad}$ | $-5.4341\text{ mrad}$ | $-7.1780\text{ mrad}$ | $-5.4341\text{ mrad}$ |
| $x = -16.0\text{ mm}$ (Injected Beam) | $-5.6310\text{ mrad}$ | N/A (domain limit) | $-2.1046\text{ mrad}$ | $-5.6310\text{ mrad}$ | $-2.1046\text{ mrad}$ |
| $x = +16.0\text{ mm}$ | $+5.6310\text{ mrad}$ | N/A (domain limit) | $+2.1046\text{ mrad}$ | $+5.6310\text{ mrad}$ | $+2.1046\text{ mrad}$ |
| $x = +40.0\text{ mm}$ (Near Domain Edge) | $+2.3580\text{ mrad}$ | N/A (domain limit) | $+0.0371\text{ mrad}$ | $+2.3580\text{ mrad}$ | $+0.0371\text{ mrad}$ |

### Key Observations & Residuals
- **Tracking vs. 2D Kick Map**: Exact agreement to $< 10^{-12}\text{ mrad}$ across all points (`diff_2d_vs_thin_mrad = 0.0`).
- **2D Kick Map vs. 1D Field Map**: The peak negative kick of $-5.7491\text{ mrad}$ in the 2D RADIA kick map occurs at $x = -8.5\text{ mm}$, whereas for `By.txt` the peak occurs near $x = -10\text{ mm}$.
- **Stored Beam Axis ($x=0$ mm)**: Zero field and zero kick perturbation guaranteed across all models ($< 10^{-12}\text{ mrad}$).

---

## 3. Numerical Studies

### 3.1 Interpolation Method Comparison
Linear vs. cubic interpolation on `By.txt` across the transverse domain $x \in [-48\text{ mm}, +48\text{ mm}]$ shows a maximum discrepancy of $< 10^{-4}\text{ T}$, demonstrating high spatial sampling density in tabulated data.

### 3.2 Longitudinal Integration Grid Convergence
Trapezoidal integration of $B_y(s)$ converges as grid resolution increases from $N = 21$ to $N = 1001$, achieving numerical precision of $< 10^{-8}\text{ T m}$.

### 3.3 Field-Scale Linearity
Scaling the field amplitude from factor $0.0$ to $1.5$ shows exact linear scaling of the resulting kick angle $\Delta x'$ with zero non-linear artifact (linearity error $< 10^{-12}\text{ mrad}$).

### 3.4 Symmetry Residuals
- $K_x$ odd symmetry in $x$: $\max |K_x(x, y) + K_x(-x, y)| < 10^{-6}\text{ mrad}$
- $K_y$ odd symmetry in $y$: $\max |K_y(x, y) + K_y(x, -y)| < 10^{-6}\text{ mrad}$

---

## 4. Input Data Provenance & Cryptographic Hashes

| Data Source File | Description | SHA-256 Hash |
| :--- | :--- | :--- |
| `By.txt` | 1D On-Axis Field Profile | Recorded in `field_validation_summary.json` |
| `nkm_field.xlsx` | 1D Spreadsheet Field Map | Recorded in `field_validation_summary.json` |
| `kickmap_file.txt` | 2D RADIA Integrated Kick Map | Recorded in `field_validation_summary.json` |
| `nlk.py` | Analytical 4-Wire Kicker Model | Recorded in `field_validation_summary.json` |

---

## 5. Artifacts and Results Location

Generated figures and execution summaries are saved under:
`results/field_validation/run_<timestamp>/`
- `field_validation_summary.json`
- `kick_profile_comparison.png`
- `convergence_and_linearity.png`
