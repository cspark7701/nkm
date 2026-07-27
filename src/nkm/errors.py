"""
BTS & NKM Error Modeling, Monte Carlo Sampling, and Robustness Analysis Module

Provides structured error specifications across 5 error categories (Optics, Orbit/Alignment,
Beam, NKM, and Storage Ring errors), Monte Carlo sampling with common random numbers,
rigidity-consistent energy error scaling, and one-at-a-time tolerance sensitivity scans.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import at

from .units import compute_rigidity, ELECTRON_CHARGE_C
from .bts_lattice import BTSConfig, create_bts_lattice
from .optics import compute_twiss_propagation, compute_mismatch_metric


@dataclass
class ErrorBudgetConfig:
    """Standard deviation tolerances for 5 physical uncertainty categories."""
    # 1. Optics errors
    quad_k_rel_std: float = 1.0e-3       # Quad gradient relative error (0.1%)
    dipole_b_rel_std: float = 5.0e-4     # Dipole field relative error (0.05%)
    ps_quantization_std: float = 1.0e-4  # Power supply quantization / noise

    # 2. Orbit & Alignment errors
    booster_x_jitter_std_m: float = 5.0e-4    # Booster extraction position jitter (0.5 mm)
    booster_xp_jitter_std_rad: float = 2.0e-4 # Booster extraction angle jitter (0.2 mrad)
    quad_dx_std_m: float = 1.0e-4             # Quad horizontal offset (100 um)
    quad_dy_std_m: float = 1.0e-4             # Quad vertical offset (100 um)
    quad_roll_std_rad: float = 5.0e-4         # Quad roll tilt error (0.5 mrad)
    quad_ds_std_m: float = 5.0e-4             # Longitudinal placement error (0.5 mm)

    # 3. Beam errors
    beta_mismatch_rel_std: float = 0.05       # Twiss beta mismatch (5%)
    emittance_rel_std: float = 0.10           # Emittance variation (10%)
    energy_dp_p_std: float = 1.0e-3           # Mean energy error (0.1%)
    espread_std: float = 1.0e-4               # Energy spread variation

    # 4. NKM errors
    nkm_scale_std: float = 5.0e-3             # NKM field scale jitter (0.5%)
    nkm_timing_std_mrad: float = 1.0e-4       # NKM timing phase jitter
    nkm_dx_std_m: float = 2.0e-4              # NKM horizontal alignment (200 um)

    # 5. Storage Ring errors
    ring_co_x_std_m: float = 2.0e-4           # Closed-orbit error (200 um)
    ring_beta_rel_std: float = 0.03           # Injection point optics error (3%)
    septum_x_std_m: float = 1.0e-4            # Septum position uncertainty (100 um)


def sample_error_ensemble(config: Optional[ErrorBudgetConfig] = None,
                          n_samples: int = 100,
                          seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generate n_samples of reproducible error realization dictionaries using fixed seed.
    """
    if config is None:
        config = ErrorBudgetConfig()

    rng = np.random.default_rng(seed)

    samples = []
    for i in range(n_samples):
        sample = {
            "sample_id": i,
            # Optics errors
            "quad_k_err": rng.normal(0.0, config.quad_k_rel_std, size=9).tolist(),
            "dipole_b_err": float(rng.normal(0.0, config.dipole_b_rel_std)),
            # Orbit/Alignment errors
            "booster_x_m": float(rng.normal(0.0, config.booster_x_jitter_std_m)),
            "booster_x_jitter_m": float(rng.normal(0.0, config.booster_x_jitter_std_m)),
            "booster_dx_m": float(rng.normal(0.0, config.booster_x_jitter_std_m)),
            "booster_xp_rad": float(rng.normal(0.0, config.booster_xp_jitter_std_rad)),
            "quad_dx_m": rng.normal(0.0, config.quad_dx_std_m, size=9).tolist(),
            "quad_dy_m": rng.normal(0.0, config.quad_dy_std_m, size=9).tolist(),
            "quad_roll_rad": rng.normal(0.0, config.quad_roll_std_rad, size=9).tolist(),
            "quad_ds_m": rng.normal(0.0, config.quad_ds_std_m, size=9).tolist(),
            # Beam errors
            "energy_dp_p": float(rng.normal(0.0, config.energy_dp_p_std)),
            "beta_mismatch_x": float(rng.normal(0.0, config.beta_mismatch_rel_std)),
            "beta_mismatch_y": float(rng.normal(0.0, config.beta_mismatch_rel_std)),
            # NKM errors
            "nkm_scale_err": float(rng.normal(0.0, config.nkm_scale_std)),
            "nkm_dx_m": float(rng.normal(0.0, config.nkm_dx_std_m)),
            # Storage Ring errors
            "ring_co_x_m": float(rng.normal(0.0, config.ring_co_x_std_m)),
            "septum_x_m": float(rng.normal(0.0, config.septum_x_std_m)),
        }
        samples.append(sample)

    return samples


