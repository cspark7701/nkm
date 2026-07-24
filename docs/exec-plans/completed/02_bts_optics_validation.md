# Milestone 02 — BTS Lattice Construction & Optics Propagation Validation

**Status**: COMPLETED  
**Date Completed**: 2026-07-24  

---

## 1. Executive Summary & Objective

The objective of Milestone 02 is to implement a modular Accelerator Toolbox (pyAT) BTS lattice model (`src/nkm/lattice.py`), construct exact linear transfer matrix propagation routines (`src/nkm/optics.py`), verify symplecticity of element transfer matrices, and implement the uncoupled 2D phase-space mismatch metric $\mathcal{M}_u$.

---

## 2. Mathematical Formulations & Requirements

### 2.1 Uncoupled Phase-Space Mismatch Metric

The 2D phase-space mismatch metric $\mathcal{M}_u$ ($u \in \{x, y\}$) evaluates exit Twiss parameters $(\beta_u, \alpha_u, \gamma_u)$ against storage ring injection target parameters $(\beta_{uT}, \alpha_{uT}, \gamma_{uT})$:

$$\mathcal{M}_u = \frac{1}{2} \operatorname{Tr}\left(\mathbf{\Sigma}_{uT}^{-1} \mathbf{\Sigma}_{u}\right) - 1 = \frac{1}{2} \left[ \frac{\beta_u}{\beta_{uT}} + \frac{\beta_{uT}}{\beta_u} + \frac{(\alpha_u \beta_{uT} - \alpha_{uT} \beta_u)^2}{\beta_u \beta_{uT}} \right] - 1$$

- $\mathcal{M}_u \ge 0$ is non-negative, and $\mathcal{M}_u = 0$ if and only if optics match perfectly.

### 2.2 Symplecticity Requirement

Every $6 \times 6$ linear transfer matrix $M$ along the transport line must satisfy the symplectic condition:

$$M^T J M = J, \quad J = \begin{bmatrix} 0 & 1 & 0 & 0 & 0 & 0 \\ -1 & 0 & 0 & 0 & 0 & 0 \\ 0 & 0 & 0 & 1 & 0 & 0 \\ 0 & 0 & -1 & 0 & 0 & 0 \\ 0 & 0 & 0 & 0 & 0 & 1 \\ 0 & 0 & 0 & 0 & -1 & 0 \end{bmatrix}$$

---

## 3. Verification & Key Results

- **Lattice Construction**: Built 36-element BTS transport line in `src/nkm/lattice.py`.
- **Symplecticity Check**: $\max |M^T J M - J| < 10^{-14}$ across all dipoles, quadrupoles, drifts, and full line transfer matrix.
- **Twiss Function Accuracy**: Twiss propagation via transfer matrices matches pyAT `at.linopt` output to within $< 10^{-12}$ relative difference.
- **Target Optics Benchmark**: Target values $\beta_{xT} = 2.3365\text{ m}$, $\beta_{yT} = 4.2562\text{ m}$, $\alpha_{xT} = -0.0163$, $\alpha_{yT} = 0.0178$, $D_{xT} = 0.0809\text{ m}$, $D_{pxT} = 0.0475\text{ rad}$.

---

## 4. Key Implementation Files Created

- `src/nkm/lattice.py`: Modular BTS pyAT lattice constructor `build_bts_lattice()`.
- `src/nkm/optics.py`: Twiss propagation, transfer matrix calculation, and `compute_mismatch_factor()`.
- `scripts/validate_bts_optics.py`: Optics propagation CLI validator and plot generator.
- `tests/test_optics.py`: Unit test suite verifying transfer matrices, symplecticity, and mismatch metrics.
- `docs/validation/bts_optics_validation.md`: Milestone 02 optics validation report.

---

## 5. Verification Command

```bash
python scripts/validate_bts_optics.py
pytest tests/test_optics.py
```
