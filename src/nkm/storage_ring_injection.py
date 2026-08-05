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
from .tracking import track_nkm_thin_kick, track_nkm_thick_symplectic, TrackingResult
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


@dataclass
class SeptumModel:
    """
    Physical Septum Magnet Wall Model for Storage Ring Injection.
    """
    x_septum_m: float = -0.016         # Septum sheet inner edge position (m)
    thickness_m: float = 0.002          # Septum blade thickness (m)
    element_name: str = "SEPTUM"        # Target element name
    s_position_m: float = 0.0           # s-coordinate (m)
    allowed_side: str = "stored"        # 'stored' (x > x_septum) or 'injected' (x < x_septum - thickness)

    @property
    def x_outer_m(self) -> float:
        return self.x_septum_m - self.thickness_m

    def check_collision(self, x: np.ndarray) -> np.ndarray:
        """
        Return boolean array where True indicates particle collides with physical septum wall or invalid side.
        """
        wall_collision = (x <= self.x_septum_m) & (x >= self.x_outer_m)
        if self.allowed_side == "stored":
            invalid_side = x <= self.x_septum_m
            return wall_collision | invalid_side
        elif self.allowed_side == "injected":
            invalid_side = x >= self.x_outer_m
            return wall_collision | invalid_side
        return wall_collision


