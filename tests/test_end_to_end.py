"""
Unit Tests for Task 05 — End-to-End BTS-to-Storage-Ring Coupling
"""

import sys
from pathlib import Path
import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.nkm.end_to_end import (
    BoosterExtractionConfig,
    generate_booster_extraction_distribution,
    run_end_to_end_pipeline
)
from src.nkm.bts_lattice import BTSConfig
from src.nkm.storage_ring_injection import StorageRingInjectionConfig


def test_booster_extraction_distribution():
    """Test canonical booster extraction 6D beam generation."""
    cfg = BoosterExtractionConfig(n_particles=200, seed=42)
    beam = generate_booster_extraction_distribution(cfg)

    assert beam.shape == (6, 200)
    assert not np.any(np.isnan(beam))
    assert pytest.approx(np.mean(beam[0, :]), abs=1e-4) == 0.0
    assert pytest.approx(np.mean(beam[2, :]), abs=1e-4) == 0.0


def test_end_to_end_pipeline_execution():
    """Test complete end-to-end tracking pipeline from booster to storage ring."""
    booster_cfg = BoosterExtractionConfig(n_particles=100, seed=42)
    bts_cfg = BTSConfig()
    ring_cfg = StorageRingInjectionConfig()

    res = run_end_to_end_pipeline(
        booster_config=booster_cfg,
        bts_config=bts_cfg,
        ring_config=ring_cfg,
        n_turns=2,
        kicker_model="ideal"
    )

    assert "bts_transmission" in res
    assert "bts_exit_beam" in res
    assert "ring_tracking_result" in res

    assert res["bts_transmission"] == 1.0
    assert res["ring_tracking_result"].survived_particles > 0
    assert res["overall_end_to_end_efficiency"] > 0.80
