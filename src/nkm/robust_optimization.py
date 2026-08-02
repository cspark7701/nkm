"""
NKM Robust Optimization and Statistical Robustness Evaluation Module

Provides Monte Carlo statistical evaluations (p50, p68, p95, p99 percentiles, failure probability,
bootstrap confidence intervals), one-at-a-time tolerance sensitivity rankings, and robust
design optimization algorithms.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
from scipy.optimize import minimize

from .bts_lattice import BTSConfig, create_bts_lattice
from .optics import compute_twiss_propagation, compute_mismatch_metric
from .errors import ErrorBudgetConfig, sample_error_ensemble, apply_sample_errors
from .optimization import BaseOpticsObjective, BTSOptimizationConfig, BTSNormalizedObjectives, BTSHardwareConstraints


class RobustMonteCarloObjective(BaseOpticsObjective):
    """
    Robust Monte Carlo Objective Strategy for Optics Optimization.
    
    Evaluates optics mismatch across an error ensemble sample, returning mean / median
    mismatch residuals for robust optics design.
    """
    def __init__(self,
                 config: Optional[BTSOptimizationConfig] = None,
                 n_samples: int = 20,
                 seed: int = 42):
        self.config = config or BTSOptimizationConfig()
        self.objectives = BTSNormalizedObjectives(self.config.target_config)
        self.constraints = BTSHardwareConstraints(self.config.constraint_config)
        self.nominal_strengths = self.objectives.nominal_strengths
        self.quad_names = self.objectives.quad_names
        self.n_samples = n_samples
        self.seed = seed
        self.samples = sample_error_ensemble(n_samples=n_samples, seed=seed)

    def compute_residual_vector(self, strengths: np.ndarray) -> np.ndarray:
        eval_dict = self.evaluate(strengths)
        return np.array([
            eval_dict["mismatch_x"],
            eval_dict["mismatch_y"],
            eval_dict["disp_x_residual"],
            eval_dict["disp_px_residual"]
        ])

    def evaluate(self, strengths: np.ndarray) -> Dict[str, Any]:
        target_twiss = {
            "beta": [self.config.target_config.target_beta_x, self.config.target_config.target_beta_y],
            "alpha": [self.config.target_config.target_alpha_x, self.config.target_config.target_alpha_y]
        }
        bts_config = BTSConfig(
            k_q11=float(strengths[0]), k_q12=float(strengths[1]), k_q13=float(strengths[2]),
            k_q21=float(strengths[3]), k_q22=float(strengths[4]), k_q23=float(strengths[5]),
            k_q31=float(strengths[6]), k_q32=float(strengths[7]), k_q33=float(strengths[8])
        )
        stats = evaluate_robustness_statistics(bts_config, target_twiss, self.samples)
        
        mx_p50 = stats["mismatch_x"]["p50"]
        my_p50 = stats["mismatch_y"]["p50"]
        merit = float(mx_p50 + my_p50)
        
        return {
            "feasible": bool(stats["feasible_fraction"] > 0.8),
            "violations": [] if stats["feasible_fraction"] > 0.8 else ["High failure rate in Monte Carlo ensemble"],
            "merit": merit,
            "mismatch_x": mx_p50,
            "mismatch_y": my_p50,
            "disp_x_residual": 0.0,
            "disp_px_residual": 0.0,
            "max_beta_x": stats["max_beta_x_m"]["p50"],
            "max_beta_y": stats["max_beta_y_m"]["p50"],
            "robust_stats": stats
        }


def evaluate_robustness_statistics(nominal_config: BTSConfig,
                                     target_twiss: Dict[str, Any],
                                     samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluate Monte Carlo statistics (p50, p68, p95, p99, failure probability, bootstrap CI)
    across a set of error realization samples.
    """
    n_samples = len(samples)
    mx_list = []
    my_list = []
    bx_max_list = []
    by_max_list = []
    failures = 0

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
            bx_max_list.append(prop["max_beta_x"])
            by_max_list.append(prop["max_beta_y"])

            if prop["max_beta_x"] > 60.0 or prop["max_beta_y"] > 60.0 or mx > 0.5 or my > 0.5:
                failures += 1
        except Exception:
            mx_list.append(1e3)
            my_list.append(1e3)
            bx_max_list.append(1e3)
            by_max_list.append(1e3)
            failures += 1

    mx_arr = np.array(mx_list)
    my_arr = np.array(my_list)
    bx_arr = np.array(bx_max_list)
    by_arr = np.array(by_max_list)

    # Bootstrap 95% confidence interval for median mismatch Mx
    rng = np.random.default_rng(42)
    boot_medians = []
    for _ in range(1000):
        boot_sample = rng.choice(mx_arr, size=n_samples, replace=True)
        boot_medians.append(np.median(boot_sample))
    ci_lower = float(np.percentile(boot_medians, 2.5))
    ci_upper = float(np.percentile(boot_medians, 97.5))

    return {
        "n_samples": n_samples,
        "feasible_fraction": float(1.0 - (failures / n_samples)),
        "failure_probability": float(failures / n_samples),
        "mismatch_x": {
            "p50": float(np.median(mx_arr)),
            "p50_median": float(np.median(mx_arr)),
            "p68": float(np.percentile(mx_arr, 68)),
            "p95": float(np.percentile(mx_arr, 95)),
            "p99": float(np.percentile(mx_arr, 99)),
            "mean": float(np.mean(mx_arr)),
            "std": float(np.std(mx_arr)),
            "bootstrap_95ci_median": [ci_lower, ci_upper]
        },
        "mismatch_y": {
            "p50": float(np.median(my_arr)),
            "p50_median": float(np.median(my_arr)),
            "p68": float(np.percentile(my_arr, 68)),
            "p95": float(np.percentile(my_arr, 95)),
            "p99": float(np.percentile(my_arr, 99)),
            "mean": float(np.mean(my_arr)),
            "std": float(np.std(my_arr)),
        },
        "max_beta_x_m": {
            "p50": float(np.median(bx_arr)),
            "p50_median": float(np.median(bx_arr)),
            "p95": float(np.percentile(bx_arr, 95)),
            "p99": float(np.percentile(bx_arr, 99)),
        },
        "max_beta_y_m": {
            "p50": float(np.median(by_arr)),
            "p50_median": float(np.median(by_arr)),
            "p95": float(np.percentile(by_arr, 95)),
            "p99": float(np.percentile(by_arr, 99)),
        }
    }


