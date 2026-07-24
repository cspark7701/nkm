# NKM Multi-Turn Storage Ring Injection Validation Report

## 1. Executive Summary

This document specifies the physical multi-turn storage ring injection dynamics, physical aperture tracking, and performance metrics for the NKM injection system. Single-pass separation proxies are replaced by physical multi-turn tracking through the storage ring lattice (`storage_ring_lattice_nkm.mat`).

---

## 2. Kicker Model Comparisons

Four kicker models are evaluated consistently for both injected and circulating stored beams:

| Kicker Model | Description | Turn 1 Kicker Action | Turns 2+ Kicker Action | Injected Beam Capture | Stored Beam Perturbation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Model 1: NKM Off** | Zero magnetic field | No kick | Zero kick | Uncaptured ($0\%$) | $0.0\text{ mm}$ (Zero) |
| **Model 2: Ideal Kicker** | Constant dipole kick | $-5.7491\text{ mrad}$ uniform kick | Zero kick | High ($100\%$) | $0.0\text{ mm}$ (Zero) |
| **Model 3: Linearized NKM** | Local dipole + quad gradient | Dipole + linear $K_1$ gradient | Zero kick | High ($100\%$) | Small oscillation |
| **Model 4: RADIA Fieldmap NKM** | Full 2D integrated field map | Non-linear 2D field map | Zero kick | High ($100\%$) | Minimal oscillation |

---

## 3. Physical Apertures & Loss Accounting

- **Horizontal Aperture**: $x \in [-30\text{ mm}, +30\text{ mm}]$
- **Vertical Aperture**: $y \in [-15\text{ mm}, +15\text{ mm}]$
- **Septum Position**: $x_{\text{septum}} = -16.0\text{ mm}$ (blade thickness $2.0\text{ mm}$)
- **Loss Categorization**: Each particle loss is logged with turn number, element index, and cause (`aperture_exceeded`, `septum_impact`, `domain_out_of_bounds`).

---

## 4. Multi-Turn Injection Performance Metrics

- **Capture Efficiency ($\eta_{\text{cap}}$)**: Percentage of injected beam distribution surviving inside the physical acceptance after $N_{\text{turns}}$.
- **Loss Fraction ($f_{\text{loss}}$)**: $1.0 - \eta_{\text{cap}}$.
- **Stored Beam Centroid Oscillation ($\Delta x_{\text{stored}}$)**: Peak-to-peak amplitude of the stored beam centroid oscillation over $N_{\text{turns}}$.
- **Stored Beam Emittance Growth ($\Delta \epsilon_x / \epsilon_x$)**: Relative percentage increase in geometric emittance after passage of the kicker.
- **Septum Clearance ($d_{\text{clear}}$)**: Distance between the injected beam centroid and septum blade at turn 1.

---

## 5. Artifacts and Results Location

Generated JSON execution summaries and scan tables are saved under:
`results/multiturn_injection/run_<timestamp>/`
- `multiturn_injection_summary.json`
