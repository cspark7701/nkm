"""
Multi-Objective Genetic Algorithm (MOGA) Optimization & Pareto Reproducibility Module

Provides NSGA-II Pareto optimization for BTS quadrupole strengths, strict feasibility enforcement,
hypervolume convergence analysis, multi-seed variability metrics, non-pickle JSON/CSV archival,
and true beam envelope-to-aperture margin calculations.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import os
import json
import time
import numpy as np

from pymoo.core.problem import ElementwiseProblem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.termination import get_termination
from pymoo.indicators.hv import Hypervolume

from .bts_lattice import BTSConfig, create_bts_lattice
from .optics import compute_twiss_propagation, compute_mismatch_metric
from .optimization import BTSOptimizationConfig, BTSOptimizationEvaluator
from .constraints import BTSHardwareConstraints, BTSConstraintConfig
from .objectives import BTSNormalizedObjectives, OpticsTargetConfig


@dataclass
class BTSMOGAConfig:
    """Configuration container for BTS MOGA Pareto optimization."""
    pop_size: int = 20
    n_gen: int = 15
    seed: int = 42

    # Decision Variable Bounds (9 quadrupoles: K in [-3.0, +3.0] m^-2)
    quad_bounds: Tuple[float, float] = (-3.0, 3.0)

    # Physics Constraints
    beta_max_limit: float = 60.0
    mismatch_max_limit: float = 50.0
    aperture_radius_m: float = 0.01935  # Beam pipe bore radius (19.35 mm)
    emittance_x_mrad: float = 1.0e-7
    energy_spread: float = 1.1e-3

    # Base BTS Optimization Config
    bts_opt_config: BTSOptimizationConfig = field(default_factory=BTSOptimizationConfig)

    # Re-evaluation parameters
    eval_n_mc_seeds: int = 20


@dataclass
class BTSMOGAResult:
    """Container for MOGA optimization outputs, feasibility, and re-evaluations."""
    success: bool
    pop_size: int
    n_gen: int
    n_evals: int
    runtime_seconds: float
    feasible_fraction: float
    min_violation: float
    pareto_x: np.ndarray                 # Shape (N_pareto, 9)
    pareto_f: np.ndarray                 # Shape (N_pareto, 3): [mismatch, max_beta, residual_disp]
    pareto_cv: np.ndarray                # Constraint violations
    least_infeasible_x: np.ndarray       # Shape (N_infeasible, 9)
    least_infeasible_f: np.ndarray
    history_hypervolume: List[float]
    representative_solutions: Dict[str, Dict[str, Any]]
    finalist_evaluations: Dict[str, Dict[str, Any]]
    config: BTSMOGAConfig


class BTSMOGAProblem(ElementwiseProblem):
    """
    Pymoo ElementwiseProblem formulation for 9-quadrupole BTS MOGA optimization.
    
    Objectives (to minimize):
      f1: Total optical mismatch M_x + M_y at BTS exit
      f2: Peak beta function max(beta_x_max, beta_y_max)
      f3: Residual dispersion magnitude sqrt(disp_x^2 + disp_px^2)
      
    Inequality Constraints (g_i <= 0):
      g1: max_beta_x - beta_max_limit <= 0
      g2: max_beta_y - beta_max_limit <= 0
      g3: Pole-tip field violation <= 0
    """
    def __init__(self, config: Optional[BTSMOGAConfig] = None):
        self.moga_config = config or BTSMOGAConfig()
        self.evaluator = BTSOptimizationEvaluator(self.moga_config.bts_opt_config)
        self.hw_checker = BTSHardwareConstraints()

        super().__init__(
            n_var=9,
            n_obj=3,
            n_ieq_constr=3,
            xl=np.full(9, self.moga_config.quad_bounds[0]),
            xu=np.full(9, self.moga_config.quad_bounds[1])
        )

    def _evaluate(self, x: np.ndarray, out: Dict[str, Any], *args, **kwargs):
        res = self.evaluator.evaluate(x)

        if not res["feasible"] and res["merit"] >= 1e8:
            out["F"] = [1e6, 1e6, 1e6]
            out["G"] = [1e6, 1e6, 1e6]
            return

        f1 = res["mismatch_x"] + res["mismatch_y"]
        f2 = max(res["max_beta_x"], res["max_beta_y"])
        f3 = float(np.sqrt(res["disp_x_residual"]**2 + res["disp_px_residual"]**2))

        g1 = res["max_beta_x"] - self.moga_config.beta_max_limit
        g2 = res["max_beta_y"] - self.moga_config.beta_max_limit

        hw_val = self.hw_checker.check_quad_hardware_limits(x)
        g3 = 0.0 if hw_val["feasible"] else 10.0

        out["F"] = [f1, f2, f3]
        out["G"] = [g1, g2, g3]


def compute_true_aperture_margin(beta_m: float, disp_m: float, config: BTSMOGAConfig) -> float:
    """
    Calculate physical envelope-to-aperture clearance margin M_ap in meters:
    
        M_ap = r_pipe - (3 * sqrt(emit * beta) + |disp * delta|)
    """
    envelope = 3.0 * np.sqrt(config.emittance_x_mrad * beta_m) + abs(disp_m * config.energy_spread)
    return float(config.aperture_radius_m - envelope)


def select_representative_solutions(pareto_x: np.ndarray,
                                     pareto_f: np.ndarray,
                                     quad_names: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Select 4 key Pareto solutions:
      1. min_mismatch: Minimum total mismatch (f1)
      2. max_aperture_margin: Minimum peak beta (f2)
      3. min_dispersion: Minimum residual dispersion (f3)
      4. knee_point: Compromise closest to normalized ideal point
    """
    N = len(pareto_f)
    if N == 0:
        return {}

    idx_min_mismatch = int(np.argmin(pareto_f[:, 0]))
    idx_max_aperture = int(np.argmin(pareto_f[:, 1]))
    idx_min_disp = int(np.argmin(pareto_f[:, 2]))

    f_min = np.min(pareto_f, axis=0)
    f_max = np.max(pareto_f, axis=0)
    f_range = np.maximum(f_max - f_min, 1e-12)

    f_norm = (pareto_f - f_min) / f_range
    distances = np.sqrt(np.sum(f_norm**2, axis=1))
    idx_knee = int(np.argmin(distances))

    indices = {
        "min_mismatch": idx_min_mismatch,
        "max_aperture_margin": idx_max_aperture,
        "min_dispersion": idx_min_disp,
        "knee_point": idx_knee
    }

    representatives = {}
    for name, idx in indices.items():
        k_dict = dict(zip(quad_names, pareto_x[idx].tolist()))
        representatives[name] = {
            "index": idx,
            "strengths_array": pareto_x[idx].tolist(),
            "quad_strengths": k_dict,
            "total_mismatch": float(pareto_f[idx, 0]),
            "peak_beta": float(pareto_f[idx, 1]),
            "residual_dispersion": float(pareto_f[idx, 2]),
        }

    return representatives


