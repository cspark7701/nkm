"""
Unit and integration tests for src/nkm/storage_ring_injection.py (Task 04)
"""

import sys
from pathlib import Path
import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.nkm.storage_ring_injection import (
    StorageRingInjectionConfig,
    load_storage_ring_injection_lattice,
    track_multiturn_injection,
    compute_multiturn_injection_metrics
)
from src.nkm.beam import generate_6d_beam
from src.nkm.kickmap import NKMKickMap2D


@pytest.fixture
def ring_and_nkm():
    config = StorageRingInjectionConfig()
    ring, nkm_idx = load_storage_ring_injection_lattice(config)
    return ring, nkm_idx


@pytest.fixture
def kickmap_obj():
    p = REPO_ROOT / "kickmap_file.txt"
    assert p.is_file()
    return NKMKickMap2D(p)


def test_storage_ring_loading(ring_and_nkm):
    ring, nkm_idx = ring_and_nkm
    assert len(ring) > 3000
    assert nkm_idx == 1


def test_multiturn_tracking_models(ring_and_nkm, kickmap_obj):
    ring, _ = ring_and_nkm
    config = StorageRingInjectionConfig()

    # Fast test distribution: 50 particles, 5 turns
    injected_beam = generate_6d_beam(
        n_particles=50,
        beta_x=10.0, alpha_x=0.0, emit_x=1e-7,
        beta_y=5.0, alpha_y=0.0, emit_y=1e-8,
        x_offset=-0.016,
        seed=42
    )

    stored_beam = generate_6d_beam(
        n_particles=50,
        beta_x=10.0, alpha_x=0.0, emit_x=1e-8,
        beta_y=5.0, alpha_y=0.0, emit_y=1e-9,
        x_offset=0.0,
        seed=42
    )

    models = ["off", "ideal", "linear", "fieldmap"]

    for model in models:
        inj_res = track_multiturn_injection(
            injected_beam, ring, n_turns=5,
            kicker_model=model, kickmap_obj=kickmap_obj,
            config=config
        )

        stored_res = track_multiturn_injection(
            stored_beam, ring, n_turns=5,
            kicker_model=model, kickmap_obj=kickmap_obj,
            config=config
        )

        metrics = compute_multiturn_injection_metrics(inj_res, stored_res, config)

        assert "capture_efficiency" in metrics
        assert 0.0 <= metrics["capture_efficiency"] <= 1.0
        assert "stored_beam_centroid_oscillation_mm" in metrics
