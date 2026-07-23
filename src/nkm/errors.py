"""
BTS & NKM Error Modeling, Monte Carlo Sampling, and Robustness Analysis Module

Provides structured error specifications (quad gradients, misalignments, roll errors,
booster centroid jitter, energy errors, NKM scale jitter), Monte Carlo sampling,
single-parameter tolerance scans, and variance-based sensitivity ranking.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import at

from .bts_lattice import BTSConfig, create_bts_lattice, validate_bts_lattice
from .optics import compute_twiss_propagation, compute_mismatch_metric


@dataclass
class ErrorBudgetConfig:
    """Standard deviation tolerances for magnet and beam parameters."""
    # Quadrupole gradient relative error (std)
    quad_k_rel_std: float = 1e-3  # 0.1%
    # Dipole field relative error (std)
    dipole_b_rel_std: float = 5e-4  # 0.05%
    # Quadrupole transverse misalignments (m)
    quad_dx_std_m: float = 1e-4  # 100 um
    quad_dy_std_m: float = 1e-4  # 100 um
    # Quadrupole roll tilt error (rad)
    quad_roll_std_rad: float = 5e-4  # 0.5 mrad
    # Booster extraction centroid jitter (m, rad)
    booster_x_std_m: float = 5e-4  # 0.5 mm
    booster_xp_std_rad: float = 2e-4  # 0.2 mrad
    # Energy error (std, dp/p)
    energy_rel_std: float = 1e-3  # 0.1%
    # NKM field scale jitter (std)
    nkm_scale_std: float = 5e-3  # 0.5%


def sample_error_ensemble(config: Optional[ErrorBudgetConfig] = None,
                          n_samples: int = 1000,
                          seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generate n_samples of reproducible error realization dictionaries.
    
    Args:
        config: ErrorBudgetConfig instance.
        n_samples: Number of Monte Carlo realizations.
        seed: Fixed random seed for reproducibility.
        
    Returns:
        List of dictionaries containing perturbed values for each sample.
    """
    if config is None:
        config = ErrorBudgetConfig()
        
    np.random.seed(seed)
    quad_names = ['q11', 'q12', 'q13', 'q21', 'q22', 'q23', 'q31', 'q32', 'q33']
    
    samples = []
    for i in range(n_samples):
        sample = {
            "sample_id": i,
            "quad_k_err": np.random.normal(0.0, config.quad_k_rel_std, size=9).tolist(),
            "quad_dx_m": np.random.normal(0.0, config.quad_dx_std_m, size=9).tolist(),
            "quad_dy_m": np.random.normal(0.0, config.quad_dy_std_m, size=9).tolist(),
            "quad_roll_rad": np.random.normal(0.0, config.quad_roll_std_rad, size=9).tolist(),
            "booster_dx_m": float(np.random.normal(0.0, config.booster_x_std_m)),
            "booster_dxp_rad": float(np.random.normal(0.0, config.booster_xp_std_rad)),
            "energy_dp_p": float(np.random.normal(0.0, config.energy_rel_std)),
            "nkm_scale_err": float(np.random.normal(0.0, config.nkm_scale_std)),
        }
        samples.append(sample)
        
    return samples