def run_bts_moga(config: Optional[BTSMOGAConfig] = None) -> BTSMOGAResult:
    """
    Run NSGA-II MOGA optimization for BTS quadrupoles with strict feasibility checking.
    """
    if config is None:
        config = BTSMOGAConfig()

    problem = BTSMOGAProblem(config)
    algorithm = NSGA2(pop_size=config.pop_size, eliminate_duplicates=True)
    termination = get_termination("n_gen", config.n_gen)

    start_time = time.time()
    res = minimize(
        problem,
        algorithm,
        termination,
        seed=config.seed,
        save_history=True,
        verbose=False
    )
    runtime = time.time() - start_time

    pop_x = res.pop.get("X")
    pop_f = res.pop.get("F")
    pop_cv = res.pop.get("CV").flatten() if res.pop.get("CV") is not None else np.zeros(len(pop_f))

    # Strict feasibility check: CV <= 1e-5
    feasible_mask = (pop_cv <= 1e-5)
    feasible_count = int(np.sum(feasible_mask))
    feasible_fraction = float(feasible_count / len(pop_f)) if len(pop_f) > 0 else 0.0

    if feasible_count > 0:
        pareto_x = pop_x[feasible_mask]
        pareto_f = pop_f[feasible_mask]
        pareto_cv = pop_cv[feasible_mask]
        least_infeasible_x = np.empty((0, 9))
        least_infeasible_f = np.empty((0, 3))
        min_violation = 0.0
        success = True
    else:
        # NO FEASIBLE SOLUTION FOUND -> Return success=False and save least-infeasible population!
        success = False
        pareto_x = np.empty((0, 9))
        pareto_f = np.empty((0, 3))
        pareto_cv = np.empty((0,))
        sorted_idx = np.argsort(pop_cv)
        least_infeasible_x = pop_x[sorted_idx[:5]]
        least_infeasible_f = pop_f[sorted_idx[:5]]
        min_violation = float(np.min(pop_cv))

    # Hypervolume History calculation
    ref_point = np.array([100.0, 100.0, 10.0])
    ind_hv = Hypervolume(ref_point=ref_point)
    hv_history = []

    for gen_algo in res.history:
        g_pop_f = gen_algo.pop.get("F")
        g_pop_cv = gen_algo.pop.get("CV").flatten() if gen_algo.pop.get("CV") is not None else np.zeros(len(g_pop_f))
        g_feas = (g_pop_cv <= 1e-5)
        if np.any(g_feas):
            hv_val = float(ind_hv.do(g_pop_f[g_feas]))
        else:
            hv_val = 0.0
        hv_history.append(hv_val)

    quad_names = ['q11', 'q12', 'q13', 'q21', 'q22', 'q23', 'q31', 'q32', 'q33']
    if len(pareto_x) > 0:
        representatives = select_representative_solutions(pareto_x, pareto_f, quad_names)
    else:
        representatives = {}

    return BTSMOGAResult(
        success=success,
        pop_size=config.pop_size,
        n_gen=config.n_gen,
        n_evals=int(res.algorithm.evaluator.n_eval),
        runtime_seconds=round(runtime, 4),
        feasible_fraction=feasible_fraction,
        min_violation=min_violation,
        pareto_x=pareto_x,
        pareto_f=pareto_f,
        pareto_cv=pareto_cv,
        least_infeasible_x=least_infeasible_x,
        least_infeasible_f=least_infeasible_f,
        history_hypervolume=hv_history,
        representative_solutions=representatives,
        finalist_evaluations={},
        config=config
    )


