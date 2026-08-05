"""
NKM Particle Tracking and Step Integration Module

Provides centered thin-kick, thick symplectic split integration, and genuine RK4 Lorentz-force
tracking utilities for 6D particle distributions through the NKM and storage ring injection region.
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional, Any, Callable, Union, List, Iterator
import numpy as np

from .units import (
    KickMapMetadata,
    compute_rigidity,
    convert_kick_angle,
    integrated_field_to_kick,
    ELECTRON_CHARGE_C
)
from .integrators import SymplecticSplitIntegrator, LorentzRK4Integrator


@dataclass
class TrackingResult:
    """
    Standardized Particle Tracking Result Container.
    
    Unifies tracking output metrics across transfer lines, single kicks, and multi-turn storage ring tracking.
    Supports both attribute access (res.survival_fraction) and dict indexing (res['survival_fraction'])
    for 100% backward compatibility.
    """
    particles_6d: np.ndarray
    n_particles: int
    survived_particles: int
    survival_fraction: float
    centroid: Optional[Dict[str, float]] = None
    emittance_x_mrad: float = 0.0
    emittance_y_mrad: float = 0.0
    centroid_history: Optional[np.ndarray] = None
    emittance_history: Optional[np.ndarray] = None
    survival_history: Optional[List[int]] = None
    loss_log: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_beam(cls,
                  beam: np.ndarray,
                  centroid_history: Optional[np.ndarray] = None,
                  emittance_history: Optional[np.ndarray] = None,
                  survival_history: Optional[List[int]] = None,
                  loss_log: Optional[List[Dict[str, Any]]] = None,
                  metadata: Optional[Dict[str, Any]] = None) -> "TrackingResult":
        """Construct a TrackingResult directly from a 6D beam array and compute beam statistics."""
        from .beam import compute_beam_statistics
        stats = compute_beam_statistics(beam)
        return cls(
            particles_6d=beam,
            n_particles=int(beam.shape[1]),
            survived_particles=int(stats["survived_particles"]),
            survival_fraction=float(stats["survival_fraction"]),
            centroid=stats["centroid"],
            emittance_x_mrad=float(stats["emittance_x_mrad"]),
            emittance_y_mrad=float(stats["emittance_y_mrad"]),
            centroid_history=centroid_history,
            emittance_history=emittance_history,
            survival_history=survival_history,
            loss_log=loss_log or [],
            metadata=metadata or {}
        )

    @property
    def final_beam(self) -> np.ndarray:
        return self.particles_6d

    @property
    def capture_efficiency(self) -> float:
        return self.survival_fraction

    @property
    def final_stats(self) -> Dict[str, Any]:
        return {
            "n_particles": self.n_particles,
            "survived_particles": self.survived_particles,
            "survival_fraction": self.survival_fraction,
            "centroid": self.centroid,
            "emittance_x_mrad": self.emittance_x_mrad,
            "emittance_y_mrad": self.emittance_y_mrad,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert TrackingResult into dictionary format for backward compatibility."""
        d = {
            "particles_6d": self.particles_6d,
            "final_beam": self.particles_6d,
            "n_particles": self.n_particles,
            "survived_particles": self.survived_particles,
            "survival_fraction": self.survival_fraction,
            "capture_efficiency": self.survival_fraction,
            "centroid": self.centroid,
            "emittance_x_mrad": self.emittance_x_mrad,
            "emittance_y_mrad": self.emittance_y_mrad,
            "final_stats": self.final_stats,
            "turn_centroids": self.centroid_history,
            "turn_emittances": self.emittance_history,
            "turn_survived": self.survival_history,
            "loss_log": self.loss_log,
            "metadata": self.metadata,
        }
        d.update(self.metadata)
        return d

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]

    def __contains__(self, key: str) -> bool:
        return key in self.to_dict()

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict().get(key, default)


