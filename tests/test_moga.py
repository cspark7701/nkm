"""
Unit and Integration Tests for Milestone 7 MOGA Optimization
"""

import os
import tempfile
import pytest
import numpy as np

from nkm.moga import (
    BTSMOGAConfig,
    BTSMOGAProblem,
    run_bts_moga,
    select_representative_solutions,
    save_moga_results,
    plot_moga_summary
)


def test_moga_problem_evaluation():
    """Verify problem formulation, bounds, objectives, and constraints."""
    cfg = BTSMOGAConfig(pop_size=10, n_gen=2, seed=42)
    problem = BTSMOGAProblem(cfg)
    
    assert problem.n_var == 9
    assert problem.n_obj == 3
    assert problem.n_ieq_constr == 3
    assert np.all(problem.xl == -5.0)
    assert np.all(problem.xu == 5.0)
    
    # Test evaluation with nominal quadrupoles
    nominal_x = np.array([0.738, 0.415, 0.415, -0.9902, 1.288, 1.288, -2.08, 4.13, -2.24])
    out = {}
    problem._evaluate(nominal_x, out)
    
    assert "F" in out
    assert "G" in out
    assert len(out["F"]) == 3
    assert len(out["G"]) == 3
    # Check that mismatch and peak beta are positive finite floats
    assert out["F"][0] > 0
    assert out["F"][1] > 0
    assert out["F"][2] >= 0


def test_moga_deterministic_reproducibility():
    """Verify that running MOGA twice with the same seed produces identical Pareto fronts."""
    cfg = BTSMOGAConfig(pop_size=10, n_gen=5, seed=123, eval_n_particles=100, eval_n_mc_seeds=5)
    
    res1 = run_bts_moga(cfg)
    res2 = run_bts_moga(cfg)
    
    assert res1.success
    assert res2.success
    assert len(res1.pareto_x) == len(res2.pareto_x)
    np.testing.assert_allclose(res1.pareto_x, res2.pareto_x, rtol=1e-5, atol=1e-5)
    np.testing.assert_allclose(res1.pareto_f, res2.pareto_f, rtol=1e-5, atol=1e-5)


def test_representative_solution_selection():
    """Test selection of min_mismatch, max_aperture_margin, min_dispersion, and knee_point."""
    quad_names = ['q11', 'q12', 'q13', 'q21', 'q22', 'q23', 'q31', 'q32', 'q33']
    pareto_x = np.random.uniform(-2, 2, (5, 9))
    pareto_f = np.array([
        [10.0, 30.0, 0.5],
        [ 2.0, 50.0, 0.8],
        [15.0, 15.0, 0.2],
        [ 5.0, 25.0, 0.1],
        [ 8.0, 20.0, 0.4]
    ])
    
    reps = select_representative_solutions(pareto_x, pareto_f, quad_names)
    
    assert "min_mismatch" in reps
    assert "max_aperture_margin" in reps
    assert "min_dispersion" in reps
    assert "knee_point" in reps
    
    assert reps["min_mismatch"]["total_mismatch"] == 2.0
    assert reps["max_aperture_margin"]["peak_beta"] == 15.0
    assert reps["min_dispersion"]["residual_dispersion"] == 0.1


def test_moga_saving_and_plotting():
    """Test saving results and generating plot artifacts."""
    cfg = BTSMOGAConfig(pop_size=10, n_gen=3, seed=42, eval_n_particles=50, eval_n_mc_seeds=3)
    result = run_bts_moga(cfg)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        save_moga_results(result, output_dir=tmp_dir)
        
        assert os.path.exists(os.path.join(tmp_dir, "moga_pareto_front.csv"))
        assert os.path.exists(os.path.join(tmp_dir, "representative_solutions.json"))
        assert os.path.exists(os.path.join(tmp_dir, "moga_result.pkl"))
        
        plot_moga_summary(result, save_dir=tmp_dir)
        
        assert os.path.exists(os.path.join(tmp_dir, "moga_pareto_front_2d.png"))
        assert os.path.exists(os.path.join(tmp_dir, "moga_convergence.png"))
        assert os.path.exists(os.path.join(tmp_dir, "moga_parallel_coordinates.png"))
