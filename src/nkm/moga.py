"""
Milestone 7 — Multi-Objective Genetic Algorithm (MOGA) Optimization Module

Implements NSGA-II Pareto optimization for BTS quadrupole strengths using pymoo.
Evaluates trade-offs between optical mismatch, peak beta function (aperture margin),
and residual dispersion, while enforcing hard lattice stability and beta constraints.
Includes representative design selection, full 6D re-evaluation, error robustness analysis,
result serialization, and publication-ready diagnostics plotting.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import os
import json
import pickle
import time
import numpy as np
import matplotlib.pyplot as plt

from pymoo.core.problem import ElementwiseProblem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.termination import get_termination

from .bts_lattice import BTSConfig, create_bts_lattice
from .optics import compute_twiss_propagation, compute_mismatch_metric
from .optimization import BTSOptimizationConfig, BTSOptimizationEvaluator
from .beam import generate_6d_beam, compute_beam_statistics
from .errors import ErrorBudgetConfig, evaluate_monte_carlo_robustness




@dataclass
class BTSMOGAConfig:
    """Configuration container for BTS MOGA Pareto optimization."""
    # MOGA Algorithm Parameters
    pop_size: int = 50
    n_gen: int = 40
    seed: int = 42
    
    # Decision Variable Bounds (9 quadrupoles)
    quad_bounds: Tuple[float, float] = (-5.0, 5.0)
    
    # Physics Constraints
    beta_max_limit: float = 60.0
    mismatch_max_limit: float = 50.0
    
    # Base BTS Optimization Config
    bts_opt_config: BTSOptimizationConfig = field(default_factory=BTSOptimizationConfig)
    
    # Finalist Re-evaluation Parameters
    eval_n_particles: int = 10000
    eval_n_mc_seeds: int = 50


@dataclass
class BTSMOGAResult:
    """Container for MOGA optimization outputs and re-evaluations."""
    success: bool
    pop_size: int
    n_gen: int
    n_evals: int
    runtime_seconds: float
    pareto_x: np.ndarray                 # Shape (N_pareto, 9)
    pareto_f: np.ndarray                 # Shape (N_pareto, 3): [mismatch, max_beta, residual_disp]
    pareto_g: np.ndarray                 # Shape (N_pareto, 3): constraint values <= 0
    pareto_cv: np.ndarray                # Constraint violation
    history_min_f: np.ndarray            # Shape (n_gen, 3) minimum objective per generation
    representative_solutions: Dict[str, Dict[str, Any]]
    finalist_evaluations: Dict[str, Dict[str, Any]]
    config: BTSMOGAConfig


class BTSMOGAProblem(ElementwiseProblem):
    """
    Pymoo ElementwiseProblem formulation for 9-quadrupole BTS MOGA optimization.
    
    Decision Variables:
        X = [K_q11, K_q12, K_q13, K_q21, K_q22, K_q23, K_q31, K_q32, K_q33]
        
    Objectives (to minimize):
        f1: Total optical mismatch M_x + M_y at BTS exit
        f2: Peak beta function max(beta_x_max, beta_y_max) (Aperture risk)
        f3: Residual dispersion magnitude sqrt(dx_residual^2 + dpx_residual^2)
        
    Inequality Constraints (g_i <= 0):
        g1: max_beta_x - beta_max_limit <= 0
        g2: max_beta_y - beta_max_limit <= 0
        g3: (M_x + M_y) - mismatch_max_limit <= 0
    """
    def __init__(self, config: Optional[BTSMOGAConfig] = None):
        self.moga_config = config or BTSMOGAConfig()
        self.evaluator = BTSOptimizationEvaluator(self.moga_config.bts_opt_config)
        
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
            # Unstable or unphysical lattice propagation
            out["F"] = [1e6, 1e6, 1e6]
            out["G"] = [1e6, 1e6, 1e6]
            return
            
        mx = res["mismatch_x"]
        my = res["mismatch_y"]
        f1 = mx + my
        f2 = max(res["max_beta_x"], res["max_beta_y"])
        f3 = float(np.sqrt(res["disp_x_residual"]**2 + res["disp_px_residual"]**2))
        
        g1 = res["max_beta_x"] - self.moga_config.beta_max_limit
        g2 = res["max_beta_y"] - self.moga_config.beta_max_limit
        g3 = f1 - self.moga_config.mismatch_max_limit
        
        out["F"] = [f1, f2, f3]
        out["G"] = [g1, g2, g3]


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
        raise ValueError("Cannot select representative solutions from an empty Pareto front.")

    idx_min_mismatch = int(np.argmin(pareto_f[:, 0]))
    idx_max_aperture = int(np.argmin(pareto_f[:, 1]))
    idx_min_disp = int(np.argmin(pareto_f[:, 2]))
    
    # Normalize objectives to [0, 1] for knee-point calculation
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


def reevaluate_finalists(representatives: Dict[str, Dict[str, Any]],
                         moga_config: BTSMOGAConfig) -> Dict[str, Dict[str, Any]]:
    """
    Perform optics evaluation and Monte Carlo error robustness analysis
    for the selected representative Pareto designs.
    """
    results = {}
    opt_evaluator = BTSOptimizationEvaluator(moga_config.bts_opt_config)
    err_budget = ErrorBudgetConfig()
    target_twiss = {
        "beta": [moga_config.bts_opt_config.target_beta_x, moga_config.bts_opt_config.target_beta_y],
        "alpha": [moga_config.bts_opt_config.target_alpha_x, moga_config.bts_opt_config.target_alpha_y]
    }

    for name, sol in representatives.items():
        strengths = np.array(sol["strengths_array"])
        
        # 1. Twiss optics evaluation
        optics_eval = opt_evaluator.evaluate(strengths)
        
        # 2. Construct BTSConfig with design quad strengths
        k_list = sol["strengths_array"]
        bts_cfg = BTSConfig(
            k_q11=k_list[0], k_q12=k_list[1], k_q13=k_list[2],
            k_q21=k_list[3], k_q22=k_list[4], k_q23=k_list[5],
            k_q31=k_list[6], k_q32=k_list[7], k_q33=k_list[8]
        )
        
        # 3. Monte Carlo robustness sampling
        mc_results = evaluate_monte_carlo_robustness(
            nominal_config=bts_cfg,
            target_twiss=target_twiss,
            n_samples=moga_config.eval_n_mc_seeds,
            seed=moga_config.seed
        )
        
        results[name] = {
            "mismatch_x": optics_eval["mismatch_x"],
            "mismatch_y": optics_eval["mismatch_y"],
            "max_beta_x": optics_eval["max_beta_x"],
            "max_beta_y": optics_eval["max_beta_y"],
            "disp_x_residual": optics_eval["disp_x_residual"],
            "disp_px_residual": optics_eval["disp_px_residual"],
            "mc_feasible_fraction": mc_results["feasible_fraction"],
            "mc_mismatch_x_mean": mc_results["mismatch_x"]["mean"],
            "mc_mismatch_x_p95": mc_results["mismatch_x"]["p95"],
            "mc_mismatch_y_mean": mc_results["mismatch_y"]["mean"],
            "mc_mismatch_y_p95": mc_results["mismatch_y"]["p95"],
            "mc_max_beta_x_p95": mc_results["max_beta_x_m"]["p95"],
            "mc_max_beta_y_p95": mc_results["max_beta_y_m"]["p95"],
        }
        
    return results




def run_bts_moga(config: Optional[BTSMOGAConfig] = None) -> BTSMOGAResult:
    """
    Run NSGA-II MOGA optimization for BTS quadrupoles.
    
    Returns:
        BTSMOGAResult instance containing Pareto front, representatives, and re-evaluations.
    """
    if config is None:
        config = BTSMOGAConfig()
        
    problem = BTSMOGAProblem(config)
    
    algorithm = NSGA2(
        pop_size=config.pop_size,
        eliminate_duplicates=True
    )
    
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
    
    # Extract feasible non-dominated solutions
    if res.opt is not None and len(res.opt) > 0:
        opt_x = np.atleast_2d(res.opt.get("X"))
        opt_f = np.atleast_2d(res.opt.get("F"))
        opt_g = np.atleast_2d(res.opt.get("G")) if res.opt.get("G") is not None else np.zeros((len(opt_f), 3))
        opt_cv = np.atleast_2d(res.opt.get("CV")).flatten() if res.opt.get("CV") is not None else np.zeros(len(opt_f))
    elif res.F is not None:
        opt_x = np.atleast_2d(res.X)
        opt_f = np.atleast_2d(res.F)
        opt_g = np.atleast_2d(res.G) if getattr(res, "G", None) is not None else np.zeros((len(opt_f), 3))
        opt_cv = np.atleast_2d(res.CV).flatten() if getattr(res, "CV", None) is not None else np.zeros(len(opt_f))
    else:
        pop_x = res.pop.get("X")
        pop_f = res.pop.get("F")
        pop_g = res.pop.get("G")
        pop_cv = res.pop.get("CV")
        opt_x = np.atleast_2d(pop_x)
        opt_f = np.atleast_2d(pop_f)
        opt_g = np.atleast_2d(pop_g) if pop_g is not None else np.zeros((len(opt_f), 3))
        opt_cv = np.atleast_2d(pop_cv).flatten() if pop_cv is not None else np.zeros(len(opt_f))
        
    # Ensure constraint feasibility (CV <= 1e-5)
    feasible_mask = (opt_cv <= 1e-5)
    
    if not np.any(feasible_mask):
        feasible_mask = np.ones(len(opt_f), dtype=bool)
        
    pareto_x = opt_x[feasible_mask]
    pareto_f = opt_f[feasible_mask]
    pareto_g = opt_g[feasible_mask]
    pareto_cv = opt_cv[feasible_mask]

    
    # History tracking (min objective per generation)
    n_gens_actual = len(res.history)
    history_min_f = np.zeros((n_gens_actual, 3))
    for i, algo in enumerate(res.history):
        pop_f = algo.pop.get("F")
        pop_cv = algo.pop.get("CV")
        feas = (pop_cv <= 1e-5).flatten() if pop_cv is not None else np.ones(len(pop_f), dtype=bool)
        if np.any(feas):
            history_min_f[i] = np.min(pop_f[feas], axis=0)
        else:
            history_min_f[i] = np.min(pop_f, axis=0)
            
    quad_names = ['q11', 'q12', 'q13', 'q21', 'q22', 'q23', 'q31', 'q32', 'q33']
    representatives = select_representative_solutions(pareto_x, pareto_f, quad_names)
    
    # Re-evaluate finalists
    finalist_evals = reevaluate_finalists(representatives, config)
    
    return BTSMOGAResult(
        success=bool(len(pareto_x) > 0),
        pop_size=config.pop_size,
        n_gen=config.n_gen,
        n_evals=int(res.algorithm.evaluator.n_eval),
        runtime_seconds=round(runtime, 4),
        pareto_x=pareto_x,
        pareto_f=pareto_f,
        pareto_g=pareto_g,
        pareto_cv=pareto_cv,
        history_min_f=history_min_f,
        representative_solutions=representatives,
        finalist_evaluations=finalist_evals,
        config=config
    )


def save_moga_results(result: BTSMOGAResult, output_dir: str = "results/moga"):
    """Save MOGA Pareto front, history, and representative solutions to results directory."""
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Save Pareto front CSV
    csv_header = "q11,q12,q13,q21,q22,q23,q31,q32,q33,mismatch_total,peak_beta,residual_dispersion"
    data = np.hstack([result.pareto_x, result.pareto_f])
    np.savetxt(os.path.join(output_dir, "moga_pareto_front.csv"), data, delimiter=",", header=csv_header, comments="")
    
    # 2. Save Representative solutions JSON
    with open(os.path.join(output_dir, "representative_solutions.json"), "w") as f:
        json.dump({
            "representatives": result.representative_solutions,
            "evaluations": result.finalist_evaluations
        }, f, indent=2)
        
    # 3. Save full result object pickle
    with open(os.path.join(output_dir, "moga_result.pkl"), "wb") as f:
        pickle.dump(result, f)


def plot_moga_summary(result: BTSMOGAResult, save_dir: Optional[str] = "results/moga"):
    """
    Generate and save publication-quality diagnostic plots for Milestone 7 MOGA study.
    """
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        
    pareto_f = result.pareto_f
    reps = result.representative_solutions
    
    # Figure 1: 2D Pareto Front Projections
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    
    # f1 vs f2
    sc1 = axes[0].scatter(pareto_f[:, 0], pareto_f[:, 1], c=pareto_f[:, 2], cmap='viridis', s=40, alpha=0.8)
    axes[0].set_xlabel(r"Total Mismatch $\mathcal{M}_x + \mathcal{M}_y$")
    axes[0].set_ylabel(r"Peak $\beta$ [m]")
    axes[0].set_title("Mismatch vs Peak Beta")
    axes[0].grid(True, linestyle="--", alpha=0.6)
    plt.colorbar(sc1, ax=axes[0], label=r"Residual Disp. [m]")
    
    # f1 vs f3
    sc2 = axes[1].scatter(pareto_f[:, 0], pareto_f[:, 2], c=pareto_f[:, 1], cmap='plasma', s=40, alpha=0.8)
    axes[1].set_xlabel(r"Total Mismatch $\mathcal{M}_x + \mathcal{M}_y$")
    axes[1].set_ylabel(r"Residual Dispersion [m]")
    axes[1].set_title("Mismatch vs Dispersion")
    axes[1].grid(True, linestyle="--", alpha=0.6)
    plt.colorbar(sc2, ax=axes[1], label=r"Peak $\beta$ [m]")
    
    # f2 vs f3
    sc3 = axes[2].scatter(pareto_f[:, 1], pareto_f[:, 2], c=pareto_f[:, 0], cmap='inferno', s=40, alpha=0.8)
    axes[2].set_xlabel(r"Peak $\beta$ [m]")
    axes[2].set_ylabel(r"Residual Dispersion [m]")
    axes[2].set_title("Peak Beta vs Dispersion")
    axes[2].grid(True, linestyle="--", alpha=0.6)
    plt.colorbar(sc3, ax=axes[2], label=r"Total Mismatch")
    
    # Highlight representative points
    colors_rep = {'min_mismatch': 'red', 'max_aperture_margin': 'green', 'min_dispersion': 'magenta', 'knee_point': 'blue'}
    markers_rep = {'min_mismatch': 'o', 'max_aperture_margin': 's', 'min_dispersion': '^', 'knee_point': 'D'}
    
    for name, sol in reps.items():
        f1, f2, f3 = sol["total_mismatch"], sol["peak_beta"], sol["residual_dispersion"]
        c, m = colors_rep[name], markers_rep[name]
        axes[0].scatter(f1, f2, color=c, marker=m, s=120, edgecolors='black', label=name, zorder=5)
        axes[1].scatter(f1, f3, color=c, marker=m, s=120, edgecolors='black', label=name, zorder=5)
        axes[2].scatter(f2, f3, color=c, marker=m, s=120, edgecolors='black', label=name, zorder=5)
        
    axes[0].legend(loc="upper right", fontsize=9)
    plt.tight_layout()
    if save_dir:
        fig.savefig(os.path.join(save_dir, "moga_pareto_front_2d.png"), dpi=300)
    plt.close(fig)
    
    # Figure 2: Convergence History
    fig, ax = plt.subplots(figsize=(8, 5))
    gens = np.arange(1, len(result.history_min_f) + 1)
    ax.plot(gens, result.history_min_f[:, 0], 'r-o', label=r"Min Mismatch ($\mathcal{M}_x+\mathcal{M}_y$)", markersize=4)
    ax.plot(gens, result.history_min_f[:, 1], 'g-s', label=r"Min Peak $\beta$ [m]", markersize=4)
    ax.plot(gens, result.history_min_f[:, 2] * 10.0, 'b-^', label=r"Min Residual Disp. [m] ($\times 10$)", markersize=4)
    ax.set_xlabel("Generation")
    ax.set_ylabel("Objective Value")
    ax.set_title("MOGA Convergence History Across Generations")
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(loc="upper right")
    plt.tight_layout()
    if save_dir:
        fig.savefig(os.path.join(save_dir, "moga_convergence.png"), dpi=300)
    plt.close(fig)
    
    # Figure 3: Parallel Coordinates of Pareto Solutions
    fig, ax = plt.subplots(figsize=(10, 5))
    quad_names = ['Q11', 'Q12', 'Q13', 'Q21', 'Q22', 'Q23', 'Q31', 'Q32', 'Q33']
    for i in range(len(result.pareto_x)):
        ax.plot(quad_names, result.pareto_x[i], color='gray', alpha=0.25, linewidth=1)
        
    for name, sol in reps.items():
        c = colors_rep[name]
        ax.plot(quad_names, sol["strengths_array"], color=c, linewidth=2.5, marker='o', label=name)
        
    ax.set_ylabel("Quadrupole Strength K [$m^{-2}$]")
    ax.set_title("Parallel Coordinates of Quad Strengths Across Pareto Set")
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(loc="upper right")
    plt.tight_layout()
    if save_dir:
        fig.savefig(os.path.join(save_dir, "moga_parallel_coordinates.png"), dpi=300)
    plt.close(fig)