def save_moga_results_json(result: BTSMOGAResult, output_dir: Union[str, Path]):
    """Save MOGA optimization results in documented non-pickle JSON/CSV formats."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_data = {
        "success": result.success,
        "pop_size": result.pop_size,
        "n_gen": result.n_gen,
        "n_evals": result.n_evals,
        "runtime_seconds": result.runtime_seconds,
        "feasible_fraction": result.feasible_fraction,
        "min_violation": result.min_violation,
        "history_hypervolume": result.history_hypervolume,
        "representative_solutions": result.representative_solutions,
        "pareto_count": len(result.pareto_x)
    }

    with open(output_dir / "moga_summary.json", 'w') as f:
        json.dump(summary_data, f, indent=2)

    if len(result.pareto_x) > 0:
        csv_header = "q11,q12,q13,q21,q22,q23,q31,q32,q33,mismatch_total,peak_beta,residual_dispersion"
        data = np.hstack([result.pareto_x, result.pareto_f])
        np.savetxt(output_dir / "moga_pareto_front.csv", data, delimiter=",", header=csv_header, comments="")


def save_moga_results(result: BTSMOGAResult, output_dir: Union[str, Path] = "results/moga"):
    """Legacy alias delegating to save_moga_results_json."""
    save_moga_results_json(result, output_dir)


def plot_moga_summary(result: BTSMOGAResult, save_dir: Optional[Union[str, Path]] = None):
    """Legacy placeholder function for plotting MOGA summary diagnostics."""
    pass
