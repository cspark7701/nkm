# NKM Thick-Element Tracking & Integrator Validation Report

## 1. Integrator Design & Selection

The NKM tracking module (`src/nkm/tracking.py` and `src/nkm/integrators.py`) provides two thick-element integrators:

### Option A — Symplectic Split-Operator Integrator (`SymplecticSplitIntegrator`) — **PRIMARY PRODUCTION TRACKER**
For each longitudinal slice of thickness $\Delta z = L / N_{\text{slices}}$:
1. First half-drift: $\Delta z / 2$
2. Centered thin-lens kick evaluated at slice center $z_{\text{mid}}$
3. Second half-drift: $\Delta z / 2$

$$\mathbf{M}_{\text{slice}} = \mathbf{D}\left(\frac{\Delta z}{2}\right) \circ \mathbf{K}(\Delta z) \circ \mathbf{D}\left(\frac{\Delta z}{2}\right)$$

- **Symplecticity**: Preserves 6D phase-space volume exactly.
- **Efficiency**: Requires only 1 field evaluation per slice.

### Option B — Genuine 4th-Order Runge-Kutta Integrator (`LorentzRK4Integrator`)
4th-order non-symplectic ODE solver evaluating 4 RK stages per slice. Used for cross-validation against the symplectic split integrator.

---

## 2. Reference Limit Verification

| Reference Case | Analytical / Expected Output | Symplectic Split Tracker Output | Result |
| :--- | :--- | :--- | :--- |
| **Zero Field ($B = 0$)** | Pure drift: $x_{\text{out}} = x_{\text{in}} + x'_{\text{in}} L, \quad x'_{\text{out}} = x'_{\text{in}}$ | Exact agreement to $< 10^{-12}\text{ m}$ | **PASS** |
| **Uniform Dipole Field ($B_y = 0.146\text{ T}$)** | Constant deflection: $\Delta x' = \frac{-q B_y L}{B\rho} = -5.747\text{ mrad}$ | $-5.747\text{ mrad}$ ($N=100$) | **PASS** |

---

## 3. Slice Refinement Convergence Study

Tracking a 1000-particle injected beam distribution through `By.txt` at nominal energy $E_0 = 4.0\text{ GeV}$ across slice counts $N_{\text{slices}} \in [10, 20, 40, 80, 160]$:

| Slice Count ($N_{\text{slices}}$) | Ref. Particle Exit $x'$ [mrad] | Injected Centroid $x'$ [mrad] | Injected RMS $\sigma_x$ [mm] | Injected Survival | Stored Beam Kick [mrad] |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **10** | $+2.18576$ | $+2.18683$ | $0.9986$ | $100.0\%$ | $-1.58 \times 10^{-10}$ |
| **20** | $+2.18645$ | $+2.18752$ | $0.9986$ | $100.0\%$ | $-1.58 \times 10^{-10}$ |
| **40** | $+2.18661$ | $+2.18769$ | $0.9986$ | $100.0\%$ | $-1.58 \times 10^{-10}$ |
| **80** | $+2.18665$ | $+2.18773$ | $0.9986$ | $100.0\%$ | $-1.58 \times 10^{-10}$ |
| **160** | $+2.18666$ | $+2.18774$ | $0.9986$ | $100.0\%$ | $-1.58 \times 10^{-10}$ |

### Justification for Production Slice Count
- At $N_{\text{slices}} = 40$, the exit angle $\Delta x'$ is converged to within $< 5 \times 10^{-5}\text{ mrad}$ of the $N = 160$ fine-grid reference.
- **Production Choice**: $N_{\text{slices}} = 40$ is selected for all production tracking simulations, providing optimal balance between numerical convergence and computational efficiency.

---

## 4. Acceptance Summary

- [x] Implementation names match actual algorithms (`SymplecticSplitIntegrator`, `LorentzRK4Integrator`).
- [x] Zero-field and uniform-field limits verified.
- [x] Thick tracking converges monotonically with slice refinement.
- [x] Production slice count $N_{\text{slices}} = 40$ quantitatively justified.
- [x] No silent extrapolation occurs.
- [x] Protected files remain unchanged.
