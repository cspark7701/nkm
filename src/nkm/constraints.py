"""
NKM BTS Hardware and Physical Optics Constraints Module

Defines element-specific hardware bounds, pole-tip field limits, beam envelope margins,
and physical feasibility validators for the Booster-to-Storage Ring (BTS) transfer line.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np

from .units import compute_rigidity, ELECTRON_CHARGE_C
from .bts_lattice import BTSConfig, create_bts_lattice
from .optics import compute_twiss_propagation


@dataclass
class QuadrupoleHardwareBounds:
    """Hardware limits for a specific quadrupole family or individual magnet."""
    name: str
    k_min: float = -3.0     # Minimum normalized strength K [m^-2]
    k_max: float = 3.0      # Maximum normalized strength K [m^-2]
    r_bore_m: float = 0.01935  # Bore radius in meters (19.35 mm)
    b_pole_max_T: float = 1.2  # Maximum pole-tip field limit in Tesla


@dataclass
class BTSConstraintConfig:
    """Configuration for physical hardware and beam envelope constraints."""
    energy_eV: float = 4.0e9
    beta_max_limit_m: float = 60.0       # Maximum peak beta function limit
    disp_max_limit_m: float = 1.5        # Maximum dispersion magnitude limit
    aperture_margin_m: float = 0.002     # Clearance margin inside beam pipe (2 mm)
    emit_x_mrad: float = 1.0e-7          # Design horizontal beam emittance
    emit_y_mrad: float = 1.0e-8          # Design vertical beam emittance
    energy_spread: float = 1.1e-3        # Design energy spread delta
    b_pole_limit_T: float = 1.2          # Maximum allowable pole-tip field across all quads

    # Individual quadrupole bounds (q11..q33)
    quad_bounds: Dict[str, QuadrupoleHardwareBounds] = field(default_factory=lambda: {
        "q11": QuadrupoleHardwareBounds("q11", k_min=-3.0, k_max=3.0),
        "q12": QuadrupoleHardwareBounds("q12", k_min=-3.0, k_max=3.0),
        "q13": QuadrupoleHardwareBounds("q13", k_min=-3.0, k_max=3.0),
        "q21": QuadrupoleHardwareBounds("q21", k_min=-3.0, k_max=3.0),
        "q22": QuadrupoleHardwareBounds("q22", k_min=-3.0, k_max=3.0),
        "q23": QuadrupoleHardwareBounds("q23", k_min=-3.0, k_max=3.0),
        "q31": QuadrupoleHardwareBounds("q31", k_min=-3.0, k_max=3.0),
        "q32": QuadrupoleHardwareBounds("q32", k_min=-3.0, k_max=3.0),
        "q33": QuadrupoleHardwareBounds("q33", k_min=-3.0, k_max=3.0),
    })


class BTSHardwareConstraints:
    """
    Evaluates hardware limits (K bounds, pole-tip fields) and physical optics constraints
    (peak beta, dispersion, beam envelope) for a set of BTS quadrupole strengths.
    """
    def __init__(self, config: Optional[BTSConstraintConfig] = None):
        self.config = config or BTSConstraintConfig()
        self.brho = compute_rigidity(self.config.energy_eV, ELECTRON_CHARGE_C)
        self.quad_names = ['q11', 'q12', 'q13', 'q21', 'q22', 'q23', 'q31', 'q32', 'q33']

    def check_quad_hardware_limits(self, strengths: np.ndarray) -> Dict[str, Any]:
        """
        Check strength bounds and pole-tip fields for each quadrupole.
        """
        violations = []
        pole_fields = {}
        k_map = dict(zip(self.quad_names, strengths))

        for qname in self.quad_names:
            k_val = k_map[qname]
            bounds = self.config.quad_bounds[qname]

            if not (bounds.k_min <= k_val <= bounds.k_max):
                violations.append(f"Quad {qname} strength K={k_val:.4f} outside [{bounds.k_min}, {bounds.k_max}]")

            # Pole-tip field B_pole = |K| * B_rho * r_bore
            b_pole = abs(k_val) * self.brho * bounds.r_bore_m
            pole_fields[qname] = float(b_pole)

            if b_pole > bounds.b_pole_max_T:
                violations.append(f"Quad {qname} pole-tip field B_pole={b_pole:.3f}T exceeds {bounds.b_pole_max_T}T limit")

        is_ok = len(violations) == 0
        return {
            "feasible": is_ok,
            "violations": violations,
            "pole_fields_T": pole_fields,
            "max_pole_field_T": float(max(pole_fields.values())) if pole_fields else 0.0
        }

    def check_optics_constraints(self, prop_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check peak beta and dispersion limits along the BTS line.
        """
        violations = []
        max_beta_x = prop_results.get("max_beta_x", 0.0)
        max_beta_y = prop_results.get("max_beta_y", 0.0)

        if max_beta_x > self.config.beta_max_limit_m:
            violations.append(f"Peak beta_x = {max_beta_x:.2f}m exceeds limit {self.config.beta_max_limit_m}m")

        if max_beta_y > self.config.beta_max_limit_m:
            violations.append(f"Peak beta_y = {max_beta_y:.2f}m exceeds limit {self.config.beta_max_limit_m}m")

        is_ok = len(violations) == 0
        return {
            "feasible": is_ok,
            "violations": violations,
            "max_beta_x": float(max_beta_x),
            "max_beta_y": float(max_beta_y)
        }

    def validate_full(self, strengths: np.ndarray, prop_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combined hardware and optics constraint validation.
        """
        hw = self.check_quad_hardware_limits(strengths)
        opt = self.check_optics_constraints(prop_results)

        all_violations = hw["violations"] + opt["violations"]
        all_passed = hw["feasible"] and opt["feasible"]

        return {
            "feasible": all_passed,
            "violations": all_violations,
            "hardware": hw,
            "optics": opt
        }