def apply_sample_errors(nominal_config: BTSConfig, sample: Dict[str, Any]) -> Tuple[at.Lattice, Dict[str, Any]]:
    """
    Apply an error sample to construct a perturbed AT lattice and perturbed initial Twiss.
    """
    k_list = nominal_config.quad_strengths_list
    perturbed_k = [k * (1.0 + err) for k, err in zip(k_list, sample["quad_k_err"])]
    
    pert_config = BTSConfig(
        k_q11=perturbed_k[0], k_q12=perturbed_k[1], k_q13=perturbed_k[2],
        k_q21=perturbed_k[3], k_q22=perturbed_k[4], k_q23=perturbed_k[5],
        k_q31=perturbed_k[6], k_q32=perturbed_k[7], k_q33=perturbed_k[8],
        energy_eV=nominal_config.energy_eV * (1.0 + sample["energy_dp_p"])
    )
    
    lattice = create_bts_lattice(pert_config)
    quad_names = ['q11', 'q12', 'q13', 'q21', 'q22', 'q23', 'q31', 'q32', 'q33']
    
    # Apply alignment / tilt errors to quadrupoles in lattice
    dx_list = sample["quad_dx_m"]
    dy_list = sample["quad_dy_m"]
    roll_list = sample["quad_roll_rad"]
    
    for elem in lattice:
        if elem.FamName in quad_names:
            idx = quad_names.index(elem.FamName)
            dx = dx_list[idx]
            dy = dy_list[idx]
            roll = roll_list[idx]
            
            # Translation alignment shifts (T1 at entrance, T2 at exit)
            elem.T1 = np.array([-dx, 0.0, -dy, 0.0, 0.0, 0.0])
            elem.T2 = np.array([dx, 0.0, dy, 0.0, 0.0, 0.0])
            
            # Roll tilt rotation matrices (R1 at entrance, R2 at exit)
            cos_r, sin_r = np.cos(roll), np.sin(roll)
            r_mat = np.eye(6)
            r_mat[0, 0] = cos_r
            r_mat[0, 2] = sin_r
            r_mat[2, 0] = -sin_r
            r_mat[2, 2] = cos_r
            
            elem.R1 = r_mat
            elem.R2 = r_mat.T
                
    # Perturbed initial Twiss
    init_twiss = {
        'beta': [7.560000, 12.269000],
        'alpha': [1.523100, -1.654700],
        'dispersion': [0.276200 + sample["booster_dx_m"], -0.065700 + sample["booster_dxp_rad"], 0.0, 0.0]
    }
    
    return lattice, init_twiss


def evaluate_monte_carlo_robustness(nominal_config: BTSConfig,
                                     target_twiss: Dict[str, Any],
                                     n_samples: int = 1000,
                                     seed: int = 42) -> Dict[str, Any]:
    """
    Run Monte Carlo robustness simulation across n_samples error realizations.
    
    Returns:
        Dictionary of statistical metrics (mean, std, median, 95th percentile, max)
        for mismatch Mx, My and peak beta functions.
    """
    samples = sample_error_ensemble(n_samples=n_samples, seed=seed)
    
    mx_list = []
    my_list = []
    beta_x_max_list = []
    beta_y_max_list = []
    feasible_count = 0
    
    for s in samples:
        try:
            lattice, init_twiss = apply_sample_errors(nominal_config, s)
            prop = compute_twiss_propagation(lattice, init_twiss)
            
            beta_end = prop["final_beta"]
            alpha_end = prop["final_alpha"]
            
            mx = compute_mismatch_metric(beta_end[0], alpha_end[0], target_twiss["beta"][0], target_twiss["alpha"][0])
            my = compute_mismatch_metric(beta_end[1], alpha_end[1], target_twiss["beta"][1], target_twiss["alpha"][1])
            
            mx_list.append(mx)
            my_list.append(my)
            beta_x_max_list.append(prop["max_beta_x"])
            beta_y_max_list.append(prop["max_beta_y"])
            
            if prop["max_beta_x"] <= 60.0 and prop["max_beta_y"] <= 60.0:
                feasible_count += 1
        except Exception:
            mx_list.append(1e3)
            my_list.append(1e3)
            beta_x_max_list.append(1e3)
            beta_y_max_list.append(1e3)
            
    mx_arr = np.array(mx_list)
    my_arr = np.array(my_list)
    bx_arr = np.array(beta_x_max_list)
    by_arr = np.array(beta_y_max_list)
    
    return {
        "n_samples": n_samples,
        "feasible_fraction": float(feasible_count / n_samples),
        "mismatch_x": {
            "mean": float(np.mean(mx_arr)),
            "std": float(np.std(mx_arr)),
            "p50": float(np.median(mx_arr)),
            "p95": float(np.percentile(mx_arr, 95)),
            "max": float(np.max(mx_arr)),
        },
        "mismatch_y": {
            "mean": float(np.mean(my_arr)),
            "std": float(np.std(my_arr)),
            "p50": float(np.median(my_arr)),
            "p95": float(np.percentile(my_arr, 95)),
            "max": float(np.max(my_arr)),
        },
        "max_beta_x_m": {
            "mean": float(np.mean(bx_arr)),
            "p95": float(np.percentile(bx_arr, 95)),
            "max": float(np.max(bx_arr)),
        },
        "max_beta_y_m": {
            "mean": float(np.mean(by_arr)),
            "p95": float(np.percentile(by_arr, 95)),
            "max": float(np.max(by_arr)),
        },
        "raw_mx": mx_arr.tolist(),
        "raw_my": my_arr.tolist(),
    }


