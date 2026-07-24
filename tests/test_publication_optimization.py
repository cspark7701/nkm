"""
Unit and integration tests for publication BTS optimization (Task 05)
"""

import sys
from pathlib import Path
import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.nkm.constraints import BTSHardwareConstraints, BTSConstraintConfig
from src.nkm.objectives import BTSNormalizedObjectives, OpticsTargetConfig
from src.nkm.optimization import (
    BTSOptimizationConfig,
    BTSOptimizationEvaluator,
    optimize_bts_quadrupoles,
    compute_sensitivity_matrix,
    round_strengths
)


def test_hardware_bounds_and_pole_fields():
    config = BTSConstraintConfig()
    constraints = BTSHardwareConstraints(config)

    # Valid strengths
    k_valid = np.array([0.448, -1.026, 0.887, -1.066, 1.488, -0.669, 0.589, -1.168, 0.941])
    hw_val = constraints.check_quad_hardware_limits(k_valid)
    assert hw_val["feasible"] is True
    assert hw_val["max_pole_field_T"] < 1.2

    # Invalid strength (exceeds 3.0 m^-2)
    k_invalid = k_valid.copy()
    k_invalid[0] = 5.0
    hw_inv = constraints.check_quad_hardware_limits(k_invalid)
    assert hw_inv["feasible"] is False
    assert len(hw_inv["violations"]) > 0


def test_normalized_objectives():
    objectives = BTSNormalizedObjectives()
    initial_k = objectives.nominal_strengths

    r_vec = objectives.compute_residual_vector(initial_k)
    assert len(r_vec) == 6
    merit = objectives.compute_scalar_merit(initial_k)
    assert merit >= 0.0


def test_optimization_reproducibility():
    config = BTSOptimizationConfig(random_seed=42, max_iter=5)

    # Run optimization with seed 42
    res1 = optimize_bts_quadrupoles(method="least_squares", config=config, n_starts=1)
    # Run optimization again with same seed 42
    res2 = optimize_bts_quadrupoles(method="least_squares", config=config, n_starts=1)

    np.testing.assert_allclose(res1.optimized_strengths, res2.optimized_strengths, atol=1e-12)
    assert res1.final_merit == pytest.approx(res2.final_merit, rel=1e-9)


def test_sensitivity_matrix():
    objectives = BTSNormalizedObjectives()
    initial_k = objectives.nominal_strengths

    sens = compute_sensitivity_matrix(initial_k, step_size=1e-4)

    assert sens["jacobian_matrix"].shape == (6, 9)
    assert len(sens["singular_values"]) == 6
    assert sens["condition_number"] > 0.0


def test_significant_digits():
    k = np.array([0.44857219481, -1.026778931, 0.887640112])
    k_rounded = round_strengths(k, decimals=6)
    assert len(str(k_rounded[0]).split('.')[1]) <= 6