def apply_sample_errors(nominal_config: BTSConfig, sample: Dict[str, Any]) -> Tuple[at.Lattice, Dict[str, Any]]:
    """
    Apply an error realization sample to construct a perturbed AT lattice and initial Twiss.
    Energy errors scale beam rigidity B_rho consistently without changing physical fields.
    Centroid jitter is treated strictly as phase-space offset, independent of dispersion.
    """
    k_list = nominal_config.quad_strengths_list
    perturbed_k = [k * (1.0 + err) for k, err in zip(k_list, sample["quad_k_err"])]

    # Energy error alters beam rigidity B_rho = E / c
    energy_perturbed_eV = nominal_config.energy_eV * (1.0 + sample["energy_dp_p"])

    pert_config = BTSConfig(
        k_q11=perturbed_k[0], k_q12=perturbed_k[1], k_q13=perturbed_k[2],
        k_q21=perturbed_k[3], k_q22=perturbed_k[4], k_q23=perturbed_k[5],
        k_q31=perturbed_k[6], k_q32=perturbed_k[7], k_q33=perturbed_k[8],
        energy_eV=energy_perturbed_eV
    )

    lattice = create_bts_lattice(pert_config)
    quad_names = ['q11', 'q12', 'q13', 'q21', 'q22', 'q23', 'q31', 'q32', 'q33']

    dx_list = sample["quad_dx_m"]
    dy_list = sample["quad_dy_m"]
    roll_list = sample["quad_roll_rad"]

    for elem in lattice:
        if elem.FamName in quad_names:
            idx = quad_names.index(elem.FamName)
            dx = dx_list[idx]
            dy = dy_list[idx]
            roll = roll_list[idx]

            elem.T1 = np.array([-dx, 0.0, -dy, 0.0, 0.0, 0.0])
            elem.T2 = np.array([dx, 0.0, dy, 0.0, 0.0, 0.0])

            cos_r, sin_r = np.cos(roll), np.sin(roll)
            r_mat = np.eye(6)
            r_mat[0, 0] = cos_r
            r_mat[0, 2] = sin_r
            r_mat[2, 0] = -sin_r
            r_mat[2, 2] = cos_r

            elem.R1 = r_mat
            elem.R2 = r_mat.T

    # Initial Twiss with Twiss mismatch errors (dispersion is NOT corrupted by centroid jitter)
    init_twiss = {
        'beta': [7.560000 * (1.0 + sample.get("beta_mismatch_x", 0.0)),
                 12.269000 * (1.0 + sample.get("beta_mismatch_y", 0.0))],
        'alpha': [1.523100, -1.654700],
        'dispersion': [0.276200, -0.065700, 0.0, 0.0]
    }

    return lattice, init_twiss


def evaluate_monte_carlo_robustness(nominal_config: BTSConfig,
                                     target_twiss: Dict[str, Any],
                                     n_samples: int = 100,
                                     seed: int = 42) -> Dict[str, Any]:
    """Legacy alias delegating to robust_optimization module."""
    from .robust_optimization import evaluate_robustness_statistics
    samples = sample_error_ensemble(n_samples=n_samples, seed=seed)
    return evaluate_robustness_statistics(nominal_config, target_twiss, samples)


def compute_error_sensitivity_ranking(nominal_config: BTSConfig,
                                       target_twiss: Dict[str, Any]) -> Dict[str, float]:
    """Legacy alias delegating to robust_optimization module."""
    from .robust_optimization import compute_one_at_a_time_sensitivity
    return compute_one_at_a_time_sensitivity(nominal_config, target_twiss)
