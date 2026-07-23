"""
BTS Lattice Construction and Validation Module

Provides typed configuration objects, lattice constructors, and lattice verification functions
for the Booster-to-Storage Ring (BTS) transfer line.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import at


@dataclass
class BTSConfig:
    """Configuration data structure for the BTS transfer line."""
    energy_eV: float = 4.0e9  # Beam energy in eV (4.0 GeV)
    
    # Magnet lengths (m)
    l_kext: float = 0.310000
    l_sept_in: float = 1.000000
    l_b1: float = 1.400000
    l_b2: float = 1.400000
    l_b3: float = 1.400000
    l_sept_ex: float = 1.000000
    l_quad: float = 0.200000
    
    # Bending angles (rad)
    ang_kext: float = 0.007500
    ang_sept_in: float = 0.088500
    ang_b1: float = -0.111701
    ang_b2: float = 0.176000
    ang_b3: float = -0.111701
    ang_sept_ex: float = 0.088500
    
    # Edge angles (rad)
    e1_kext: float = 0.0
    e2_kext: float = 0.0
    e1_sept_in: float = 0.0
    e2_sept_in: float = 0.088500
    e1_b1: float = 0.0
    e2_b1: float = 0.0
    e1_b2: float = 0.0
    e2_b2: float = 0.0
    e1_b3: float = 0.0
    e2_b3: float = 0.0
    e1_sept_ex: float = 0.088500
    e2_sept_ex: float = 0.0
    
    # Quadrupole strengths K = B' / (B*rho) [m^-2]
    k_q11: float = 0.448572
    k_q12: float = -1.026778
    k_q13: float = 0.887640
    
    k_q21: float = -1.066465
    k_q22: float = 1.488384
    k_q23: float = -0.669894
    
    k_q31: float = 0.589886
    k_q32: float = -1.168702
    k_q33: float = 0.941655
    
    # Apertures (m)
    ap1_limit: float = 19.35e-3
    ap2_limit: float = 30.0e-3
    
    # Drift lengths (m)
    l_dr1: float = 1.845000
    l_dr2: float = 2.378000
    l_dr3: float = 1.573000
    l_dr4: float = 0.655000
    l_dr5: float = 2.700000
    
    l_dr_q11_12: float = 0.350000
    l_dr_q12_13: float = 0.350000
    l_dr_q21_22: float = 0.350000
    l_dr_q22_23: float = 0.350000
    l_dr_q31_32: float = 0.350000
    l_dr_q32_33: float = 0.350000

    @property
    def total_bending_angle(self) -> float:
        """Sum of all dipole bending angles in radians."""
        return (self.ang_kext + self.ang_sept_in + self.ang_b1 + 
                self.ang_b2 + self.ang_b3 + self.ang_sept_ex)

    @property
    def quad_strengths_list(self) -> List[float]:
        """List of 9 quadrupole strengths in order q11 to q33."""
        return [self.k_q11, self.k_q12, self.k_q13,
                self.k_q21, self.k_q22, self.k_q23,
                self.k_q31, self.k_q32, self.k_q33]


def create_bts_lattice(config: Optional[BTSConfig] = None) -> at.Lattice:
    """
    Construct and return the Accelerator Toolbox (AT) BTS lattice model.
    
    Args:
        config: BTSConfig object. If None, default configuration is used.
        
    Returns:
        at.Lattice instance for the BTS line.
    """
    if config is None:
        config = BTSConfig()
        
    # Apertures
    ap_rect = at.Aperture('ap_rect', limits=[-config.ap1_limit, config.ap1_limit, -config.ap1_limit, config.ap1_limit])
    ap_rect2 = at.Aperture('ap_rect2', limits=[-config.ap2_limit, config.ap2_limit, -config.ap2_limit, config.ap2_limit])
    
    # Markers
    m1 = at.Marker('m1')
    m2 = at.Marker('m2')
    m3 = at.Marker('m3')
    m4 = at.Marker('m4')

    # Drifts
    dr1 = at.Drift("dr1", config.l_dr1)
    dr2 = at.Drift("dr2", config.l_dr2)
    dr3 = at.Drift("dr3", config.l_dr3)
    dr4 = at.Drift("dr4", config.l_dr4)
    dr5 = at.Drift("dr5", config.l_dr5)

    dr_q11_12 = at.Drift("dr_q11_12", config.l_dr_q11_12)
    dr_q12_13 = at.Drift("dr_q12_13", config.l_dr_q12_13)
    dr_q21_22 = at.Drift("dr_q21_22", config.l_dr_q21_22)
    dr_q22_23 = at.Drift("dr_q22_23", config.l_dr_q22_23)
    dr_q31_32 = at.Drift("dr_q31_32", config.l_dr_q31_32)
    dr_q32_33 = at.Drift("dr_q32_33", config.l_dr_q32_33)

    # Dipoles
    kext = at.Dipole('kext', length=config.l_kext, BendingAngle=config.ang_kext, EntranceAngle=config.e1_kext, ExitAngle=config.e2_kext)
    sept_in = at.Dipole('sept_in', length=config.l_sept_in, BendingAngle=config.ang_sept_in, EntranceAngle=config.e1_sept_in, ExitAngle=config.e2_sept_in)
    b1 = at.Dipole('b1', length=config.l_b1, BendingAngle=config.ang_b1, EntranceAngle=config.e1_b1, ExitAngle=config.e2_b1)
    b2 = at.Dipole('b2', length=config.l_b2, BendingAngle=config.ang_b2, EntranceAngle=config.e1_b2, ExitAngle=config.e2_b2)
    b3 = at.Dipole('b3', length=config.l_b3, BendingAngle=config.ang_b3, EntranceAngle=config.e1_b3, ExitAngle=config.e2_b3)
    sept_ex = at.Dipole('sept_ex', length=config.l_sept_ex, BendingAngle=config.ang_sept_ex, EntranceAngle=config.e1_sept_ex, ExitAngle=config.e2_sept_ex)

    # Quadrupoles
    q11 = at.Quadrupole('q11', config.l_quad, config.k_q11)
    q12 = at.Quadrupole('q12', config.l_quad, config.k_q12)
    q13 = at.Quadrupole('q13', config.l_quad, config.k_q13)

    q21 = at.Quadrupole('q21', config.l_quad, config.k_q21)
    q22 = at.Quadrupole('q22', config.l_quad, config.k_q22)
    q23 = at.Quadrupole('q23', config.l_quad, config.k_q23)

    q31 = at.Quadrupole('q31', config.l_quad, config.k_q31)
    q32 = at.Quadrupole('q32', config.l_quad, config.k_q32)
    q33 = at.Quadrupole('q33', config.l_quad, config.k_q33)

    lattice = at.Lattice(
        [
            m1, ap_rect, kext, sept_in, dr1,
            q11, dr_q11_12, q12, dr_q12_13, q13, dr2,
            m2, ap_rect2, b1, dr3,
            q21, dr_q21_22, q22, dr_q22_23, q23, dr4,
            m3, ap_rect2, b2, dr4,
            q31, dr_q31_32, q32, dr_q32_33, q33, dr3,
            b3, dr5, sept_ex, ap_rect, m4
        ],
        name='BTS',
        energy=config.energy_eV
    )
    return lattice


def check_symplecticity(matrix: np.ndarray) -> float:
    """
    Compute the symplecticity error of a transfer matrix M.
    
    For a 2n x 2n matrix M, symplecticity requires M^T J M = J,
    where J is the canonical symplectic block matrix.
    
    Returns:
        Max absolute difference norm || M^T J M - J ||_inf.
    """
    dim = matrix.shape[0]
    if dim not in (4, 6):
        raise ValueError(f"Symplecticity check requires 4x4 or 6x6 matrix, got {dim}x{dim}")
        
    n = dim // 2
    J_block = np.array([[0, 1], [-1, 0]])
    J = np.block([[J_block if i == j else np.zeros((2, 2)) for j in range(n)] for i in range(n)])
    
    res = matrix.T @ J @ matrix - J
    return float(np.max(np.abs(res)))


def validate_bts_lattice(lattice: at.Lattice) -> Dict[str, Any]:
    """
    Perform comprehensive validation checks on the BTS lattice.
    
    Checks:
    - Total length and element count
    - Total bend angle sum
    - Transfer matrix finiteness
    - Transfer matrix symplecticity
    - Aperture bounds positivity
    
    Returns:
        Dictionary of validation results and boolean status flags.
    """
    total_length = float(lattice.s_range[-1])
    element_count = len(lattice)
    
    # Bend angle sum
    total_bend = 0.0
    for elem in lattice:
        if hasattr(elem, 'BendingAngle'):
            total_bend += elem.BendingAngle
            
    # Transfer matrix
    m44, _ = at.find_m44(lattice, 0)
    m66, _ = at.find_m66(lattice, 0)
    
    is_m44_finite = bool(np.all(np.isfinite(m44)))
    is_m66_finite = bool(np.all(np.isfinite(m66)))
    
    symp_error_m44 = check_symplecticity(m44)
    symp_error_m66 = check_symplecticity(m66)
    
    is_symplectic_44 = symp_error_m44 < 1e-10
    is_symplectic_66 = symp_error_m66 < 1e-10
    
    # Aperture check
    aperture_valid = True
    for elem in lattice:
        if hasattr(elem, 'Limits') and elem.Limits is not None:
            if any(lim <= 0 for lim in elem.Limits[1::2]):
                aperture_valid = False
                
    all_passed = (
        is_m44_finite and
        is_m66_finite and
        is_symplectic_44 and
        aperture_valid and
        total_length > 0
    )
    
    return {
        "all_checks_passed": all_passed,
        "total_length_m": total_length,
        "element_count": element_count,
        "total_bend_angle_rad": float(total_bend),
        "total_bend_angle_deg": float(np.degrees(total_bend)),
        "is_m44_finite": is_m44_finite,
        "is_m66_finite": is_m66_finite,
        "symplecticity_error_m44": symp_error_m44,
        "symplecticity_error_m66": symp_error_m66,
        "is_symplectic_m44": is_symplectic_44,
        "is_symplectic_m66": is_symplectic_66,
        "apertures_valid": aperture_valid,
    }
