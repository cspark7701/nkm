"""
NKM Integrators Module — Symplectic Split and Lorentz RK4 Integrators

Provides centered drift-kick-drift (symplectic split-operator) and 4th-order Runge-Kutta
numerical integrators for tracking relativistic beam distributions through thick magnetic elements.
"""

from typing import Dict, Tuple, Optional, Any, Callable, Union
import numpy as np

from .units import compute_rigidity, ELECTRON_CHARGE_C, KickMapMetadata


class SymplecticSplitIntegrator:
    """
    Symplectic Split-Operator Integrator (Drift-Kick-Drift map per slice).
    
    Order: 2nd-order Symplectic (Verlet).
    For each longitudinal slice of thickness dz = L / N_slices:
      1. Half-drift dz / 2
      2. Centered thin kick at slice center z_mid
      3. Half-drift dz / 2
    """
    def __init__(self, field_fn: Callable[[np.ndarray, np.ndarray, float], Tuple[np.ndarray, np.ndarray]],
                 length_m: float = 0.525,
                 n_slices: int = 40,
                 energy_GeV: float = 4.0,
                 particle_charge_C: float = ELECTRON_CHARGE_C,
                 scale_factor: float = 1.0):
        self.field_fn = field_fn
        self.length_m = length_m
        self.n_slices = n_slices
        self.energy_GeV = energy_GeV
        self.particle_charge_C = particle_charge_C
        self.scale_factor = scale_factor

        self.energy_eV = energy_GeV * 1e9
        self.brho = compute_rigidity(self.energy_eV, particle_charge_C)
        self.charge_sign = float(np.sign(particle_charge_C))
        self.dz = length_m / n_slices

    def track(self, beam: np.ndarray) -> np.ndarray:
        """
        Track 6D particle array of shape (6, n_particles) through N_slices.
        """
        out_beam = beam.copy()
        valid_mask = ~np.isnan(out_beam[0, :])
        if not np.any(valid_mask):
            return out_beam

        dz = self.dz
        half_dz = dz * 0.5

        for i in range(self.n_slices):
            z_mid = (i + 0.5) * dz

            # 1. Half drift dz / 2
            out_beam[0, valid_mask] += out_beam[1, valid_mask] * half_dz
            out_beam[2, valid_mask] += out_beam[3, valid_mask] * half_dz

            # 2. Centered kick at z_mid
            x = out_beam[0, valid_mask]
            y = out_beam[2, valid_mask]

            by_val, bx_val = self.field_fn(x, y, z_mid)
            by_val = by_val * self.scale_factor
            bx_val = bx_val * self.scale_factor

            # Deflection angles in radians
            # Delta x' = (q / |q|) * (By * dz) / B_rho
            # Delta y' = - (q / |q|) * (Bx * dz) / B_rho
            delta_xp = self.charge_sign * (by_val * dz) / self.brho
            delta_yp = - self.charge_sign * (bx_val * dz) / self.brho

            out_beam[1, valid_mask] += delta_xp
            out_beam[3, valid_mask] += delta_yp

            # 3. Half drift dz / 2
            out_beam[0, valid_mask] += out_beam[1, valid_mask] * half_dz
            out_beam[2, valid_mask] += out_beam[3, valid_mask] * half_dz

        return out_beam


class LorentzRK4Integrator:
    """
    Genuine 4th-Order Runge-Kutta (RK4) Lorentz Force Integrator.
    
    Non-symplectic 4th-order ODE integrator for 6D particle trajectories.
    """
    def __init__(self, field_fn: Callable[[np.ndarray, np.ndarray, float], Tuple[np.ndarray, np.ndarray]],
                 length_m: float = 0.525,
                 n_slices: int = 40,
                 energy_GeV: float = 4.0,
                 particle_charge_C: float = ELECTRON_CHARGE_C,
                 scale_factor: float = 1.0):
        self.field_fn = field_fn
        self.length_m = length_m
        self.n_slices = n_slices
        self.energy_GeV = energy_GeV
        self.particle_charge_C = particle_charge_C
        self.scale_factor = scale_factor

        self.energy_eV = energy_GeV * 1e9
        self.brho = compute_rigidity(self.energy_eV, particle_charge_C)
        self.charge_sign = float(np.sign(particle_charge_C))
        self.dz = length_m / n_slices

    def _derivatives(self, state: np.ndarray, z: float) -> np.ndarray:
        """
        Compute dx/dz, dx'/dz, dy/dz, dy'/dz for 4D state [x, xp, y, yp].
        """
        x, xp, y, yp = state[0], state[1], state[2], state[3]
        by_val, bx_val = self.field_fn(x, y, z)
        by_val = by_val * self.scale_factor
        bx_val = bx_val * self.scale_factor

        dx_dz = xp
        dxp_dz = self.charge_sign * by_val / self.brho
        dy_dz = yp
        dyp_dz = - self.charge_sign * bx_val / self.brho

        return np.array([dx_dz, dxp_dz, dy_dz, dyp_dz])

    def track(self, beam: np.ndarray) -> np.ndarray:
        """
        Track 6D particle array of shape (6, n_particles) using 4th-order RK4.
        """
        out_beam = beam.copy()
        valid_mask = ~np.isnan(out_beam[0, :])
        if not np.any(valid_mask):
            return out_beam

        dz = self.dz

        for i in range(self.n_slices):
            z0 = i * dz
            z_mid = z0 + 0.5 * dz
            z1 = z0 + dz

            state = out_beam[:4, valid_mask]

            k1 = self._derivatives(state, z0)
            k2 = self._derivatives(state + 0.5 * dz * k1, z_mid)
            k3 = self._derivatives(state + 0.5 * dz * k2, z_mid)
            k4 = self._derivatives(state + dz * k3, z1)

            out_beam[:4, valid_mask] += (dz / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)

        return out_beam
