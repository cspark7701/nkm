"""
Unit and Integration Tests for Milestone 4 BTS Deterministic Optimization
"""

import sys
from pathlib import Path
import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.nkm.optimization import (
    BTSOptimizationConfig,
    BTSOptimizationEvaluator,
    DeterministicObjective,
    OpticsOptimizer,
    optimize_bts_quadrupoles,
    compute_sensitivity_matrix
)
from src.nkm.robust_optimization import RobustMonteCarloObjective


@pytest.fixture
def opt_config():
    return BTSOptimizationConfig(random_seed=42)


@pytest.fixture
def evaluator(opt_config):
    return BTSOptimizationEvaluator(opt_config)


def test_optimization_evaluator_baseline(evaluator):
    """Test evaluator output on nominal baseline quadrupole strengths."""
    initial_k = evaluator.nominal_strengths
    res = evaluator.evaluate(initial_k)
    
    # Baseline lattice exceeds beta_max limit (beta_y_max = 242.6m > 60m), so feasible is False
    assert res["feasible"] is False
    assert res["merit"] > 1e5  # High baseline merit due to mismatch
    assert pytest.approx(res["mismatch_x"], abs=1e-2) == 8.67
    assert pytest.approx(res["mismatch_y"], abs=1e-2) == 28.61


def test_bts_optimization_slsqp(opt_config):
    """Test SLSQP optimization run and check merit reduction and constraint compliance."""
    res = optimize_bts_quadrupoles(method="SLSQP", config=opt_config, n_starts=1)
    
    assert res.success is True
    assert res.final_merit < res.initial_merit
    assert res.final_max_beta_x <= 60.0
    assert res.final_max_beta_y <= 60.0
    assert np.all(res.optimized_strengths >= -5.0)
    assert np.all(res.optimized_strengths <= 5.0)


def test_sensitivity_matrix(evaluator):
    """Test sensitivity matrix calculation and shape."""
    initial_k = evaluator.nominal_strengths
    sens = compute_sensitivity_matrix(initial_k)
    
    assert sens["jacobian_matrix"].shape == (6, 9)
    assert len(sens["observable_names"]) == 6
    assert len(sens["quad_names"]) == 9
    assert np.any(np.abs(sens["jacobian_matrix"]) > 1e-3)


def test_optimization_reproducibility(opt_config):
    """Verify that optimization with fixed seed is reproducible."""
    res1 = optimize_bts_quadrupoles(method="SLSQP", config=opt_config, n_starts=1)
    res2 = optimize_bts_quadrupoles(method="SLSQP", config=opt_config, n_starts=1)
    
    assert np.allclose(res1.optimized_strengths, res2.optimized_strengths, atol=1e-6)
    assert pytest.approx(res1.final_merit, abs=1e-6) == res2.final_merit


def test_optics_optimizer_strategy_pattern(opt_config):
    """Verify OpticsOptimizer execution with DeterministicObjective and RobustMonteCarloObjective."""
    det_obj = DeterministicObjective(opt_config)
    optimizer_det = OpticsOptimizer(objective=det_obj, config=opt_config)
    res_det = optimizer_det.optimize(method="SLSQP", n_starts=1)

    assert res_det.success is True
    assert res_det.final_merit < res_det.initial_merit

    # Verify RobustMonteCarloObjective strategy instantiation & evaluation
    robust_obj = RobustMonteCarloObjective(opt_config, n_samples=5, seed=42)
    robust_eval = robust_obj.evaluate(res_det.optimized_strengths)
    assert "robust_stats" in robust_eval
    assert "mismatch_x" in robust_eval

