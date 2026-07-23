"""
BTS Quadrupole Optimization & Sensitivity Analysis Module

Provides physics evaluation, multi-algorithm optimization (SLSQP, trust-constr, Nelder-Mead,
differential evolution), multi-start global search, and Jacobian sensitivity matrix calculations
for matching BTS line optics to storage ring target parameters.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable
import time
import numpy as np
from scipy.optimize import minimize, least_squares, differential_evolution
import at

from .bts_lattice import BTSConfig, create_bts_lattice, validate_bts_lattice
from .optics import compute_twiss_propagation, compute_mismatch_metric


@dataclass
class BTSOptimizationConfig:
    """Configuration for BTS quadrupole optics optimization."""
    # Target Twiss parameters at BTS exit
    target_beta_x: float = 2.336495
    target_beta_y: float = 4.256241
    target_alpha_x: float = -0.016335
    target_alpha_y: float = 0.017772
    target_disp_x: float = 0.080868
    target_disp_px: float = 0.047472
    
    # Initial Twiss parameters at BTS entrance
    init_beta_x: float = 7.560000
    init_beta_y: float = 12.269000
    init_alpha_x: float = 1.523100
    init_alpha_y: float = -1.654700
    init_disp_x: float = 0.276200
    init_disp_px: float = -0.065700
    
    # Merit function weights
    weight_mismatch_x: float = 1.0
    weight_mismatch_y: float = 1.0
    weight_disp_x: float = 10.0
    weight_disp_px: float = 10.0
    weight_reg_k: float = 1e-4  # Quad strength regularization weight
    
    # Limits and bounds
    quad_bounds: Tuple[float, float] = (-5.0, 5.0)
    beta_max_limit: float = 60.0
    
    # Optimizer settings
    random_seed: int = 42


@dataclass
class BTSOptimizationResult:
    """Data container for BTS optimization results."""
    success: bool
    method: str
    optimized_strengths: np.ndarray
    initial_merit: float
    final_merit: float
    initial_mismatch_x: float
    initial_mismatch_y: float
    final_mismatch_x: float
    final_mismatch_y: float
    final_max_beta_x: float
    final_max_beta_y: float
    final_disp_x_residual: float
    constraints_satisfied: bool
    iterations: int
    runtime_seconds: float
    message: str


class BTSOptimizationEvaluator:
    """Evaluates physics merit function and constraints for a given set of quad strengths."""
    
    def __init__(self, config: Optional[BTSOptimizationConfig] = None):
        self.config = config or BTSOptimizationConfig()
        
        self.initial_twiss = {
            'beta': [self.config.init_beta_x, self.config.init_beta_y],
            'alpha': [self.config.init_alpha_x, self.config.init_alpha_y],
            'dispersion': [self.config.init_disp_x, self.config.init_disp_px, 0.0, 0.0]
        }
        
        self.nominal_config = BTSConfig()
        self.nominal_strengths = np.array(self.nominal_config.quad_strengths_list)
        self.lattice = create_bts_lattice(self.nominal_config)
        self.quad_names = ['q11', 'q12', 'q13', 'q21', 'q22', 'q23', 'q31', 'q32', 'q33']
        self._quad_elems = [elem for elem in self.lattice if elem.FamName in self.quad_names]

    def set_quads(self, strengths: np.ndarray):
        """Update quadrupole strengths K in the lattice in-place."""
        k_map = dict(zip(self.quad_names, strengths))
        for elem in self._quad_elems:
            elem.K = k_map[elem.FamName]

    def evaluate(self, strengths: np.ndarray) -> Dict[str, Any]:
        """
        Evaluate optics propagation and return dictionary of metrics and merit components.
        """
        self.set_quads(strengths)
        
        try:
            prop = compute_twiss_propagation(self.lattice, self.initial_twiss)
        except Exception:
            return {
                "feasible": False,
                "merit": 1e9,
                "mismatch_x": 1e6,
                "mismatch_y": 1e6,
                "max_beta_x": 1e6,
                "max_beta_y": 1e6,
            }
            
        beta_end = prop["final_beta"]
        alpha_end = prop["final_alpha"]
        disp_end = prop["final_dispersion"]
        
        mx = compute_mismatch_metric(beta_end[0], alpha_end[0],
                                     self.config.target_beta_x, self.config.target_alpha_x)
        my = compute_mismatch_metric(beta_end[1], alpha_end[1],
                                     self.config.target_beta_y, self.config.target_alpha_y)
        
        dx_diff = disp_end[0] - self.config.target_disp_x
        dpx_diff = disp_end[1] - self.config.target_disp_px
        
        max_beta_x = prop["max_beta_x"]
        max_beta_y = prop["max_beta_y"]
        
        # Penalties for exceeding beta limit (60 m)
        beta_penalty = 0.0
        if max_beta_x > self.config.beta_max_limit:
            beta_penalty += (max_beta_x - self.config.beta_max_limit)**2
        if max_beta_y > self.config.beta_max_limit:
            beta_penalty += (max_beta_y - self.config.beta_max_limit)**2
            
        # Strength regularization penalty
        k_reg = float(np.sum((strengths - self.nominal_strengths)**2))
        
        merit = (
            self.config.weight_mismatch_x * mx +
            self.config.weight_mismatch_y * my +
            self.config.weight_disp_x * (dx_diff**2) +
            self.config.weight_disp_px * (dpx_diff**2) +
            100.0 * beta_penalty +
            self.config.weight_reg_k * k_reg
        )
        
        constraints_ok = (max_beta_x <= self.config.beta_max_limit) and (max_beta_y <= self.config.beta_max_limit)
        
        return {
            "feasible": constraints_ok,
            "merit": float(merit),
            "mismatch_x": float(mx),
            "mismatch_y": float(my),
            "disp_x_residual": float(dx_diff),
            "disp_px_residual": float(dpx_diff),
            "max_beta_x": float(max_beta_x),
            "max_beta_y": float(max_beta_y),
            "beta_end": beta_end,
            "alpha_end": alpha_end,
            "disp_end": disp_end,
        }

    def objective_fn(self, strengths: np.ndarray) -> float:
        """Scalar objective function for scipy minimize."""
        res = self.evaluate(strengths)
        return res["merit"]


def optimize_bts_quadrupoles(method: str = "SLSQP",
                             config: Optional[BTSOptimizationConfig] = None,
                             n_starts: int = 1) -> BTSOptimizationResult:
    """
    Run constrained optimization to optimize 9 BTS quadrupole strengths.
    
    Args:
        method: Optimization algorithm ('SLSQP', 'trust-constr', 'Nelder-Mead', 'differential_evolution').
        config: BTSOptimizationConfig instance.
        n_starts: Number of seeded random restarts for global multi-start search.
        
    Returns:
        BTSOptimizationResult instance.
    """
    if config is None:
        config = BTSOptimizationConfig()
        
    evaluator = BTSOptimizationEvaluator(config)
    initial_k = evaluator.nominal_strengths
    
    init_res = evaluator.evaluate(initial_k)
    
    start_time = time.time()

    # Define quad bounds
    bounds = [config.quad_bounds] * 9

    best_result = None
    best_merit = float('inf')

    # Multi-start loop
    np.random.seed(config.random_seed)

    for start_idx in range(n_starts):
        if start_idx == 0:
            x0 = initial_k.copy()
        else:
            x0 = np.random.uniform(bounds[0][0], bounds[0][1], size=9)
            
        if method == "differential_evolution":
            opt_res = differential_evolution(
                evaluator.objective_fn,
                bounds=bounds,
                seed=config.random_seed,
                maxiter=100
            )
        elif method == "L-BFGS-B":
            opt_res = minimize(
                evaluator.objective_fn,
                x0,
                method="L-BFGS-B",
                bounds=bounds,
                options={'maxiter': 40, 'ftol': 1e-4}
            )
        elif method == "SLSQP":
            opt_res = minimize(
                evaluator.objective_fn,
                x0,
                method="SLSQP",
                bounds=bounds,
                options={'maxiter': 40, 'ftol': 1e-4}
            )
        else:  # Nelder-Mead or other methods
            opt_res = minimize(
                evaluator.objective_fn,
                x0,
                method=method,
                bounds=bounds,
                options={'maxiter': 30}
            )

        final_eval = evaluator.evaluate(opt_res.x)
        if final_eval["merit"] < best_merit:
            best_merit = final_eval["merit"]
            best_result = (opt_res, final_eval)

    opt_res, final_eval = best_result
    runtime = time.time() - start_time

    return BTSOptimizationResult(
        success=bool(opt_res.success or final_eval["feasible"]),
        method=method,
        optimized_strengths=np.array(opt_res.x),
        initial_merit=init_res["merit"],
        final_merit=final_eval["merit"],
        initial_mismatch_x=init_res["mismatch_x"],
        initial_mismatch_y=init_res["mismatch_y"],
        final_mismatch_x=final_eval["mismatch_x"],
        final_mismatch_y=final_eval["mismatch_y"],
        final_max_beta_x=final_eval["max_beta_x"],
        final_max_beta_y=final_eval["max_beta_y"],
        final_disp_x_residual=final_eval["disp_x_residual"],
        constraints_satisfied=final_eval["feasible"],
        iterations=getattr(opt_res, "nit", getattr(opt_res, "nfev", 0)),
        runtime_seconds=round(runtime, 4),
        message=str(getattr(opt_res, "message", "Completed"))
    )


def compute_sensitivity_matrix(strengths: np.ndarray,
                               step_size: float = 1e-4,
                               config: Optional[BTSOptimizationConfig] = None) -> Dict[str, Any]:
    """
    Compute finite-difference Jacobian sensitivity matrix J_ij = dO_i / dK_j
    of exit optics observables (beta_x, beta_y, alpha_x, alpha_y, Dx, Dpx)
    with respect to the 9 quadrupole strengths K.
    
    Returns:
        Dictionary containing Jacobian matrix (6x9) and parameter labels.
    """
    evaluator = BTSOptimizationEvaluator(config)
    
    base_res = evaluator.evaluate(strengths)
    obs_names = ['beta_x', 'beta_y', 'alpha_x', 'alpha_y', 'disp_x', 'disp_px']
    quad_names = ['q11', 'q12', 'q13', 'q21', 'q22', 'q23', 'q31', 'q32', 'q33']
    
    jacobian = np.zeros((6, 9))
    
    for j in range(9):
        k_plus = strengths.copy()
        k_minus = strengths.copy()
        
        k_plus[j] += step_size
        k_minus[j] -= step_size
        
        eval_plus = evaluator.evaluate(k_plus)
        eval_minus = evaluator.evaluate(k_minus)
        
        vec_plus = np.array([
            eval_plus["beta_end"][0], eval_plus["beta_end"][1],
            eval_plus["alpha_end"][0], eval_plus["alpha_end"][1],
            eval_plus["disp_end"][0], eval_plus["disp_end"][1]
        ])
        vec_minus = np.array([
            eval_minus["beta_end"][0], eval_minus["beta_end"][1],
            eval_minus["alpha_end"][0], eval_minus["alpha_end"][1],
            eval_minus["disp_end"][0], eval_minus["disp_end"][1]
        ])
        
        jacobian[:, j] = (vec_plus - vec_minus) / (2.0 * step_size)
        
    return {
        "observable_names": obs_names,
        "quad_names": quad_names,
        "jacobian_matrix": jacobian,
        "step_size": step_size,
    }
