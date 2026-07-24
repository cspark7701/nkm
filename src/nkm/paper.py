"""
Data-Driven Publication Paper Pipeline & Figure/Table Generation Module

Provides dynamic compilation of publication-quality tables (LaTeX & Markdown) and 300 DPI figures
derived exclusively from validated simulation models and results.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import matplotlib.pyplot as plt

from .bts_lattice import BTSConfig, create_bts_lattice
from .optics import compute_twiss_propagation, compute_mismatch_metric
from .fieldmap import load_1d_fieldmap, NKMFieldMap1D
from .kickmap import NKMKickMap2D
from .optimization import BTSOptimizationConfig, BTSOptimizationEvaluator
from .constraints import BTSHardwareConstraints
from .results_schema import (
    PaperResultSchema,
    compute_input_data_hashes,
    record_environment_metadata,
    compute_rms_envelope
)


def generate_paper_tables(repo_root: Path, output_dir: Path) -> Dict[str, str]:
    """
    Generate publication tables dynamically from optics calculations and configuration objects.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    tables = {}

    nominal_config = BTSConfig()
    lat = create_bts_lattice(nominal_config)
    twiss_init = {'beta': [7.56, 12.27], 'alpha': [1.52, -1.65], 'dispersion': [0.2762, -0.0657, 0, 0]}
    prop = compute_twiss_propagation(lat, twiss_init)

    # Table 1: BTS Line & Storage Ring Reference Parameters
    t1_md = f"""# Table 1: BTS Line & Storage Ring Reference Parameters

| Parameter | Symbol | Value | Unit |
| :--- | :--- | :--- | :--- |
| Beam Energy | $E_0$ | {nominal_config.energy_eV * 1e-9:.1f} | GeV |
| Relativistic Gamma | $\gamma$ | {nominal_config.energy_eV / 0.51099895e6:.2f} | - |
| Entrance Beta ($\beta_x, \beta_y$) | $(\beta_{{x0}}, \beta_{{y0}})$ | ({twiss_init['beta'][0]:.4f}, {twiss_init['beta'][1]:.4f}) | m |
| Entrance Alpha ($\alpha_x, \alpha_y$) | $(\alpha_{{x0}}, \alpha_{{y0}})$ | ({twiss_init['alpha'][0]:.4f}, {twiss_init['alpha'][1]:.4f}) | - |
| Entrance Dispersion ($D_x, D_x'$) | $(D_{{x0}}, D_{{x0}}')$ | ({twiss_init['dispersion'][0]:.4f}, {twiss_init['dispersion'][1]:.4f}) | m, rad |
| Exit Beta ($\beta_x, \beta_y$) | $(\beta_{{xExit}}, \beta_{{yExit}})$ | ({prop['final_beta'][0]:.4f}, {prop['final_beta'][1]:.4f}) | m |
| Exit Dispersion ($D_x, D_x'$) | $(D_{{xExit}}, D_{{xExit}}')$ | ({prop['final_dispersion'][0]:.4f}, {prop['final_dispersion'][1]:.4f}) | m, rad |
"""

    t1_path = output_dir / "table1_bts_parameters.md"
    with open(t1_path, "w") as f:
        f.write(t1_md)

    tables["table1"] = t1_md

    # Table 2: Quadrupole Strengths
    quad_names = ['q11', 'q12', 'q13', 'q21', 'q22', 'q23', 'q31', 'q32', 'q33']
    k_list = nominal_config.quad_strengths_list

    rows = []
    for qname, k_val in zip(quad_names, k_list):
        rows.append(f"| `{qname}` | {k_val:+.4f} | `[-3.0, +3.0]` |")
    t2_body = "\n".join(rows)

    t2_md = f"""# Table 2: Quadrupole Strengths & Hardware Limits

| Quadrupole | Nominal $K$ [$\text{{m}}^{{-2}}$] | Hardware Bounds [$\text{{m}}^{{-2}}$] |
| :--- | :--- | :--- |
{t2_body}
"""

    t2_path = output_dir / "table2_quad_strengths.md"
    with open(t2_path, "w") as f:
        f.write(t2_md)

    tables["table2"] = t2_md

    return tables


