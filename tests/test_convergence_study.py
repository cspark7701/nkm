"""
Unit Tests for Task 06 — Converged Multi-Turn Injection Studies
Tests smoke/pilot/production config separation, bootstrap CI, convergence scans.
"""

import sys
from pathlib import Path
import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.nkm.convergence_study import (
    smoke_config,
    pilot_config,
    production_config,
    bootstrap_capture_ci,
    particle_count_convergence_scan,
    turn_count_convergence_scan,
    compute_first_loss_turn_distribution,
    compute_stored_beam_perturbation,
    compute_injection_acceptance,
    run_ensemble_study,
)
from src.nkm.storage_ring_injection import (
    StorageRingInjectionConfig,
    load_storage_ring_injection_lattice,
    track_multiturn_injection,
    TrackingResult,
)
from src.nkm.beam import generate_6d_beam


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def ring_and_config():
    cfg = StorageRingInjectionConfig()
    ring, nkm_idx = load_storage_ring_injection_lattice(cfg)
    return ring, cfg


# ---------------------------------------------------------------------------
# Config Separation Tests
# ---------------------------------------------------------------------------

class TestTierConfigs:
    def test_smoke_tier(self):
        t = smoke_config()
        assert t.n_particles == 100
        assert t.n_turns == 10
        assert t.label == "smoke"

    def test_pilot_tier(self):
        t = pilot_config()
        assert t.n_particles == 1000
        assert t.n_turns == 100
        assert t.label == "pilot"

    def test_production_tier(self):
        t = production_config()
        assert t.n_particles >= 10000
        assert t.n_turns >= 1000
        assert t.label == "production"

    def test_production_has_multiple_seeds(self):
        t = production_config()
        assert len(t.seeds) >= 3, "Production tier should use at least 3 seeds for bootstrap CI."

    def test_tiers_are_strictly_ordered(self):
        s, p, pr = smoke_config(), pilot_config(), production_config()
        assert s.n_particles < p.n_particles < pr.n_particles
        assert s.n_turns < p.n_turns < pr.n_turns


# ---------------------------------------------------------------------------
# Bootstrap CI Tests
# ---------------------------------------------------------------------------

class TestBootstrapCI:
    def test_deterministic_with_fixed_rng(self):
        survived = [95, 90, 88, 92, 85]
        rng = np.random.default_rng(42)
        res = bootstrap_capture_ci(survived, n_particles=100, rng=rng)
        assert "mean" in res and "ci_lo" in res and "ci_hi" in res and "ci_level" in res
        assert 0.0 < res["ci_lo"] <= res["mean"] <= res["ci_hi"] <= 1.0

    def test_ci_width_with_single_seed(self):
        """Bootstrap CI collapses to zero width when only one seed is used."""
        res = bootstrap_capture_ci([80], n_particles=100, rng=np.random.default_rng(0))
        assert res["n_seeds"] == 1
        assert res["std"] == 0.0

    def test_mean_matches_average_efficiency(self):
        survived = [500, 600, 700]
        n_part = 1000
        res = bootstrap_capture_ci(survived, n_particles=n_part, rng=np.random.default_rng(0))
        expected_mean = np.mean([0.5, 0.6, 0.7])
        assert abs(res["mean"] - expected_mean) < 1e-10

    def test_95_percent_ci_level(self):
        survived = [480, 520, 510, 490, 500]
        res = bootstrap_capture_ci(survived, n_particles=1000, ci_level=0.95)
        assert res["ci_level"] == 0.95


# ---------------------------------------------------------------------------
# Convergence Scan Tests
# ---------------------------------------------------------------------------

class TestConvergenceScans:
    def test_particle_count_scan_returns_correct_shape(self, ring_and_config):
        ring, config = ring_and_config
        results = particle_count_convergence_scan(
            n_particle_values=[50, 100],
            n_turns=5,
            ring=ring,
            kicker_model="off",
            kickmap_obj=None,
            config=config,
            seed=42
        )
        assert len(results) == 2
        assert all("n_particles" in r and "capture_efficiency" in r for r in results)

    def test_turn_count_scan_returns_correct_shape(self, ring_and_config):
        ring, config = ring_and_config
        results = turn_count_convergence_scan(
            n_turn_values=[2, 5],
            n_particles=50,
            ring=ring,
            kicker_model="off",
            kickmap_obj=None,
            config=config,
            seed=42
        )
        assert len(results) == 2
        assert all("n_turns" in r and "capture_efficiency" in r for r in results)


