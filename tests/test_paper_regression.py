"""
Automated Regression Tests for Key Journal Paper Results and Metrics (Milestone 8)
"""

import os
import tempfile
import pytest
import numpy as np

from nkm.bts_lattice import BTSConfig, create_bts_lattice
from nkm.optics import compute_twiss_propagation, compute_mismatch_metric
from nkm.kickmap import NKMKickMap2D, load_2d_kickmap

from nkm.paper import run_paper_pipeline


def test_baseline_paper_metrics():
    """Verify baseline unoptimized lattice parameters and mismatch values."""
    config_base = BTSConfig()
    lat_base = create_bts_lattice(config_base)
    twiss_init = {'beta': [7.56, 12.27], 'alpha': [1.52, -1.65], 'dispersion': [0.2762, -0.0657, 0, 0]}
    prop_base = compute_twiss_propagation(lat_base, twiss_init)
    
    target_beta_x, target_alpha_x = 2.336495, -0.016335
    target_beta_y, target_alpha_y = 4.256241, 0.017772
    
    mx = compute_mismatch_metric(prop_base["final_beta"][0], prop_base["final_alpha"][0], target_beta_x, target_alpha_x)
    my = compute_mismatch_metric(prop_base["final_beta"][1], prop_base["final_alpha"][1], target_beta_y, target_alpha_y)
    
    assert abs(mx - 8.6746) < 0.1
    assert abs(my - 28.6147) < 0.2
    assert abs((mx + my) - 37.2893) < 0.3
    assert prop_base["max_beta_y"] > 200.0  # Baseline severely violates 60m beta limit


def test_slsqp_paper_metrics():
    """Verify SLSQP optimized lattice satisfies hard beta constraints and reduces mismatch."""
    config_slsqp = BTSConfig(
        k_q11=0.47419899, k_q12=-1.70822248, k_q13=1.33402498,
        k_q21=-1.05419705, k_q22=1.63861169, k_q23=-0.98192641,
        k_q31=1.08602944, k_q32=-1.67069631, k_q33=0.92706350
    )
    lat_slsqp = create_bts_lattice(config_slsqp)
    twiss_init = {'beta': [7.56, 12.27], 'alpha': [1.52, -1.65], 'dispersion': [0.2762, -0.0657, 0, 0]}
    prop_slsqp = compute_twiss_propagation(lat_slsqp, twiss_init)
    
    target_beta_x, target_alpha_x = 2.336495, -0.016335
    target_beta_y, target_alpha_y = 4.256241, 0.017772
    
    my = compute_mismatch_metric(prop_slsqp["final_beta"][1], prop_slsqp["final_alpha"][1], target_beta_y, target_alpha_y)
    
    assert my < 5.0
    assert prop_slsqp["max_beta_x"] <= 60.0
    assert prop_slsqp["max_beta_y"] <= 60.0


def test_nkm_field_paper_metrics():
    """Verify RADIA 2D kick map evaluated at injection offset (-16 mm) produces negative integrated kick."""
    kickmap = NKMKickMap2D("kickmap_file.txt")
    kx_val, ky_val = kickmap.evaluate(-0.016, 0.0)
    
    assert kx_val < 0.0
    assert abs(kx_val) > 1.0






def test_paper_pipeline_execution():
    """Verify paper reproduction pipeline exports all tables, figures, and summary JSON."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        summary = run_paper_pipeline(output_dir=tmp_dir)
        
        assert len(summary["tables_generated"]) == 3
        assert len(summary["figures_generated"]) == 6  # 3 PNG + 3 PDF
        assert os.path.exists(os.path.join(tmp_dir, "paper_summary_metrics.json"))
        assert os.path.exists(os.path.join(tmp_dir, "tables", "table1_bts_parameters.tex"))
        assert os.path.exists(os.path.join(tmp_dir, "figures", "fig1_bts_optics_comparison.png"))