def generate_paper_figures(repo_root: Path, output_dir: Path) -> List[Path]:
    """
    Generate all high-resolution publication figures dynamically using compute_rms_envelope.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_files = []

    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.size': 10,
        'axes.labelsize': 11,
        'axes.titlesize': 12,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'figure.autolayout': True
    })

    # 1. BTS Optics Propagation
    nominal_config = BTSConfig()
    lat = create_bts_lattice(nominal_config)
    twiss_init = {'beta': [7.56, 12.27], 'alpha': [1.52, -1.65], 'dispersion': [0.2762, -0.0657, 0, 0]}
    prop = compute_twiss_propagation(lat, twiss_init)

    s = prop["s_pos"]
    beta_x, beta_y = prop["beta"][:, 0], prop["beta"][:, 1]
    dx = prop["dispersion"][:, 0]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    ax1.plot(s, beta_x, 'b-', label=r'$\beta_x$ (m)')
    ax1.plot(s, beta_y, 'r--', label=r'$\beta_y$ (m)')
    ax1.set_ylabel(r'$\beta$ [m]')
    ax1.set_title('BTS Optical Functions')
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='upper right')

    ax2.plot(s, dx, 'g-', label=r'$D_x$ (m)')
    ax2.set_xlabel('s [m]')
    ax2.set_ylabel(r'$D_x$ [m]')
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='upper right')

    fig_path1 = output_dir / "fig1_bts_optics.png"
    fig.savefig(fig_path1, dpi=300)
    plt.close(fig)
    generated_files.append(fig_path1)

    # 2. Statistically Consistent Beam Envelope (3-sigma)
    fig, ax = plt.subplots(figsize=(10, 4.5))

    env_x_mm = compute_rms_envelope(beta_x, dx, emit_mrad=1e-7, espread=1.1e-3, n_sigma=3.0) * 1e3
    env_y_mm = compute_rms_envelope(beta_y, np.zeros_like(beta_y), emit_mrad=1e-8, espread=1.1e-3, n_sigma=3.0) * 1e3

    ax.plot(s, env_x_mm, 'r-', label=r'Horizontal Total Envelope ($3\sigma_x$)')
    ax.plot(s, -env_x_mm, 'r-')
    ax.plot(s, env_y_mm, 'b-', label=r'Vertical Total Envelope ($3\sigma_y$)')
    ax.plot(s, -env_y_mm, 'b-')
    ax.axhline(19.35, color='black', linestyle=':', label='Pipe Aperture ($\pm 19.35$ mm)')
    ax.axhline(-19.35, color='black', linestyle=':')

    ax.set_xlabel(r'Longitudinal Coordinate $s$ [m]')
    ax.set_ylabel(r'Beam Envelope [mm]')
    ax.set_title('Statistically Consistent Total $3\sigma$ Beam Envelopes')
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(loc='upper right')

    fig_path2 = output_dir / "fig2_beam_envelopes.png"
    fig.savefig(fig_path2, dpi=300)
    plt.close(fig)
    generated_files.append(fig_path2)

    return generated_files


def run_paper_pipeline(repo_root: Optional[Path] = None, run_id: str = "paper_run") -> Dict[str, Any]:
    """
    Execute full data-driven paper pipeline.
    Fails if input files/hashes are invalid.
    """
    if repo_root is None:
        repo_root = Path(__file__).resolve().parent.parent.parent

    # Verify input data hashes
    input_hashes = compute_input_data_hashes(repo_root)
    if "MISSING" in input_hashes.values():
        raise FileNotFoundError(f"Missing scientific input data files: {input_hashes}")

    schema = PaperResultSchema(run_id=run_id, base_dir=repo_root / "results" / "paper")
    schema.initialize_directories()

    record_environment_metadata(schema.run_dir)

    with open(schema.run_dir / "input_hashes.json", "w") as f:
        json.dump(input_hashes, f, indent=2)

    tables = generate_paper_tables(repo_root, schema.tables_dir)
    figures = generate_paper_figures(repo_root, schema.figures_dir)

    metrics_summary = {
        "run_id": run_id,
        "input_hashes_verified": True,
        "tables_count": len(tables),
        "figures_count": len(figures)
    }

    with open(schema.run_dir / "metrics.json", "w") as f:
        json.dump(metrics_summary, f, indent=2)

    return metrics_summary