# ---------------------------------------------------------------------------
# First-Loss Turn Distribution Tests
# ---------------------------------------------------------------------------

class TestFirstLossTurnDistribution:
    def test_with_no_losses(self):
        res = TrackingResult(
            particles_6d=np.zeros((6, 100)),
            n_particles=100,
            survived_particles=100,
            survival_fraction=1.0,
            centroid=None,
            emittance_x_mrad=0.0,
            emittance_y_mrad=0.0,
            centroid_history=np.zeros((10, 2)),
            emittance_history=np.zeros((10, 2)),
            survival_history=[100] * 10,
            loss_log=[],
            metadata={}
        )
        dist = compute_first_loss_turn_distribution(res, n_turns=10)
        assert dist["n_lost_particles"] == 0
        assert dist["first_loss_turns"] == []

    def test_with_known_losses(self):
        loss_log = [
            {"particle_index": 0, "turn": 1, "cause": "aperture_exceeded"},
            {"particle_index": 1, "turn": 1, "cause": "aperture_exceeded"},
            {"particle_index": 2, "turn": 3, "cause": "aperture_exceeded"},
        ]
        res = TrackingResult(
            particles_6d=np.zeros((6, 100)),
            n_particles=100, survived_particles=97, survival_fraction=0.97,
            centroid=None, emittance_x_mrad=0.0, emittance_y_mrad=0.0,
            centroid_history=np.zeros((5, 2)), emittance_history=np.zeros((5, 2)),
            survival_history=[100, 99, 98, 97, 97], loss_log=loss_log, metadata={}
        )
        dist = compute_first_loss_turn_distribution(res, n_turns=5)
        assert dist["n_lost_particles"] == 3
        assert dist["fraction_lost_on_turn_1"] == pytest.approx(2 / 3)


# ---------------------------------------------------------------------------
# Stored-Beam Perturbation Tests
# ---------------------------------------------------------------------------

class TestStoredBeamPerturbation:
    def test_zero_perturbation_for_constant_centroid(self):
        n_turns = 10
        cent_hist = np.zeros((n_turns, 2))
        emit_hist = np.full((n_turns, 2), 1e-8)
        res = TrackingResult(
            particles_6d=np.zeros((6, 100)),
            n_particles=100, survived_particles=100, survival_fraction=1.0,
            centroid=None, emittance_x_mrad=1e-8, emittance_y_mrad=1e-9,
            centroid_history=cent_hist, emittance_history=emit_hist,
            survival_history=[100] * n_turns, loss_log=[], metadata={}
        )
        pert = compute_stored_beam_perturbation(res)
        assert pert["centroid_oscillation_x_mm"] == pytest.approx(0.0, abs=1e-12)
        assert pert["emittance_growth_x_percent"] == pytest.approx(0.0, abs=1e-10)


# ---------------------------------------------------------------------------
# Ensemble Study Integration Test (smoke tier, off kicker)
# ---------------------------------------------------------------------------

class TestEnsembleStudy:
    def test_smoke_ensemble_off_kicker(self, ring_and_config):
        ring, config = ring_and_config
        tier = smoke_config()
        tier.n_turns = 3  # Minimize runtime for unit tests

        result = run_ensemble_study(
            tier=tier,
            ring=ring,
            kicker_model="off",
            kickmap_obj=None,
            config=config,
            stored_beam_n_particles=50
        )

        assert result["kicker_model"] == "off"
        ci = result["capture_efficiency_ci"]
        assert 0.0 <= ci["mean"] <= 1.0
        assert ci["ci_lo"] <= ci["mean"] <= ci["ci_hi"]
        assert len(result["per_seed_results"]) == len(tier.seeds)