def compute_one_at_a_time_sensitivity(nominal_config: BTSConfig,
                                       target_twiss: Dict[str, Any],
                                       n_samples: int = 50,
                                       seed: int = 42) -> Dict[str, float]:
    """
    Perform One-At-A-Time (OAT) sensitivity scans across individual error categories
    to rank dominant error contributors.
    """
    base_samples = sample_error_ensemble(n_samples=n_samples, seed=seed)

    ref_lattice = create_bts_lattice(nominal_config)
    ref_twiss = {'beta': [7.56, 12.27], 'alpha': [1.52, -1.65], 'dispersion': [0.276, -0.065, 0, 0]}
    ref_prop = compute_twiss_propagation(ref_lattice, ref_twiss)
    ref_mx = compute_mismatch_metric(ref_prop["final_beta"][0], ref_prop["final_alpha"][0], target_twiss["beta"][0], target_twiss["alpha"][0])
    ref_my = compute_mismatch_metric(ref_prop["final_beta"][1], ref_prop["final_alpha"][1], target_twiss["beta"][1], target_twiss["alpha"][1])
    ref_merit = ref_mx + ref_my

    error_types = [
        ("quad_k_err", "Quad Gradient Error (0.1%)"),
        ("quad_dx_m", "Quad Alignment Offset (100 um)"),
        ("quad_roll_rad", "Quad Roll Error (0.5 mrad)"),
        ("booster_x_m", "Booster Centroid Jitter (0.5 mm)"),
        ("energy_dp_p", "Energy Error (0.1%)"),
        ("nkm_scale_err", "NKM Field Scale Jitter (0.5%)"),
    ]

    rankings = {}
    for err_key, label in error_types:
        delta_merits = []
        for s in base_samples:
            iso_sample = {
                "sample_id": s["sample_id"],
                "quad_k_err": s["quad_k_err"] if err_key == "quad_k_err" else [0.0]*9,
                "quad_dx_m": s["quad_dx_m"] if err_key == "quad_dx_m" else [0.0]*9,
                "quad_dy_m": [0.0]*9,
                "quad_roll_rad": s["quad_roll_rad"] if err_key == "quad_roll_rad" else [0.0]*9,
                "quad_ds_m": [0.0]*9,
                "booster_x_m": s["booster_x_m"] if err_key == "booster_x_m" else 0.0,
                "booster_xp_rad": 0.0,
                "energy_dp_p": s["energy_dp_p"] if err_key == "energy_dp_p" else 0.0,
                "beta_mismatch_x": 0.0,
                "beta_mismatch_y": 0.0,
                "nkm_scale_err": s["nkm_scale_err"] if err_key == "nkm_scale_err" else 0.0,
                "nkm_dx_m": 0.0,
                "ring_co_x_m": 0.0,
                "septum_x_m": 0.0,
            }
            lattice, init_twiss = apply_sample_errors(nominal_config, iso_sample)
            prop = compute_twiss_propagation(lattice, init_twiss)
            mx = compute_mismatch_metric(prop["final_beta"][0], prop["final_alpha"][0], target_twiss["beta"][0], target_twiss["alpha"][0])
            my = compute_mismatch_metric(prop["final_beta"][1], prop["final_alpha"][1], target_twiss["beta"][1], target_twiss["alpha"][1])
            delta_merits.append(abs((mx + my) - ref_merit))

        rankings[label] = float(np.mean(delta_merits))

    return dict(sorted(rankings.items(), key=lambda item: item[1], reverse=True))
