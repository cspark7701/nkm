"""
NKM Multi-Turn Injection Convergence Study Module

Provides:
- Separated smoke / pilot / production simulation configurations
- Convergence scanning over particle count, turn count, NKM slice count, and random seed
- Bootstrap confidence interval estimation for capture efficiency
- Stored-beam perturbation quantification (centroid oscillation, emittance growth)
- Loss-map and first-loss-turn distribution reporting
- Injection acceptance and septum clearance metrics
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json
import numpy as np

from .storage_ring_injection import (
    StorageRingInjectionConfig,
    load_storage_ring_injection_lattice,
    track_multiturn_injection,
    TrackingResult,
)
from .beam import generate_6d_beam
from .kickmap import NKMKickMap2D


# ---------------------------------------------------------------------------
# Simulation-Tier Configuration Presets
# ---------------------------------------------------------------------------

@dataclass
class InjectionStudyTierConfig:
    """
    Defines one simulation tier (smoke / pilot / production).

    Fields
    ------
    n_particles : int
        Number of macro-particles per run.
    n_turns : int
        Number of storage-ring turns to track.
    n_slices : int
        NKM thick-kick symplectic slice count.
    seeds : list[int]
        Random seeds used for ensemble bootstrap.
    label : str
        Human-readable label for the tier.
    """
    n_particles: int
    n_turns: int
    n_slices: int
    seeds: List[int]
    label: str


def smoke_config() -> InjectionStudyTierConfig:
    """Smoke-test tier: fast CI validation, not suitable for physics claims."""
    return InjectionStudyTierConfig(
        n_particles=100,
        n_turns=10,
        n_slices=10,
        seeds=[42],
        label="smoke"
    )


def pilot_config() -> InjectionStudyTierConfig:
    """Pilot tier: intermediate study to establish convergence trends."""
    return InjectionStudyTierConfig(
        n_particles=1000,
        n_turns=100,
        n_slices=40,
        seeds=[42, 123, 777],
        label="pilot"
    )


def production_config() -> InjectionStudyTierConfig:
    """
    Production tier: numerically defensible results for publication.

    Particle count and turn count are chosen based on convergence evidence
    from the pilot study. Default values are conservative minima; increase
    if convergence scans show residuals above 0.1 percentage points.
    """
    return InjectionStudyTierConfig(
        n_particles=10000,
        n_turns=1000,
        n_slices=40,
        seeds=[42, 123, 777, 999, 2025],
        label="production"
    )


# ---------------------------------------------------------------------------
# Bootstrap Confidence Interval
# ---------------------------------------------------------------------------

def bootstrap_capture_ci(
    survived_per_seed: List[int],
    n_particles: int,
    n_bootstrap: int = 5000,
    ci_level: float = 0.95,
    rng: Optional[np.random.Generator] = None
) -> Dict[str, float]:
    """
    Estimate a bootstrap confidence interval for mean capture efficiency.

    Parameters
    ----------
    survived_per_seed : list[int]
        Number of surviving particles per seed run.
    n_particles : int
        Total injected particles per run (denominator for efficiency).
    n_bootstrap : int
        Number of bootstrap resamples.
    ci_level : float
        Confidence level (e.g. 0.95 for 95 % CI).
    rng : numpy.random.Generator, optional
        Random number generator for reproducibility.

    Returns
    -------
    dict with keys: mean, std, ci_lo, ci_hi, ci_level, n_seeds, n_bootstrap
    """
    if rng is None:
        rng = np.random.default_rng(0)
    efficiencies = np.asarray(survived_per_seed, dtype=float) / n_particles
    n_seeds = len(efficiencies)
    boot_means = np.array([
        np.mean(rng.choice(efficiencies, size=n_seeds, replace=True))
        for _ in range(n_bootstrap)
    ])
    alpha = (1.0 - ci_level) / 2.0
    ci_lo = float(np.percentile(boot_means, 100 * alpha))
    ci_hi = float(np.percentile(boot_means, 100 * (1 - alpha)))
    return {
        "mean": float(np.mean(efficiencies)),
        "std": float(np.std(efficiencies, ddof=1)) if n_seeds > 1 else 0.0,
        "ci_lo": ci_lo,
        "ci_hi": ci_hi,
        "ci_level": ci_level,
        "n_seeds": n_seeds,
        "n_bootstrap": n_bootstrap
    }


# ---------------------------------------------------------------------------
# Convergence Scanning
# ---------------------------------------------------------------------------

def particle_count_convergence_scan(
    n_particle_values: List[int],
    n_turns: int,
    ring,
    kicker_model: str,
    kickmap_obj: Optional[NKMKickMap2D],
    config: StorageRingInjectionConfig,
    seed: int = 42,
) -> List[Dict[str, Any]]:
    """
    Run injection tracking across a series of particle counts; return capture efficiencies.

    Returns
    -------
    list of dict, one per N_particles value, with fields:
        n_particles, survived, capture_efficiency
    """
    results = []
    for np_val in n_particle_values:
        beam = generate_6d_beam(
            n_particles=np_val,
            beta_x=10.0, alpha_x=0.0, emit_x=1e-7,
            beta_y=5.0, alpha_y=0.0, emit_y=1e-8,
            x_offset=config.septum_x_offset_m,
            seed=seed
        )
        res = track_multiturn_injection(
            beam, ring, n_turns=n_turns,
            kicker_model=kicker_model,
            kickmap_obj=kickmap_obj,
            config=config
        )
        results.append({
            "n_particles": np_val,
            "survived": res.survived_particles,
            "capture_efficiency": res.survival_fraction
        })
    return results


def turn_count_convergence_scan(
    n_turn_values: List[int],
    n_particles: int,
    ring,
    kicker_model: str,
    kickmap_obj: Optional[NKMKickMap2D],
    config: StorageRingInjectionConfig,
    seed: int = 42,
) -> List[Dict[str, Any]]:
    """
    Run injection tracking across a series of turn counts; return survival at end of each run.
    """
    results = []
    beam_base = generate_6d_beam(
        n_particles=n_particles,
        beta_x=10.0, alpha_x=0.0, emit_x=1e-7,
        beta_y=5.0, alpha_y=0.0, emit_y=1e-8,
        x_offset=config.septum_x_offset_m,
        seed=seed
    )
    for n_turn_val in n_turn_values:
        res = track_multiturn_injection(
            beam_base.copy(), ring, n_turns=n_turn_val,
            kicker_model=kicker_model,
            kickmap_obj=kickmap_obj,
            config=config
        )
        results.append({
            "n_turns": n_turn_val,
            "survived": res.survived_particles,
            "capture_efficiency": res.survival_fraction
        })
    return results


# ---------------------------------------------------------------------------
# First-Loss Turn Distribution
# ---------------------------------------------------------------------------

def compute_first_loss_turn_distribution(tracking_result: TrackingResult, n_turns: int) -> Dict[str, Any]:
    """
    From loss_log, compute distribution of first loss turns.

    Returns
    -------
    dict with keys:
        first_loss_turns : list[int], turn of first loss for each lost particle
        turn_histogram : dict[int, int], number of first losses per turn
        mean_first_loss_turn : float
        fraction_lost_on_turn_1 : float
    """
    particle_first_loss: Dict[int, int] = {}
    for entry in tracking_result.loss_log:
        pidx = entry.get("particle_index", entry.get("particle_idx", -1))
        turn = entry.get("turn", 0)
        if pidx not in particle_first_loss:
            particle_first_loss[pidx] = turn

    first_loss_turns = list(particle_first_loss.values())
    histogram: Dict[int, int] = {}
    for t in range(1, n_turns + 1):
        histogram[t] = sum(1 for v in first_loss_turns if v == t)

    n_lost = len(first_loss_turns)
    mean_first = float(np.mean(first_loss_turns)) if n_lost > 0 else float("nan")
    frac_turn1 = float(histogram.get(1, 0) / n_lost) if n_lost > 0 else float("nan")

    return {
        "first_loss_turns": first_loss_turns,
        "turn_histogram": histogram,
        "mean_first_loss_turn": mean_first,
        "fraction_lost_on_turn_1": frac_turn1,
        "n_lost_particles": n_lost
    }


# ---------------------------------------------------------------------------
# Stored-Beam Perturbation
# ---------------------------------------------------------------------------

def compute_stored_beam_perturbation(stored_result: TrackingResult) -> Dict[str, float]:
    """
    Quantify stored-beam perturbation from NKM fringe fields.

    Metrics
    -------
    centroid_oscillation_x_mm : max |<x>| over turns
    centroid_oscillation_y_mm : max |<y>| (if available)
    emittance_growth_x_percent : relative emittance growth
    emittance_growth_y_percent : relative emittance growth vertical
    """
    cent_hist = stored_result.centroid_history  # shape (n_turns, 2): [x_mm, xp_mrad]
    emit_hist = stored_result.emittance_history   # shape (n_turns, 2): [emit_x, emit_y]

    valid_cx = cent_hist[:, 0][~np.isnan(cent_hist[:, 0])]
    centroid_osc_x = float(np.max(np.abs(valid_cx))) if len(valid_cx) > 0 else float("nan")

    emit_x = emit_hist[:, 0][~np.isnan(emit_hist[:, 0])]
    emit_y = emit_hist[:, 1][~np.isnan(emit_hist[:, 1])]
    emittance_growth_x = float(((emit_x[-1] - emit_x[0]) / emit_x[0]) * 100.0) if len(emit_x) > 1 and emit_x[0] > 0 else 0.0
    emittance_growth_y = float(((emit_y[-1] - emit_y[0]) / emit_y[0]) * 100.0) if len(emit_y) > 1 and emit_y[0] > 0 else 0.0

    return {
        "centroid_oscillation_x_mm": centroid_osc_x,
        "emittance_growth_x_percent": emittance_growth_x,
        "emittance_growth_y_percent": emittance_growth_y
    }


# ---------------------------------------------------------------------------
# Injection Acceptance (sweep over x-offset)
# ---------------------------------------------------------------------------

def compute_injection_acceptance(
    x_offsets_m: np.ndarray,
    n_particles: int,
    n_turns: int,
    ring,
    kicker_model: str,
    kickmap_obj: Optional[NKMKickMap2D],
    config: StorageRingInjectionConfig,
    seed: int = 42,
) -> List[Dict[str, Any]]:
    """
    Sweep injection x-offset to map the injection acceptance window.

    Returns
    -------
    list of dict, one per x_offset_m, with fields:
        x_offset_m, x_offset_mm, capture_efficiency
    """
    results = []
    for x_off in x_offsets_m:
        beam = generate_6d_beam(
            n_particles=n_particles,
            beta_x=10.0, alpha_x=0.0, emit_x=1e-7,
            beta_y=5.0, alpha_y=0.0, emit_y=1e-8,
            x_offset=float(x_off),
            seed=seed
        )
        res = track_multiturn_injection(
            beam, ring, n_turns=n_turns,
            kicker_model=kicker_model,
            kickmap_obj=kickmap_obj,
            config=config
        )
        results.append({
            "x_offset_m": float(x_off),
            "x_offset_mm": float(x_off * 1e3),
            "capture_efficiency": res.survival_fraction
        })
    return results


# ---------------------------------------------------------------------------
# Full Multi-Seed Ensemble Runner
# ---------------------------------------------------------------------------

def run_ensemble_study(
    tier: InjectionStudyTierConfig,
    ring,
    kicker_model: str,
    kickmap_obj: Optional[NKMKickMap2D],
    config: Optional[StorageRingInjectionConfig] = None,
    stored_beam_n_particles: int = 1000,
) -> Dict[str, Any]:
    """
    Run multi-seed ensemble injection study for one (kicker_model, tier) combination.

    Returns
    -------
    dict with:
        label, kicker_model, tier
        capture_efficiency_ci (bootstrap CI dict)
        per_seed_results (list of per-seed metric dicts)
        stored_perturbation (mean across seeds)
        first_loss_distribution (from seed 0)
    """
    if config is None:
        config = StorageRingInjectionConfig()

    survived_counts: List[int] = []
    per_seed: List[Dict[str, Any]] = []
    all_stored_perturbations: List[Dict[str, float]] = []
    first_loss_dist: Optional[Dict[str, Any]] = None

    for i, seed in enumerate(tier.seeds):
        beam = generate_6d_beam(
            n_particles=tier.n_particles,
            beta_x=10.0, alpha_x=0.0, emit_x=1e-7,
            beta_y=5.0, alpha_y=0.0, emit_y=1e-8,
            x_offset=config.septum_x_offset_m,
            seed=seed
        )
        stored_beam = generate_6d_beam(
            n_particles=stored_beam_n_particles,
            beta_x=10.0, alpha_x=0.0, emit_x=1e-8,
            beta_y=5.0, alpha_y=0.0, emit_y=1e-9,
            x_offset=0.0,
            seed=seed
        )

        inj_res = track_multiturn_injection(
            beam, ring, n_turns=tier.n_turns,
            kicker_model=kicker_model,
            kickmap_obj=kickmap_obj,
            config=config
        )
        stored_res = track_multiturn_injection(
            stored_beam, ring, n_turns=tier.n_turns,
            kicker_model=kicker_model,
            kickmap_obj=kickmap_obj,
            config=config
        )

        survived_counts.append(inj_res.survived_particles)
        perturbation = compute_stored_beam_perturbation(stored_res)
        all_stored_perturbations.append(perturbation)

        fld = compute_first_loss_turn_distribution(inj_res, tier.n_turns)
        if i == 0:
            first_loss_dist = fld

        # Septum clearance: |final_centroid_x - septum_x|
        final_centroid = inj_res.centroid
        if final_centroid is not None:
            sep_clearance_mm = abs(final_centroid["x_mm"] - config.septum_x_offset_m * 1e3)
        else:
            sep_clearance_mm = float("nan")

        per_seed.append({
            "seed": seed,
            "n_particles": tier.n_particles,
            "n_turns": tier.n_turns,
            "survived": inj_res.survived_particles,
            "capture_efficiency": inj_res.survival_fraction,
            "centroid_x_mm": final_centroid["x_mm"] if final_centroid else float("nan"),
            "emittance_x_mrad": inj_res.emittance_x_mrad,
            "emittance_y_mrad": inj_res.emittance_y_mrad,
            "septum_clearance_mm": sep_clearance_mm,
            "n_losses": len(inj_res.loss_log),
            "stored_perturbation": perturbation
        })

    ci = bootstrap_capture_ci(survived_counts, tier.n_particles)

    # Mean stored perturbation across seeds
    mean_perturbation: Dict[str, float] = {}
    for k in all_stored_perturbations[0]:
        vals = [p[k] for p in all_stored_perturbations if not np.isnan(p[k])]
        mean_perturbation[k] = float(np.mean(vals)) if vals else float("nan")

    return {
        "label": tier.label,
        "kicker_model": kicker_model,
        "tier": {
            "n_particles": tier.n_particles,
            "n_turns": tier.n_turns,
            "n_slices": tier.n_slices,
            "seeds": tier.seeds
        },
        "capture_efficiency_ci": ci,
        "per_seed_results": per_seed,
        "mean_stored_perturbation": mean_perturbation,
        "first_loss_distribution": first_loss_dist,
    }
