#!/usr/bin/env python3
"""
Task 01 Validation Script — Component-Aware NKM Kick & Sign Conventions

Validates 2-plane transverse field-to-kick conversions, charge sign flipping,
and thin vs. thick integration agreement under Lorentz force physics.
Outputs machine-readable metrics to results/kick_conventions/task01_metrics.json.
"""

import sys
import json
import datetime
from pathlib import Path
import numpy as np

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.nkm.units import (
    compute_rigidity,
    integrated_field_to_transverse_kicks,
    transverse_kicks_to_integrated_field,
    ELECTRON_CHARGE_C,
    ELEMENTARY_CHARGE_C
)
from src.nkm.integrators import SymplecticSplitIntegrator, LorentzRK4Integrator


def run_validation() -> dict:
    output_dir = repo_root / "results" / "kick_conventions"
    output_dir.mkdir(parents=True, exist_ok=True)

    energy_eV = 4.0e9
    brho = compute_rigidity(energy_eV, ELECTRON_CHARGE_C)

    # Test case 1: Pure B_y (horizontal kick only)
    dx_by, dy_by = integrated_field_to_transverse_kicks(0.0, 0.0767, beam_energy_eV=energy_eV, particle_charge_C=ELECTRON_CHARGE_C)
    
    # Test case 2: Pure B_x (vertical kick only)
    dx_bx, dy_bx = integrated_field_to_transverse_kicks(0.0500, 0.0, beam_energy_eV=energy_eV, particle_charge_C=ELECTRON_CHARGE_C)

    # Test case 3: Combined 2-plane (Bx, By)
    dx_2p, dy_2p = integrated_field_to_transverse_kicks(0.0500, 0.0767, beam_energy_eV=energy_eV, particle_charge_C=ELECTRON_CHARGE_C)

    # Test case 4: Positive charge sign reversal
    dx_pos, dy_pos = integrated_field_to_transverse_kicks(0.0500, 0.0767, beam_energy_eV=energy_eV, particle_charge_C=ELEMENTARY_CHARGE_C)

    # Test case 5: Thick vs thin agreement
    def uniform_field(x, y, z):
        return np.full_like(x, 0.0767 / 0.525), np.full_like(x, 0.0500 / 0.525)

    beam_in = np.zeros((6, 1))
    sym_integrator = SymplecticSplitIntegrator(uniform_field, length_m=0.525, n_slices=100, energy_GeV=4.0)
    rk4_integrator = LorentzRK4Integrator(uniform_field, length_m=0.525, n_slices=100, energy_GeV=4.0)

    beam_sym = sym_integrator.track(beam_in)
    beam_rk4 = rk4_integrator.track(beam_in)

    thin_dx_err = float(abs(beam_sym[1, 0] - dx_2p))
    thin_dy_err = float(abs(beam_sym[3, 0] - dy_2p))
    rk4_dx_err = float(abs(beam_rk4[1, 0] - dx_2p))
    rk4_dy_err = float(abs(beam_rk4[3, 0] - dy_2p))

    metrics = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "beam_energy_GeV": energy_eV * 1e-9,
        "brho_T_m": float(brho),
        "electron_dx_mrad_from_By": float(dx_by * 1e3),
        "electron_dy_mrad_from_Bx": float(dy_bx * 1e3),
        "electron_dx_mrad_2plane": float(dx_2p * 1e3),
        "electron_dy_mrad_2plane": float(dy_2p * 1e3),
        "positive_charge_dx_mrad_2plane": float(dx_pos * 1e3),
        "positive_charge_dy_mrad_2plane": float(dy_pos * 1e3),
        "charge_sign_reversal_verified": bool(dx_2p == -dx_pos and dy_2p == -dy_pos),
        "symplectic_vs_analytic_kick_err": max(thin_dx_err, thin_dy_err),
        "rk4_vs_analytic_kick_err": max(rk4_dx_err, rk4_dy_err),
        "all_checks_passed": bool(
            dx_2p < 0 and dy_2p > 0 and
            dx_pos > 0 and dy_pos < 0 and
            max(thin_dx_err, thin_dy_err) < 1e-5
        )
    }

    metrics_file = output_dir / "task01_metrics.json"
    with open(metrics_file, "w") as f:
        json.dump(metrics, f, indent=2)

    return metrics


if __name__ == "__main__":
    m = run_validation()
    print("=== Task 01 Kick Convention Validation Summary ===")
    print(f"B*rho                       : {m['brho_T_m']:.6f} T*m")
    print(f"Electron 2-plane Kick (dx,dy): ({m['electron_dx_mrad_2plane']:.4f}, {m['electron_dy_mrad_2plane']:.4f}) mrad")
    print(f"Positron 2-plane Kick (dx,dy): ({m['positive_charge_dx_mrad_2plane']:.4f}, {m['positive_charge_dy_mrad_2plane']:.4f}) mrad")
    print(f"Charge Sign Reversal Check  : {m['charge_sign_reversal_verified']}")
    print(f"Symplectic Integrator Error : {m['symplectic_vs_analytic_kick_err']:.3e} rad")
    print(f"RK4 Integrator Error        : {m['rk4_vs_analytic_kick_err']:.3e} rad")
    print(f"All Checks Passed           : {m['all_checks_passed']}")
