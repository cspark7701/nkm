"""
BTS Quadrupole Optimization & Sensitivity Analysis Module

Provides physics evaluation, multi-algorithm optimization (Least-Squares, SLSQP, trust-constr, Nelder-Mead),
hardware-constrained multi-start global search, Jacobian sensitivity matrix calculations, and significant-digit
stability analysis for matching BTS line optics.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable
import time
import numpy as np
from scipy.optimize import minimize, least_squares

from .bts_lattice import BTSConfig, create_bts_lattice
from .optics import compute_twiss_propagation, compute_mismatch_metric
from .constraints import BTSHardwareConstraints, BTSConstraintConfig
from .objectives import BTSNormalizedObjectives, OpticsTargetConfig


@dataclass
class BTSOptimizationConfig:
    """Configuration for BTS quadrupole optics optimization."""
    target_config: OpticsTargetConfig = field(default_factory=OpticsTargetConfig)
    constraint_config: BTSConstraintConfig = field(default_factory=BTSConstraintConfig)

    # Quadrupole bounds
    quad_bounds: Tuple[float, float] = (-3.0, 3.0)

    # Optimizer settings
    random_seed: int = 42
    max_iter: int = 100


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
    violations: List[str]
    iterations: int
    runtime_seconds: float
    message: str


class BaseOpticsObjective:
    """Abstract Strategy Interface for Optics Optimization Objectives."""
    def evaluate(self, strengths: np.ndarray) -> Dict[str, Any]:
        raise NotImplementedError

    def compute_residual_vector(self, strengths: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def compute_scalar_merit(self, strengths: np.ndarray) -> float:
        r_vec = self.compute_residual_vector(strengths)
        return float(np.sum(r_vec**2))


class DeterministicObjective(BaseOpticsObjective):
    """Deterministic single-seed optics matching objective strategy."""
    def __init__(self, config: Optional[BTSOptimizationConfig] = None):
        self.config = config or BTSOptimizationConfig()
        self.objectives = BTSNormalizedObjectives(self.config.target_config)
        self.constraints = BTSHardwareConstraints(self.config.constraint_config)
        self.nominal_strengths = self.objectives.nominal_strengths
        self.quad_names = self.objectives.quad_names

    def compute_residual_vector(self, strengths: np.ndarray) -> np.ndarray:
        return self.objectives.compute_residual_vector(strengths)

    def evaluate(self, strengths: np.ndarray) -> Dict[str, Any]:
        """
        Evaluate full physics propagation, normalized objectives, and hardware constraints.
        """
        self.objectives.set_quads(strengths)
        try:
            prop = compute_twiss_propagation(self.objectives.lattice, self.objectives.initial_twiss)
        except Exception:
            return {
                "feasible": False,
                "merit": 1e9,
                "mismatch_x": 1e6,
                "mismatch_y": 1e6,
                "max_beta_x": 1e6,
                "max_beta_y": 1e6,
                "violations": ["Propagator exception"]
            }

        r_vec = self.objectives.compute_residual_vector(strengths)
        merit = float(np.sum(r_vec**2))

        beta_end = prop["final_beta"]
        alpha_end = prop["final_alpha"]
        disp_end = prop["final_dispersion"]

        mx = compute_mismatch_metric(
            beta_end[0], alpha_end[0],
            self.config.target_config.target_beta_x, self.config.target_config.target_alpha_x
        )
        my = compute_mismatch_metric(
            beta_end[1], alpha_end[1],
            self.config.target_config.target_beta_y, self.config.target_config.target_alpha_y
        )

        validation = self.constraints.validate_full(strengths, prop)

        return {
            "feasible": validation["feasible"],
            "violations": validation["violations"],
            "merit": merit,
            "residual_vector": r_vec,
            "mismatch_x": float(mx),
            "mismatch_y": float(my),
            "disp_x_residual": float(disp_end[0] - self.config.target_config.target_disp_x),
            "disp_px_residual": float(disp_end[1] - self.config.target_config.target_disp_px),
            "max_beta_x": float(prop["max_beta_x"]),
            "max_beta_y": float(prop["max_beta_y"]),
            "beta_end": beta_end,
            "alpha_end": alpha_end,
            "disp_end": disp_end,
        }


# Maintain BTSOptimizationEvaluator as backward-compatible alias to DeterministicObjective
BTSOptimizationEvaluator = DeterministicObjective


class OpticsOptimizer:
    """
    Unified Optics Optimization Engine using Strategy Pattern.
    
    Supports deterministic, robust Monte Carlo, and multi-algorithm optimization
    routines while managing quadrupole hardware bounds and SVD Jacobian metrics.
    """
    def __init__(self,
                 objective: Optional[BaseOpticsObjective] = None,
                 config: Optional[BTSOptimizationConfig] = None):
        self.config = config or BTSOptimizationConfig()
        self.objective = objective or DeterministicObjective(self.config)

    def optimize(self,
                 method: str = "least_squares",
                 n_starts: int = 1) -> BTSOptimizationResult:
        """
        Run constrained two-stage or direct optimization on BTS quadrupole strengths.
        """
        initial_k = getattr(self.objective, "nominal_strengths", np.zeros(9))
        init_eval = self.objective.evaluate(initial_k)

        start_time = time.time()
        bounds_val = self.config.quad_bounds
        bounds_list = [bounds_val] * 9

        best_result = None
        best_merit = float('inf')
        rng = np.random.default_rng(self.config.random_seed)

        for start_idx in range(n_starts):
            if start_idx == 0:
                x0 = initial_k.copy()
            else:
                x0 = rng.uniform(bounds_val[0], bounds_val[1], size=9)

            if method in ("least_squares", "SLSQP"):
                # Stage 1: Least Squares matching
                ls_res = least_squares(
                    self.objective.compute_residual_vector,
                    x0,
                    bounds=(bounds_val[0], bounds_val[1]),
                    max_nfev=self.config.max_iter
                )
                # Stage 2: SLSQP refinement
                opt_res = minimize(
                    self.objective.compute_scalar_merit,
                    ls_res.x,
                    method="SLSQP",
                    bounds=bounds_list,
                    options={'maxiter': self.config.max_iter, 'ftol': 1e-6}
                )
            else:
                opt_res = minimize(
                    self.objective.compute_scalar_merit,
                    x0,
                    method=method,
                    bounds=bounds_list,
                    options={'maxiter': self.config.max_iter}
                )

            final_eval = self.objective.evaluate(opt_res.x)
            if final_eval["merit"] < best_merit:
                best_merit = final_eval["merit"]
                best_result = (opt_res, final_eval)

        opt_res, final_eval = best_result
        runtime = time.time() - start_time

        return BTSOptimizationResult(
            success=bool(opt_res.success and final_eval["feasible"]),
            method=method,
            optimized_strengths=np.array(opt_res.x),
            initial_merit=init_eval["merit"],
            final_merit=final_eval["merit"],
            initial_mismatch_x=init_eval["mismatch_x"],
            initial_mismatch_y=init_eval["mismatch_y"],
            final_mismatch_x=final_eval["mismatch_x"],
            final_mismatch_y=final_eval["mismatch_y"],
            final_max_beta_x=final_eval["max_beta_x"],
            final_max_beta_y=final_eval["max_beta_y"],
            final_disp_x_residual=final_eval["disp_x_residual"],
            constraints_satisfied=final_eval["feasible"],
            violations=final_eval["violations"],
            iterations=getattr(opt_res, "nit", getattr(opt_res, "nfev", 0)),
            runtime_seconds=round(runtime, 4),
            message=str(getattr(opt_res, "message", "Completed"))
        )


def optimize_bts_quadrupoles(method: str = "least_squares",
                             config: Optional[BTSOptimizationConfig] = None,
                             n_starts: int = 1) -> BTSOptimizationResult:
    """
    Run constrained two-stage or direct optimization on BTS quadrupole strengths.
    
    Delegates to OpticsOptimizer using DeterministicObjective strategy.
    """
    optimizer = OpticsOptimizer(config=config)
    return optimizer.optimize(method=method, n_starts=n_starts)


def compute_sensitivity_matrix(strengths: np.ndarray,
                               step_size: float = 1e-4,
                               config: Optional[BTSOptimizationConfig] = None) -> Dict[str, Any]:
    """
    Compute finite-difference Jacobian sensitivity matrix J_ij = dO_i / dK_j
    of exit optics observables (beta_x, beta_y, alpha_x, alpha_y, Dx, Dpx)
    with respect to the 9 quadrupole strengths K.
    """
    evaluator = BTSOptimizationEvaluator(config)

    obs_names = ['beta_x', 'beta_y', 'alpha_x', 'alpha_y', 'disp_x', 'disp_px']
    quad_names = evaluator.quad_names
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

    # Compute SVD and condition number
    U, S, Vt = np.linalg.svd(jacobian)
    cond_num = float(S[0] / S[-1]) if S[-1] > 0 else float('inf')

    return {
        "observable_names": obs_names,
        "quad_names": quad_names,
        "jacobian_matrix": jacobian,
        "singular_values": S,
        "condition_number": cond_num,
        "step_size": step_size,
    }


def round_strengths(strengths: np.ndarray, decimals: int = 6) -> np.ndarray:
    """Format quadrupole strengths to specified significant decimal digits."""
    return np.round(strengths, decimals=decimals)