def track_nkm_thin_kick(beam: np.ndarray,
                        kick_fn: Callable[[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray]],
                        scale_factor: float = 1.0,
                        length_m: float = 0.525,
                        energy_GeV: float = 4.0,
                        metadata: Optional[KickMapMetadata] = None,
                        value_type: Optional[str] = None,
                        value_unit: Optional[str] = None) -> np.ndarray:
    """
    Track a 6D particle beam through a centered thin-lens NKM kick (Drift L/2 -> Thin Kick -> Drift L/2).
    
    Args:
        beam: 6D particle array of shape (6, n_particles)
        kick_fn: Function mapping (x, y) -> (kx, ky)
        scale_factor: Scaling factor for magnetic field strength (1.0 = nominal)
        length_m: NKM length in meters
        energy_GeV: Beam energy in GeV
        metadata: Optional KickMapMetadata object describing kick_fn outputs.
        value_type: Optional value type if metadata not provided ('integrated_field' or 'kick_angle')
        value_unit: Optional value unit if metadata not provided ('T_m', 'T_mm', 'rad', 'mrad')
        
    Returns:
        Tracked 6D particle array after centered thin kick.
    """
    out_beam = beam.copy()
    valid_mask = ~np.isnan(out_beam[0, :])
    if not np.any(valid_mask):
        return out_beam

    half_L = length_m * 0.5

    # 1. Initial drift through L/2
    out_beam[0, valid_mask] += out_beam[1, valid_mask] * half_L
    out_beam[2, valid_mask] += out_beam[3, valid_mask] * half_L

    # 2. Thin Kick at center
    x_pos = out_beam[0, valid_mask]
    y_pos = out_beam[2, valid_mask]
    
    kx_val, ky_val = kick_fn(x_pos, y_pos)
    
    energy_eV = energy_GeV * 1e9
    
    # Resolve metadata without magnitude guessing
    if metadata is None:
        if hasattr(kick_fn, "__self__") and hasattr(kick_fn.__self__, "metadata"):
            metadata = getattr(kick_fn.__self__, "metadata")
        elif value_type is not None and value_unit is not None:
            metadata = KickMapMetadata(
                coordinate_unit="m",
                value_type=value_type,  # type: ignore
                value_unit=value_unit,  # type: ignore
                beam_energy_eV=energy_eV
            )
        else:
            metadata = KickMapMetadata(
                coordinate_unit="m",
                value_type="integrated_field",
                value_unit="T_m",
                beam_energy_eV=energy_eV
            )
            
    if metadata.value_type == "kick_angle":
        delta_xp = convert_kick_angle(kx_val, metadata.value_unit, "rad") * scale_factor
        delta_yp = convert_kick_angle(ky_val, metadata.value_unit, "rad") * scale_factor
    elif metadata.value_type == "integrated_field":
        from .units import convert_integrated_field, integrated_field_to_transverse_kicks
        int_bx = convert_integrated_field(kx_val, metadata.value_unit, "T_m") * scale_factor
        int_by = convert_integrated_field(ky_val, metadata.value_unit, "T_m") * scale_factor
        delta_xp, delta_yp = integrated_field_to_transverse_kicks(
            int_bx_t_m=int_bx,
            int_by_t_m=int_by,
            beam_energy_eV=energy_eV,
            particle_charge_C=metadata.particle_charge_C,
            coordinate_convention=metadata.sign_convention
        )
    else:
        raise ValueError(f"Unsupported value_type in tracking: '{metadata.value_type}'")
        
    out_beam[1, valid_mask] += delta_xp
    out_beam[3, valid_mask] += delta_yp
    
    # 3. Final drift through L/2
    out_beam[0, valid_mask] += out_beam[1, valid_mask] * half_L
    out_beam[2, valid_mask] += out_beam[3, valid_mask] * half_L
    
    return out_beam


def track_nkm_thick_symplectic(beam: np.ndarray,
                               field_fn: Callable[[np.ndarray, np.ndarray, float], Tuple[np.ndarray, np.ndarray]],
                               length_m: float = 0.525,
                               n_slices: int = 40,
                               energy_GeV: float = 4.0,
                               scale_factor: float = 1.0,
                               particle_charge_C: float = ELECTRON_CHARGE_C) -> np.ndarray:
    """
    Thick-element particle tracking using the Symplectic Split-Operator (Drift-Kick-Drift) Integrator.
    
    Primary production tracker (Option A).
    """
    integrator = SymplecticSplitIntegrator(
        field_fn=field_fn,
        length_m=length_m,
        n_slices=n_slices,
        energy_GeV=energy_GeV,
        particle_charge_C=particle_charge_C,
        scale_factor=scale_factor
    )
    return integrator.track(beam)


def track_nkm_thick_rk4(beam: np.ndarray,
                        field_fn: Callable[[np.ndarray, np.ndarray, float], Tuple[np.ndarray, np.ndarray]],
                        length_m: float = 0.525,
                        n_slices: int = 40,
                        energy_GeV: float = 4.0,
                        scale_factor: float = 1.0,
                        particle_charge_C: float = ELECTRON_CHARGE_C) -> np.ndarray:
    """
    Thick-element particle tracking using Genuine 4th-Order Runge-Kutta Lorentz Integration (Option B).
    """
    integrator = LorentzRK4Integrator(
        field_fn=field_fn,
        length_m=length_m,
        n_slices=n_slices,
        energy_GeV=energy_GeV,
        particle_charge_C=particle_charge_C,
        scale_factor=scale_factor
    )
    return integrator.track(beam)


def track_nkm_rk4(beam: np.ndarray,
                  field_fn: Callable[[np.ndarray], np.ndarray],
                  length_m: float = 0.525,
                  n_steps: int = 40,
                  energy_GeV: float = 4.0,
                  scale_factor: float = 1.0,
                  particle_charge_C: float = ELECTRON_CHARGE_C) -> np.ndarray:
    """
    Legacy wrapper for 1D field map tracking. Delegates to SymplecticSplitIntegrator.
    """
    def field_adapter_2d(x, y, z):
        by = field_fn(x)
        bx = np.zeros_like(x)
        return by, bx

    return track_nkm_thick_symplectic(
        beam=beam,
        field_fn=field_adapter_2d,
        length_m=length_m,
        n_slices=n_steps,
        energy_GeV=energy_GeV,
        scale_factor=scale_factor,
        particle_charge_C=particle_charge_C
    )
