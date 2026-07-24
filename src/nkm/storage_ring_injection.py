"""
NKM Multi-Turn Storage Ring Injection Dynamics Module

Provides storage ring lattice loading, 4-model kicker simulation (NKM Off, Ideal Kicker,
Linear Kicker, RADIA Fieldmap NKM), multi-turn physical aperture tracking, loss accounting,
and injection performance metrics calculation.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import at

from .units import (
    KickMapMetadata,
    compute_rigidity,
    convert_kick_angle,
    integrated_field_to_kick,
    ELECTRON_CHARGE_C
)
from .beam import (
    generate_6d_beam,
    compute_beam_centroid,
    compute_projected_emittance,
    compute_beam_statistics
)
from .tracking import track_nkm_thin_kick, track_nkm_thick_symplectic
from .kickmap import NKMKickMap2D


@dataclass
class StorageRingInjectionConfig:
    """Configuration parameters for storage ring injection simulation."""
    mat_filename: str = "storage_ring_lattice_nkm.mat"
    energy_eV: float = 4.0e9
    nkm_length_m: float = 0.525
    septum_x_offset_m: float = -0.016
    septum_thickness_m: float = 0.002
    aperture_x_m: float = 0.030        # Horizontal physical aperture (+/- 30 mm)
    aperture_y_m: float = 0.015        # Vertical physical aperture (+/- 15 mm)
    enable_radiation: bool = False
    enable_rf: bool = True
    particle_charge_C: float = ELECTRON_CHARGE_C


def load_storage_ring_injection_lattice(config: Optional[StorageRingInjectionConfig] = None,
                                        mat_path: Optional[Union[str, Path]] = None) -> Tuple[at.Lattice, int]:
    """
    Load storage ring AT lattice and return (lattice, nkm_element_index).
    """
    if config is None:
        config = StorageRingInjectionConfig()

    if mat_path is None:
        repo_root = Path(__file__).resolve().parent.parent.parent
        mat_path = repo_root / config.mat_filename
    else:
        mat_path = Path(mat_path)

    if not mat_path.is_file():
        raise FileNotFoundError(f"Storage ring lattice file not found: {mat_path}")

    ring = at.load_mat(mat_path)

    # Enable radiation / RF if configured
    if config.enable_radiation:
        ring = ring.enable_6d(at.Radiative, copy=True)
    elif config.enable_rf:
        ring = ring.enable_6d(copy=True)

    # Find NKM element index
    nkm_idx = 1  # Default position after SectionStart
    for idx, elem in enumerate(ring):
        if hasattr(elem, 'FamName') and elem.FamName == 'NKM':
            nkm_idx = idx
            break

    return ring, nkm_idx


def track_multiturn_injection(beam: np.ndarray,
                              ring: at.Lattice,
                              n_turns: int = 10,
                              kicker_model: str = "fieldmap",
                              kickmap_obj: Optional[NKMKickMap2D] = None,
                              scale_factor: float = 1.0,
                              config: Optional[StorageRingInjectionConfig] = None) -> Dict[str, Any]:
    """
    Track a 6D particle distribution through the storage ring for n_turns with physical apertures.
    
    Kicker Models:
      - 'off': NKM off (0 kick)
      - 'ideal': Constant -5.7491 mrad kick on turn 1
      - 'linear': Linearized quadrupole + dipole kick model on turn 1
      - 'fieldmap': Full RADIA 2D kick map on turn 1
      
    Turn 1: Kicker is active.
    Turns 2..n_turns: Kicker is inactive (0 kick).
    """
    if config is None:
        config = StorageRingInjectionConfig()

    energy_GeV = config.energy_eV * 1e-9
    n_particles = beam.shape[1]
    current_beam = beam.copy()

    # Track histories
    turn_centroids = []
    turn_emittances = []
    turn_survived = []
    loss_log = []  # List of dicts recording (particle_idx, turn, cause)

    # Aperture bounds
    ap_x = config.aperture_x_m
    ap_y = config.aperture_y_m

    for turn in range(1, n_turns + 1):
        # 1. Apply Kicker on Turn 1 only
        if turn == 1 and kicker_model != "off":
            if kicker_model == "ideal":
                meta_ideal = KickMapMetadata(
                    coordinate_unit="m",
                    value_type="kick_angle",
                    value_unit="mrad",
                    beam_energy_eV=config.energy_eV
                )
                def kick_ideal(x, y):
                    return np.full_like(x, -5.7491), np.zeros_like(y)
                current_beam = track_nkm_thin_kick(
                    current_beam, kick_ideal,
                    scale_factor=scale_factor,
                    length_m=config.nkm_length_m,
                    energy_GeV=energy_GeV,
                    metadata=meta_ideal
                )
            elif kicker_model == "linear":
                meta_linear = KickMapMetadata(
                    coordinate_unit="m",
                    value_type="kick_angle",
                    value_unit="mrad",
                    beam_energy_eV=config.energy_eV
                )
                # Linear approximation: -5.7491 mrad dipole + quadrupole gradient
                def kick_linear(x, y):
                    k0 = -5.7491
                    k1 = 0.35  # mrad/mm
                    kx = k0 + k1 * (x * 1e3)
                    ky = -k1 * (y * 1e3)
                    return kx, ky
                current_beam = track_nkm_thin_kick(
                    current_beam, kick_linear,
                    scale_factor=scale_factor,
                    length_m=config.nkm_length_m,
                    energy_GeV=energy_GeV,
                    metadata=meta_linear
                )
            elif kicker_model == "fieldmap" and kickmap_obj is not None:
                current_beam = track_nkm_thin_kick(
                    current_beam, kickmap_obj.evaluate,
                    scale_factor=scale_factor,
                    length_m=config.nkm_length_m,
                    energy_GeV=energy_GeV,
                    metadata=kickmap_obj.metadata
                )

        # 2. Track through 1 turn of the storage ring
        res = ring.track(current_beam, nturns=1)
        if isinstance(res, tuple):
            current_beam = res[0][:, :, 0, 0]
        elif isinstance(res, np.ndarray):
            if res.ndim == 4:
                current_beam = res[:, :, 0, 0]
            elif res.ndim == 3:
                current_beam = res[:, :, 0]
            else:
                current_beam = res

        # 3. Check physical aperture limits & loss accounting
        valid_mask = ~np.isnan(current_beam[0, :])
        for p_idx in range(n_particles):
            if valid_mask[p_idx]:
                x_p = current_beam[0, p_idx]
                y_p = current_beam[2, p_idx]
                if abs(x_p) > ap_x or abs(y_p) > ap_y:
                    current_beam[:, p_idx] = np.nan
                    loss_log.append({
                        "particle_index": p_idx,
                        "turn": turn,
                        "cause": "aperture_exceeded",
                        "x_m": float(x_p),
                        "y_m": float(y_p)
                    })

        # Record turn statistics
        stats = compute_beam_statistics(current_beam)
        turn_survived.append(stats["survived_particles"])
        if stats["centroid"] is not None:
            turn_centroids.append([stats["centroid"]["x_mm"], stats["centroid"]["xp_mrad"]])
        else:
            turn_centroids.append([np.nan, np.nan])
        turn_emittances.append([stats["emittance_x_mrad"], stats["emittance_y_mrad"]])

    final_stats = compute_beam_statistics(current_beam)

    return {
        "kicker_model": kicker_model,
        "n_turns": n_turns,
        "n_particles": n_particles,
        "final_beam": current_beam,
        "final_stats": final_stats,
        "turn_survived": turn_survived,
        "turn_centroids": np.array(turn_centroids),
        "turn_emittances": np.array(turn_emittances),
        "loss_log": loss_log,
        "capture_efficiency": final_stats["survival_fraction"]
    }


def compute_multiturn_injection_metrics(injected_results: Dict[str, Any],
                                        stored_results: Dict[str, Any],
                                        config: Optional[StorageRingInjectionConfig] = None) -> Dict[str, Any]:
    """
    Compute comprehensive multi-turn injection quality metrics.
    """
    if config is None:
        config = StorageRingInjectionConfig()

    # Capture efficiency & loss fraction for injected beam
    cap_eff = float(injected_results["capture_efficiency"])
    loss_frac = float(1.0 - cap_eff)

    # Stored beam centroid oscillation amplitude (in mm)
    stored_centroids_x = stored_results["turn_centroids"][:, 0]
    valid_c_x = stored_centroids_x[~np.isnan(stored_centroids_x)]
    if len(valid_c_x) > 0:
        stored_osc_amplitude_mm = float(np.max(np.abs(valid_c_x)))
    else:
        stored_osc_amplitude_mm = np.nan

    # Stored beam emittance growth
    stored_emitt_x = stored_results["turn_emittances"][:, 0]
    valid_emitt = stored_emitt_x[~np.isnan(stored_emitt_x)]
    if len(valid_emitt) > 1 and valid_emitt[0] > 0:
        emitt_growth_pct = float(((valid_emitt[-1] - valid_emitt[0]) / valid_emitt[0]) * 100.0)
    else:
        emitt_growth_pct = 0.0

    # Septum clearance (in mm)
    final_inj_x = injected_results["final_stats"]["centroid"]["x_mm"] if injected_results["final_stats"]["centroid"] else np.nan
    septum_x_mm = config.septum_x_offset_m * 1e3
    septum_clearance_mm = float(abs(final_inj_x - septum_x_mm)) if not np.isnan(final_inj_x) else 0.0

    return {
        "kicker_model": injected_results["kicker_model"],
        "capture_efficiency": cap_eff,
        "loss_fraction": loss_frac,
        "stored_beam_centroid_oscillation_mm": stored_osc_amplitude_mm,
        "stored_beam_emittance_growth_percent": emitt_growth_pct,
        "septum_clearance_mm": septum_clearance_mm,
        "total_losses_count": len(injected_results["loss_log"])
    }