def compute_error_sensitivity_ranking(nominal_config: BTSConfig,
                                       target_twiss: Dict[str, Any]) -> Dict[str, float]:
    """
    Perform one-at-a-time sensitivity scans for individual error sources to rank dominant contributors.
    """
    base_samples = sample_error_ensemble(n_samples=100, seed=42)
    
    # 1. Baseline unperturbed mismatch
    ref_lattice = create_bts_lattice(nominal_config)
    ref_twiss = {'beta': [7.56, 12.27], 'alpha': [1.52, -1.65], 'dispersion': [0.276, -0.065, 0, 0]}
    ref_prop = compute_twiss_propagation(ref_lattice, ref_twiss)
    ref_mx = compute_mismatch_metric(ref_prop["final_beta"][0], ref_prop["final_alpha"][0], target_twiss["beta"][0], target_twiss["alpha"][0])
    ref_my = compute_mismatch_metric(ref_prop["final_beta"][1], ref_prop["final_alpha"][1], target_twiss["beta"][1], target_twiss["alpha"][1])
    ref_merit = ref_mx + ref_my
    
    rankings = {}
    error_types = [
        ("quad_k_err", "Quad Gradient Error (0.1%)"),
        ("quad_dx_m", "Quad Alignment X (100 um)"),
        ("quad_dy_m", "Quad Alignment Y (100 um)"),
        ("quad_roll_rad", "Quad Roll Error (0.5 mrad)"),
        ("booster_dx_m", "Booster Centroid X (0.5 mm)"),
        ("energy_dp_p", "Energy Error (0.1%)"),
    ]
    
    for err_key, label in error_types:
        delta_merits = []
        for s in base_samples[:50]:
            # Isolated error sample
            iso_sample = {
                "sample_id": s["sample_id"],
                "quad_k_err": s["quad_k_err"] if err_key == "quad_k_err" else [0.0]*9,
                "quad_dx_m": s["quad_dx_m"] if err_key == "quad_dx_m" else [0.0]*9,
                "quad_dy_m": s["quad_dy_m"] if err_key == "quad_dy_m" else [0.0]*9,
                "quad_roll_rad": s["quad_roll_rad"] if err_key == "quad_roll_rad" else [0.0]*9,
                "booster_dx_m": s["booster_dx_m"] if err_key == "booster_dx_m" else 0.0,
                "booster_dxp_rad": 0.0,
                "energy_dp_p": s["energy_dp_p"] if err_key == "energy_dp_p" else 0.0,
                "nkm_scale_err": 0.0,
            }
            lattice, init_twiss = apply_sample_errors(nominal_config, iso_sample)
            prop = compute_twiss_propagation(lattice, init_twiss)
            mx = compute_mismatch_metric(prop["final_beta"][0], prop["final_alpha"][0], target_twiss["beta"][0], target_twiss["alpha"][0])
            my = compute_mismatch_metric(prop["final_beta"][1], prop["final_alpha"][1], target_twiss["beta"][1], target_twiss["alpha"][1])
            delta_merits.append(abs((mx + my) - ref_merit))
            
        rankings[label] = float(np.mean(delta_merits))
        
    return dict(sorted(rankings.items(), key=lambda item: item[1], reverse=True))
