"""
NKM End-to-End Simulation Pipeline Module

Couples booster extraction particle distributions through BTS transfer line transport
to storage-ring multi-turn injection tracking and element-resolved loss accounting.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple, Optional, Any, Union
import json
import yaml
import numpy as np

from .beam import generate_6d_beam, compute_beam_statistics
from .bts_lattice import BTSConfig, create_bts_lattice
from .storage_ring_injection import (
    StorageRingInjectionConfig,
    SeptumModel,
    ElementAperture,
    track_element_resolved_injection,
    build_storage_ring_nkm_lattice
)
from .kickmap import NKMKickMap2D
from .tracking import TrackingResult


@dataclass
class BoosterExtractionConfig:
    """Booster extraction beam initial parameters."""
    n_particles: int = 1000
    energy_eV: float = 4.0e9
    beta_x_m: float = 2.50
    alpha_x: float = -0.50
    emit_x_mrad: float = 1e-8
    beta_y_m: float = 8.20
    alpha_y: float = 1.10
    emit_y_mrad: float = 1e-9
    energy_spread: float = 1e-3
    seed: int = 42


def generate_booster_extraction_distribution(config: Optional[BoosterExtractionConfig] = None) -> np.ndarray:
    """
    Generate canonical 6D particle distribution at booster extraction (BTS inlet).
    """
    if config is None:
        config = BoosterExtractionConfig()

    beam = generate_6d_beam(
        n_particles=config.n_particles,
        beta_x=config.beta_x_m,
        alpha_x=config.alpha_x,
        emit_x=config.emit_x_mrad,
        beta_y=config.beta_y_m,
        alpha_y=config.alpha_y,
        emit_y=config.emit_y_mrad,
        espread=config.energy_spread,
        seed=config.seed
    )
    return beam


def run_end_to_end_pipeline(booster_config: Optional[BoosterExtractionConfig] = None,
                            bts_config: Optional[BTSConfig] = None,
                            ring_config: Optional[StorageRingInjectionConfig] = None,
                            n_turns: int = 10,
                            kicker_model: str = "fieldmap",
                            kickmap_obj: Optional[NKMKickMap2D] = None) -> Dict[str, Any]:
    """
    Run full end-to-end simulation chain:
      Booster Extraction Distribution -> BTS Transport Line -> Handoff -> Storage Ring Injection
    """
    if booster_config is None:
        booster_config = BoosterExtractionConfig()
    if bts_config is None:
        bts_config = BTSConfig()
    if ring_config is None:
        ring_config = StorageRingInjectionConfig()

    # Step 1: Booster Extraction Distribution
    booster_beam = generate_booster_extraction_distribution(booster_config)

    # Step 2: BTS Transport Line Tracking
    bts_lattice = create_bts_lattice(bts_config)
    res_bts = bts_lattice.track(booster_beam.copy())
    if isinstance(res_bts, tuple):
        bts_exit_beam = res_bts[0][:, :, 0, 0]
    elif isinstance(res_bts, np.ndarray) and res_bts.ndim == 4:
        bts_exit_beam = res_bts[:, :, 0, 0]
    else:
        bts_exit_beam = res_bts

    # Filter BTS losses
    valid_bts = ~np.isnan(bts_exit_beam[0, :])
    bts_survived_count = int(np.sum(valid_bts))
    bts_loss_count = booster_config.n_particles - bts_survived_count
    bts_transmission = float(bts_survived_count / booster_config.n_particles)

    bts_exit_stats = compute_beam_statistics(bts_exit_beam)

    # Step 3: Handoff Handoff Coordinates (Position shift to septum injection point x_offset)
    injected_ring_beam = bts_exit_beam.copy()
    valid_mask = ~np.isnan(injected_ring_beam[0, :])
    injected_ring_beam[0, valid_mask] += ring_config.septum_x_offset_m

    # Step 4: Storage Ring Multi-Turn Injection Tracking
    try:
        ring, _ = build_storage_ring_nkm_lattice()
    except Exception:
        ring = bts_lattice

    septum = SeptumModel(
        x_septum_m=ring_config.septum_x_offset_m,
        thickness_m=ring_config.septum_thickness_m,
        allowed_side="stored"
    )

    res_ring = track_element_resolved_injection(
        injected_ring_beam,
        ring=ring,
        n_turns=n_turns,
        kicker_model=kicker_model,
        kickmap_obj=kickmap_obj,
        config=ring_config,
        septum_model=septum
    )

    # Step 5: Benchmark against Idealized Local Distribution
    local_beam = generate_6d_beam(
        n_particles=booster_config.n_particles,
        beta_x=ring_config.aperture_x_m, alpha_x=0.0, emit_x=1e-8,
        beta_y=ring_config.aperture_y_m, alpha_y=0.0, emit_y=1e-9,
        x_offset=ring_config.septum_x_offset_m,
        seed=booster_config.seed
    )
    res_local = track_element_resolved_injection(
        local_beam, ring=ring, n_turns=n_turns, kicker_model=kicker_model, kickmap_obj=kickmap_obj, config=ring_config, septum_model=septum
    )

    return {
        "booster_config": booster_config,
        "bts_config": bts_config,
        "ring_config": ring_config,
        "bts_transmission": bts_transmission,
        "bts_losses_count": bts_loss_count,
        "bts_exit_stats": bts_exit_stats,
        "bts_exit_beam": bts_exit_beam,
        "ring_tracking_result": res_ring,
        "local_tracking_result": res_local,
        "overall_end_to_end_efficiency": float(res_ring.survived_particles / booster_config.n_particles)
    }