@dataclass
class ElementAperture:
    """Element-resolved physical aperture limits."""
    x_min: float = -0.030  # -30 mm
    x_max: float = +0.030  # +30 mm
    y_min: float = -0.015  # -15 mm
    y_max: float = +0.015  # +15 mm

    def check_loss(self, x: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Returns boolean masks for (loss_xmin, loss_xmax, loss_ymin, loss_ymax)."""
        loss_xmin = x < self.x_min
        loss_xmax = x > self.x_max
        loss_ymin = y < self.y_min
        loss_ymax = y > self.y_max
        return loss_xmin, loss_xmax, loss_ymin, loss_ymax


def build_storage_ring_nkm_lattice(source_mat_path: Optional[Union[str, Path]] = None) -> at.Lattice:
    """
    Build storage ring lattice with NKM inserted from original K4GSR_HBIv4-1.mat source data.
    """
    if source_mat_path is None:
        repo_root = Path(__file__).resolve().parent.parent.parent
        source_mat_path = repo_root / "K4GSR_HBIv4-1.mat"
    else:
        source_mat_path = Path(source_mat_path)

    if not source_mat_path.is_file():
        raise FileNotFoundError(f"Original source storage ring lattice not found: {source_mat_path}")

    original_lattice = at.load_mat(source_mat_path)
    section_start = original_lattice[0]
    section_end = original_lattice[-1]

    storage_ring_lattice = original_lattice[2:len(original_lattice)-1]

    dr_nkm_up_ring = at.Drift('NKMUPRING', 2.0)
    dr_nkm = at.Drift('NKM', 0.525)
    dr_nkm_down = at.Drift('NKMDOWN', 0.175)

    storage_ring_lattice.append(dr_nkm_up_ring)
    storage_ring_lattice.append(section_end)

    storage_ring_lattice.insert(0, dr_nkm_down)
    storage_ring_lattice.insert(0, dr_nkm)
    storage_ring_lattice.insert(0, section_start)

    return storage_ring_lattice


def load_storage_ring_injection_lattice(config: Optional[StorageRingInjectionConfig] = None,
                                        mat_path: Optional[Union[str, Path]] = None,
                                        auto_generate: bool = True) -> Tuple[at.Lattice, int]:
    """
    Load storage ring AT lattice and return (lattice, nkm_element_index).
    If mat_path does not exist and auto_generate is True, resurrects storage_ring_lattice_nkm.mat
    from K4GSR_HBIv4-1.mat.
    """
    if config is None:
        config = StorageRingInjectionConfig()

    if mat_path is None:
        repo_root = Path(__file__).resolve().parent.parent.parent
        mat_path = repo_root / config.mat_filename
    else:
        mat_path = Path(mat_path)

    if not mat_path.is_file():
        if auto_generate:
            lattice = build_storage_ring_nkm_lattice()
            at.save_mat(lattice, mat_path)
        else:
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

    return TrackingResult(
        particles_6d=current_beam,
        n_particles=n_particles,
        survived_particles=int(final_stats["survived_particles"]),
        survival_fraction=float(final_stats["survival_fraction"]),
        centroid=final_stats["centroid"],
        emittance_x_mrad=float(final_stats["emittance_x_mrad"]),
        emittance_y_mrad=float(final_stats["emittance_y_mrad"]),
        centroid_history=np.array(turn_centroids),
        emittance_history=np.array(turn_emittances),
        survival_history=turn_survived,
        loss_log=loss_log,
        metadata={
            "kicker_model": kicker_model,
            "n_turns": n_turns,
        }
    )


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


def track_element_resolved_injection(beam: np.ndarray,
                                      ring: at.Lattice,
                                      n_turns: int = 10,
                                      kicker_model: str = "fieldmap",
                                      kickmap_obj: Optional[NKMKickMap2D] = None,
                                      scale_factor: float = 1.0,
                                      config: Optional[StorageRingInjectionConfig] = None,
                                      septum_model: Optional[SeptumModel] = None,
                                      element_apertures: Optional[Dict[int, ElementAperture]] = None) -> TrackingResult:
    """
    Track 6D particle distribution through storage ring element-by-element over n_turns.
    Detects physical aperture losses and septum collisions at the exact element where they occur.
    """
    if config is None:
        config = StorageRingInjectionConfig()

    if septum_model is None:
        septum_model = SeptumModel(
            x_septum_m=config.septum_x_offset_m,
            thickness_m=config.septum_thickness_m,
            element_name="SEPTUM"
        )

    default_aperture = ElementAperture(
        x_min=-config.aperture_x_m,
        x_max=+config.aperture_x_m,
        y_min=-config.aperture_y_m,
        y_max=+config.aperture_y_m
    )

    energy_GeV = config.energy_eV * 1e-9
    n_particles = beam.shape[1]
    current_beam = beam.copy()

    turn_centroids = []
    turn_emittances = []
    turn_survived = []
    loss_log = []

    # Get s positions of lattice elements
    try:
        s_positions = ring.get_s_pos()
    except Exception:
        s_positions = np.zeros(len(ring))

    for turn in range(1, n_turns + 1):
        for elem_idx, elem in enumerate(ring):
            s_pos = float(s_positions[elem_idx]) if elem_idx < len(s_positions) else 0.0
            elem_name = getattr(elem, "FamName", f"ELEM_{elem_idx}")

            # Apply NKM kicker on turn 1
            if turn == 1 and elem_name == "NKM" and kicker_model != "off":
                if kicker_model == "ideal":
                    meta_ideal = KickMapMetadata(coordinate_unit="m", value_type="kick_angle", value_unit="mrad", beam_energy_eV=config.energy_eV)
                    kick_ideal = lambda x, y: (np.full_like(x, -5.7491), np.zeros_like(y))
                    current_beam = track_nkm_thin_kick(current_beam, kick_ideal, scale_factor=scale_factor, length_m=config.nkm_length_m, energy_GeV=energy_GeV, metadata=meta_ideal)
                elif kicker_model == "linear":
                    meta_linear = KickMapMetadata(coordinate_unit="m", value_type="kick_angle", value_unit="mrad", beam_energy_eV=config.energy_eV)
                    kick_linear = lambda x, y: (-5.7491 + 0.35 * (x * 1e3), -0.35 * (y * 1e3))
                    current_beam = track_nkm_thin_kick(current_beam, kick_linear, scale_factor=scale_factor, length_m=config.nkm_length_m, energy_GeV=energy_GeV, metadata=meta_linear)
                elif kicker_model == "fieldmap" and kickmap_obj is not None:
                    current_beam = track_nkm_thin_kick(current_beam, kickmap_obj.evaluate, scale_factor=scale_factor, length_m=config.nkm_length_m, energy_GeV=energy_GeV, metadata=kickmap_obj.metadata)
            else:
                # Track single element
                res_elem = elem.track(current_beam)
                if isinstance(res_elem, tuple):
                    current_beam = res_elem[0]
                elif isinstance(res_elem, np.ndarray) and res_elem.ndim == 4:
                    current_beam = res_elem[:, :, 0, 0]

            # Element-resolved loss checks
            valid_mask = ~np.isnan(current_beam[0, :])
            if not np.any(valid_mask):
                continue

            ap = element_apertures.get(elem_idx, default_aperture) if element_apertures else default_aperture

            x_pts = current_beam[0, :]
            y_pts = current_beam[2, :]

            loss_xmin, loss_xmax, loss_ymin, loss_ymax = ap.check_loss(x_pts, y_pts)

            septum_hit = np.zeros(n_particles, dtype=bool)
            if "SEPTUM" in elem_name.upper() or elem_name == "NKM":
                septum_hit = septum_model.check_collision(x_pts)

            for p_idx in range(n_particles):
                if valid_mask[p_idx]:
                    cause = None
                    if septum_hit[p_idx]:
                        cause = "septum_collision"
                    elif loss_xmin[p_idx] or loss_xmax[p_idx]:
                        cause = "aperture_x_exceeded"
                    elif loss_ymin[p_idx] or loss_ymax[p_idx]:
                        cause = "aperture_y_exceeded"

                    if cause is not None:
                        loss_log.append({
                            "particle_index": p_idx,
                            "turn": turn,
                            "element_index": elem_idx,
                            "element_name": elem_name,
                            "s_position_m": s_pos,
                            "cause": cause,
                            "x_m": float(current_beam[0, p_idx]),
                            "y_m": float(current_beam[2, p_idx])
                        })
                        current_beam[:, p_idx] = np.nan

        stats = compute_beam_statistics(current_beam)
        turn_survived.append(stats["survived_particles"])
        if stats["centroid"] is not None:
            turn_centroids.append([stats["centroid"]["x_mm"], stats["centroid"]["xp_mrad"]])
        else:
            turn_centroids.append([np.nan, np.nan])
        turn_emittances.append([stats["emittance_x_mrad"], stats["emittance_y_mrad"]])

    final_stats = compute_beam_statistics(current_beam)
    return TrackingResult(
        particles_6d=current_beam,
        n_particles=n_particles,
        survived_particles=int(final_stats["survived_particles"]),
        survival_fraction=float(final_stats["survival_fraction"]),
        centroid=final_stats["centroid"],
        emittance_x_mrad=float(final_stats["emittance_x_mrad"]),
        emittance_y_mrad=float(final_stats["emittance_y_mrad"]),
        centroid_history=np.array(turn_centroids),
        emittance_history=np.array(turn_emittances),
        survival_history=turn_survived,
        loss_log=loss_log,
        metadata={
            "kicker_model": kicker_model,
            "n_turns": n_turns,
            "tracking_mode": "element_resolved"
        }
    )
