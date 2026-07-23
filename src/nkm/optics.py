"""
BTS Linear Optics and Mismatch Analysis Module

Provides functions for uncoupled Twiss propagation, phase advances, dispersion,
beam covariance matrix calculations, and plane-by-plane phase-space mismatch metrics.
"""

from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import at


def beam_sigma_matrix_2d(beta: float, alpha: float, emit: float = 1.0) -> np.ndarray:
    """
    Construct a 2x2 beam covariance matrix Sigma in phase space (u, u').
    
    Sigma = emit * [[beta, -alpha], [-alpha, (1 + alpha^2) / beta]]
    """
    gamma = (1.0 + alpha**2) / beta
    return emit * np.array([
        [beta, -alpha],
        [-alpha, gamma]
    ])


def compute_mismatch_metric(beta_out: float, alpha_out: float,
                            beta_target: float, alpha_target: float) -> float:
    """
    Calculate the plane-by-plane phase space mismatch metric M_u:
    
        M_u = 0.5 * Tr(Sigma_{target}^-1 * Sigma_{out}) - 1
        
    Args:
        beta_out: Output beta function (m)
        alpha_out: Output alpha parameter
        beta_target: Target beta function (m)
        alpha_target: Target alpha parameter
        
    Returns:
        Mismatch value M_u >= 0. Exactly 0 when output matches target.
    """
    sigma_target = beam_sigma_matrix_2d(beta_target, alpha_target, emit=1.0)
    sigma_out = beam_sigma_matrix_2d(beta_out, alpha_out, emit=1.0)
    
    sigma_target_inv = np.linalg.inv(sigma_target)
    tr = np.trace(sigma_target_inv @ sigma_out)
    return float(0.5 * tr - 1.0)


def compute_twiss_propagation(lattice: at.Lattice, initial_twiss: Dict[str, Any]) -> Dict[str, Any]:
    """
    Propagate linear optics through the lattice given initial Twiss parameters.
    
    Args:
        lattice: at.Lattice instance
        initial_twiss: dict with keys 'beta', 'alpha', 'dispersion'
        
    Returns:
        Dictionary containing arrays of s_pos, beta, alpha, dispersion, mu, and final Twiss values.
    """
    linopt0, latopt, linopt = at.linopt6(lattice, refpts=range(len(lattice) + 1), twiss_in=initial_twiss)
    
    s_pos = np.array([elem['s_pos'] for elem in linopt])
    beta_all = np.array([elem['beta'] for elem in linopt])
    alpha_all = np.array([elem['alpha'] for elem in linopt])
    disp_all = np.array([elem['dispersion'] for elem in linopt])
    mu_all = np.array(linopt['mu']) if 'mu' in linopt.dtype.names else np.zeros_like(beta_all)

    return {
        "s_pos": s_pos,
        "beta": beta_all,
        "alpha": alpha_all,
        "dispersion": disp_all,
        "mu": mu_all,
        "final_beta": beta_all[-1],
        "final_alpha": alpha_all[-1],
        "final_dispersion": disp_all[-1],
        "max_beta_x": float(np.max(beta_all[:, 0])),
        "max_beta_y": float(np.max(beta_all[:, 1])),
        "max_dispersion_x": float(np.max(disp_all[:, 0])),
    }


def compute_bts_optics_metrics(lattice: at.Lattice,
                               initial_twiss: Dict[str, Any],
                               target_twiss: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute optics propagation and evaluate mismatch metrics relative to target parameters.
    """
    prop = compute_twiss_propagation(lattice, initial_twiss)
    
    beta_end = prop["final_beta"]
    alpha_end = prop["final_alpha"]
    disp_end = prop["final_dispersion"]
    
    target_beta = target_twiss["beta"]
    target_alpha = target_twiss["alpha"]
    target_disp = target_twiss["dispersion"]
    
    mismatch_x = compute_mismatch_metric(beta_end[0], alpha_end[0], target_beta[0], target_alpha[0])
    mismatch_y = compute_mismatch_metric(beta_end[1], alpha_end[1], target_beta[1], target_alpha[1])
    
    disp_residual_x = float(disp_end[0] - target_disp[0])
    disp_px_residual_x = float(disp_end[1] - target_disp[1])
    
    return {
        "propagation": prop,
        "mismatch_x": mismatch_x,
        "mismatch_y": mismatch_y,
        "dispersion_x_residual_m": disp_residual_x,
        "dispersion_px_residual": disp_px_residual_x,
        "final_beta_x": float(beta_end[0]),
        "final_beta_y": float(beta_end[1]),
        "target_beta_x": float(target_beta[0]),
        "target_beta_y": float(target_beta[1]),
    }


def plot_bts_optics(lattice: at.Lattice,
                    initial_twiss: Dict[str, Any],
                    output_path: Optional[Path] = None) -> plt.Figure:
    """
    Generate publication-quality plots of BTS beta functions, dispersion, and phase advances.
    """
    prop = compute_twiss_propagation(lattice, initial_twiss)
    s = prop["s_pos"]
    beta_x, beta_y = prop["beta"][:, 0], prop["beta"][:, 1]
    dx = prop["dispersion"][:, 0]
    mu_x, mu_y = prop["mu"][:, 0], prop["mu"][:, 1]
    
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    
    # 1. Beta functions
    ax1.plot(s, beta_x, 'b-', label=r'$\beta_x$ (m)')
    ax1.plot(s, beta_y, 'r--', label=r'$\beta_y$ (m)')
    ax1.set_ylabel(r'$\beta$ [m]')
    ax1.set_title('BTS Optical Functions')
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='upper right')
    
    # 2. Dispersion
    ax2.plot(s, dx, 'g-', label=r'$D_x$ (m)')
    ax2.set_ylabel(r'$D_x$ [m]')
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='upper right')
    
    # 3. Phase advance
    ax3.plot(s, mu_x, 'b-', label=r'$\mu_x$ (rad)')
    ax3.plot(s, mu_y, 'r--', label=r'$\mu_y$ (rad)')
    ax3.set_xlabel('s [m]')
    ax3.set_ylabel(r'$\mu$ [rad]')
    ax3.grid(True, linestyle=':', alpha=0.6)
    ax3.legend(loc='upper right')
    
    plt.tight_layout()
    
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=300)
        
    return fig
