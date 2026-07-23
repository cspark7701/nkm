# BTS Lattice & Linear Optics Validation Report — Milestone 2

## Executive Summary

This report documents the validation of the Booster-to-Storage Ring (BTS) transfer line lattice model in Accelerator Toolbox (AT), as specified in Milestone 2 of the refactoring roadmap. The lattice construction, Twiss parameter propagation, transfer matrix symplecticity, and phase-space mismatch metrics $\mathcal{M}_x, \mathcal{M}_y$ have been modularized under `src/nkm/` and verified with automated unit tests.

---

## 1. AT Lattice Architecture (`src/nkm/bts_lattice.py`)

The BTS line lattice is constructed via `create_bts_lattice(config: BTSConfig)`, which encapsulates all physical and optical parameters:

- **Beam Energy**: $E_0 = 4.0\text{ GeV}$ ($\gamma = 7827.8$)
- **Total Line Length**: $L_{\text{total}} = 21.789\text{ m}$
- **Total Element Count**: 36 elements across 32 unique families
- **Bending Elements**:
  - `kext`: Extraction kicker ($L = 0.310\text{ m}$, $\theta = +7.500\text{ mrad}$)
  - `sept_in`: Injection septum ($L = 1.000\text{ m}$, $\theta = +88.500\text{ mrad}$)
  - `b1`: Dipole 1 ($L = 1.400\text{ m}$, $\theta = -111.701\text{ mrad}$)
  - `b2`: Dipole 2 ($L = 1.400\text{ m}$, $\theta = +176.000\text{ mrad}$)
  - `b3`: Dipole 3 ($L = 1.400\text{ m}$, $\theta = -111.701\text{ mrad}$)
  - `sept_ex`: Extraction septum ($L = 1.000\text{ m}$, $\theta = +88.500\text{ mrad}$)
- **Quadrupoles**: 9 quadrupoles ($L = 0.200\text{ m}$ each) organized into 3 triplets (`q11..q13`, `q21..q23`, `q31..q33`).

---

## 2. Health & Symplecticity Validation Checks

All physical health checks are executed automatically via `validate_bts_lattice()`:

| Check Item | Criteria / Threshold | Result | Status |
| :--- | :--- | :--- | :--- |
| **Total Length** | $L = 21.789\text{ m}$ | $21.789000\text{ m}$ | **PASSED** |
| **Element Count** | 36 elements | 36 elements | **PASSED** |
| **Total Dipole Bend Sum** | $\sum \theta_i \approx 7.855^\circ$ | $7.855498^\circ$ ($0.137098\text{ rad}$) | **PASSED** |
| **Transfer Matrix Finiteness** | No NaN/Inf values | Finite | **PASSED** |
| **$M_{44}$ Symplecticity Error** | $\|M_{44}^T J M_{44} - J\|_\infty < 10^{-10}$ | $2.442 \times 10^{-15}$ | **PASSED** |
| **$M_{66}$ Symplecticity Error** | $\|M_{66}^T J M_{66} - J\|_\infty < 10^{-10}$ | $2.074 \times 10^{-12}$ | **PASSED** |
| **Aperture Limits** | Positive bounds | $19.35\text{ mm}$ & $30.00\text{ mm}$ | **PASSED** |

---

## 3. Uncoupled Twiss Propagation & Phase Space Mismatch

Linear optics are computed using `compute_bts_optics_metrics()` with initial Twiss parameters at the BTS entrance:

$$\beta_{x,0} = 7.560\text{ m}, \quad \alpha_{x,0} = 1.5231, \quad D_{x,0} = 0.2762\text{ m}, \quad D_{x,0}' = -0.0657$$
$$\beta_{y,0} = 12.269\text{ m}, \quad \alpha_{y,0} = -1.6547$$

### Phase-Space Mismatch Metric $\mathcal{M}_u$

The plane-by-plane mismatch metric relative to the storage ring target optics $\Sigma_{u,\text{target}}$ is defined as:

$$\mathcal{M}_{u} = \frac{1}{2} \mathrm{Tr}\left(\Sigma_{u,\text{target}}^{-1} \Sigma_{u,\text{out}}\right) - 1, \quad u \in \{x, y\}$$

| Plane | Output Twiss at BTS Exit | Target Injection Twiss | Mismatch Metric $\mathcal{M}_u$ |
| :--- | :--- | :--- | :--- |
| **Horizontal ($x$)** | $\beta_x = 44.9808\text{ m}$, $\alpha_x = 0.6248$ | $\beta_{x,\text{target}} = 2.3365\text{ m}$, $\alpha_{x,\text{target}} = -0.0163$ | $\mathcal{M}_x = 8.6746$ |
| **Vertical ($y$)** | $\beta_y = 242.6069\text{ m}$, $\alpha_y = -10.2146$ | $\beta_{y,\text{target}} = 4.2562\text{ m}$, $\alpha_{y,\text{target}} = 0.0178$ | $\mathcal{M}_y = 28.6147$ |
| **Dispersion ($D_x$)**| $D_x = 0.0809\text{ m}$, $D_x' = 0.0475$ | $D_{x,\text{target}} = 0.0809\text{ m}$, $D_{x,\text{target}}' = 0.0475$ | $\Delta D_x = 0.0000\text{ m}$ |

> **Note**: The baseline lattice quadrupoles produce significant mismatch ($\mathcal{M}_x \approx 8.67$, $\mathcal{M}_y \approx 28.61$), establishing the exact quantitative baseline to be optimized in Milestone 4.

---

## 4. AT Model vs. `bts.madx` Comparison

A comparison between the authoritative AT model (`bts.ipynb`) and the reference input `bts.madx`:

1. **Quadrupole Count & Family Structure**:
   - AT Model: 9 quadrupoles (`q11`, `q12`, `q13`, `q21`, `q22`, `q23`, `q31`, `q32`, `q33`), allowing individual family control for optics matching.
   - `bts.madx`: Preliminary 10-quadrupole sequence (`Q11..Q13`, `Q21..Q23`, `Q31..Q34`).
2. **Quadrupole Strengths**:
   - `bts.madx` contains initial estimated gradients ($K_1$ values up to $4.13\text{ m}^{-2}$).
   - AT model uses tuned baseline strengths ($K_{11} = 0.448572\text{ m}^{-2}$, $K_{12} = -1.026778\text{ m}^{-2}$, etc.) yielding stable propagation across the line.
3. **Drift Allocations**: Drift lengths are consistent between models for total line length $\approx 21.79\text{ m}$.

---

## 5. Summary of Deliverables

- **`src/nkm/bts_lattice.py`**: Modular lattice constructor, config, and symplecticity validation.
- **`src/nkm/optics.py`**: Twiss propagation, $\mathcal{M}_u$ mismatch calculation, and plotting.
- **`scripts/validate_bts_optics.py`**: CLI script for optics validation and figure generation.
- **`tests/test_bts_lattice.py`**: 12 automated unit and integration tests.
- **`results/optics_validation/bts_optics_functions.png`**: Publication plot of optics functions.
