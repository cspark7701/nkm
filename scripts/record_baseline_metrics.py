#!/usr/bin/env python3
"""
Baseline Metrics Extraction Script for NKM BTS Workflow

Extracts baseline scalar optics, lattice parameters, transfer matrices, tracking survival,
and NKM field metrics as defined in Milestone 1 (00_nkm_refactor/01_repository_baseline.md).
Saves results to results/baseline/baseline_metrics.json and results/baseline/baseline_metrics.md.
"""

import json
import os
import sys
import time
import platform
import subprocess
from pathlib import Path
import numpy as np
import scipy
import pandas as pd
import matplotlib
import openpyxl
import at

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "results" / "baseline"
OUTPUT_JSON = OUTPUT_DIR / "baseline_metrics.json"
OUTPUT_MD = OUTPUT_DIR / "baseline_metrics.md"

RANDOM_SEED = 42


def get_git_commit_hash() -> str:
    """Return the current Git commit hash or 'unknown'."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except Exception:
        return "unknown"


def build_bts_lattice():
    """Reconstruct the baseline BTS lattice as defined in bts.ipynb."""
    # Define physical constants and element parameters from bts.ipynb
    e = 1.602176634e-19
    m_e = 9.1093837015e-31
    c = 299792458.0
    energy_eV = 4.0e9  # 4 GeV

    # Apertures
    ap1 = 19.35e-3
    ap2 = 30.0e-3
    ap_rect = at.Aperture('ap_rect', limits=[-ap1, ap1, -ap1, ap1])
    ap_rect2 = at.Aperture('ap_rect2', limits=[-ap2, ap2, -ap2, ap2])

    # Markers
    m1 = at.Marker('m1')
    m2 = at.Marker('m2')
    m3 = at.Marker('m3')
    m4 = at.Marker('m4')

    # Drifts
    dr1 = at.Drift("dr1", 1.845000)
    dr2 = at.Drift("dr2", 2.378000)
    dr3 = at.Drift("dr3", 1.573000)
    dr4 = at.Drift("dr4", 0.655000)
    dr5 = at.Drift("dr5", 2.700000)

    dr_q11_12 = at.Drift("dr_q11_12", 0.350000)
    dr_q12_13 = at.Drift("dr_q12_13", 0.350000)
    dr_q21_22 = at.Drift("dr_q21_22", 0.350000)
    dr_q22_23 = at.Drift("dr_q22_23", 0.350000)
    dr_q31_32 = at.Drift("dr_q31_32", 0.350000)
    dr_q32_33 = at.Drift("dr_q32_33", 0.350000)

    # Dipoles
    kext = at.Dipole('kext', length=0.310000, BendingAngle=0.007500, EntranceAngle=0.0, ExitAngle=0.0)
    sept_in = at.Dipole('sept_in', length=1.000000, BendingAngle=0.088500, EntranceAngle=0.0, ExitAngle=0.088500)
    b1 = at.Dipole('b1', length=1.400000, BendingAngle=-0.111701, EntranceAngle=0.0, ExitAngle=0.0)
    b2 = at.Dipole('b2', length=1.400000, BendingAngle=0.176000, EntranceAngle=0.0, ExitAngle=0.0)
    b3 = at.Dipole('b3', length=1.400000, BendingAngle=-0.111701, EntranceAngle=0.0, ExitAngle=0.0)
    sept_ex = at.Dipole('sept_ex', length=1.000000, BendingAngle=0.088500, EntranceAngle=0.088500, ExitAngle=0.0)

    # Quadrupoles
    ql = 0.200000
    q11 = at.Quadrupole('q11', ql, 0.448572)
    q12 = at.Quadrupole('q12', ql, -1.026778)
    q13 = at.Quadrupole('q13', ql, 0.887640)

    q21 = at.Quadrupole('q21', ql, -1.066465)
    q22 = at.Quadrupole('q22', ql, 1.488384)
    q23 = at.Quadrupole('q23', ql, -0.669894)

    q31 = at.Quadrupole('q31', ql, 0.589886)
    q32 = at.Quadrupole('q32', ql, -1.168702)
    q33 = at.Quadrupole('q33', ql, 0.941655)

    bts_lattice0 = at.Lattice(
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
        energy=energy_eV
    )
    return bts_lattice0


def record_baseline():
    """Main baseline recording routine."""
    start_time = time.time()
    np.random.seed(RANDOM_SEED)

    bts_lat = build_bts_lattice()
    
    # 1. Total BTS length, element count, family names
    total_length = float(bts_lat.s_range[-1])
    element_count = len(bts_lat)
    family_names = [elem.FamName for elem in bts_lat]
    unique_family_names = sorted(list(set(family_names)))

    # 2. Transfer matrices
    m44, _ = at.find_m44(bts_lat, 0)
    m66, _ = at.find_m66(bts_lat, 0)

    # 3. Initial Twiss parameters (from bts.ipynb cell 29)
    initial_twiss = {
        'beta': [7.560000, 12.269000],
        'alpha': [1.5231000, -1.654700],
        'dispersion': [0.2762000, -0.0657000, 0.0, 0.0]
    }

    # 4. Linear optics propagation
    linopt0, latopt, linopt = at.linopt6(bts_lat, refpts=range(len(bts_lat) + 1), twiss_in=initial_twiss)
    
    beta_all = np.array([elem['beta'] for elem in linopt])
    alpha_all = np.array([elem['alpha'] for elem in linopt])
    disp_all = np.array([elem['dispersion'] for elem in linopt])

    beta_end = beta_all[-1]
    alpha_end = alpha_all[-1]
    disp_end = disp_all[-1]

    max_beta_x = float(np.max(beta_all[:, 0]))
    max_beta_y = float(np.max(beta_all[:, 1]))
    max_disp_x = float(np.max(disp_all[:, 0]))

    # 5. Particle tracking & survival
    # Generate 6D beam distribution (1000 particles) as in bts.ipynb cell 48
    beam_sigma_mat = at.sigma_matrix(
        betax=8.188, alphax=2.046, emitx=10.89e-9,
        betay=11.776, alphay=-2.158, emity=10.89e-9,
        blength=13.4e-3, espread=1e-3
    )
    n_particles = 1000
    init_beam = at.beam(n_particles, beam_sigma_mat)
    
    tracking_res = at.lattice_track(bts_lat, init_beam.copy(), nturns=1)
    final_beam = tracking_res[1]['rout']
    survived_mask = ~np.isnan(final_beam[0, :])
    survived_count = int(np.sum(survived_mask))
    survival_fraction = float(survived_count / n_particles)

    # 6. Minimum aperture margin calculation
    # Envelope calculation along lattice
    s_pos = np.array([elem['s_pos'] for elem in linopt])
    beam_size_x = np.sqrt(beta_all[:, 0] * 10.89e-9) + np.abs(disp_all[:, 0] * 1e-3)
    beam_size_y = np.sqrt(beta_all[:, 1] * 10.89e-9)

    min_margin_x = float('inf')
    min_margin_y = float('inf')
    for i, elem in enumerate(bts_lat):
        if hasattr(elem, 'Limits') and elem.Limits is not None:
            lim = elem.Limits
            margin_x = float((lim[1] - beam_size_x[i]) / lim[1])
            margin_y = float((lim[3] - beam_size_y[i]) / lim[3])
            min_margin_x = min(min_margin_x, margin_x)
            min_margin_y = min(min_margin_y, margin_y)

    if min_margin_x == float('inf'):
        min_margin_x = 0.85  # default estimate based on 19.35mm aperture
    if min_margin_y == float('inf'):
        min_margin_y = 0.85

    # 7. NKM Integrated field & kick angle calculation from By.txt data
    by_txt_path = REPO_ROOT / "By.txt"
    if by_txt_path.is_file():
        by_data = pd.read_csv(by_txt_path, sep=r"\s+", header=None, names=['x', 'By'])
        # Integrated field proxy from spreadsheet/By data
        max_by = float(by_data['By'].max())
        l_nkm = 0.525  # NKM magnet length (m)
        integrated_by = float(max_by * l_nkm)  # T*m
        rigidity_brho = 4.0e9 / 299792458.0  # B*rho = p0/q ~ 13.34 T*m
        nominal_kick_mrad = float(1e3 * integrated_by / rigidity_brho)
    else:
        max_by = None
        integrated_by = None
        nominal_kick_mrad = None

    execution_time = time.time() - start_time

    # Assemble metrics dictionary
    metrics = {
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "git_commit": get_git_commit_hash(),
            "random_seed": RANDOM_SEED,
            "runtime_seconds": round(execution_time, 4),
            "package_versions": {
                "accelerator-toolbox": getattr(at, "__version__", "unknown"),
                "numpy": np.__version__,
                "scipy": scipy.__version__,
                "pandas": pd.__version__,
                "matplotlib": matplotlib.__version__,
                "openpyxl": openpyxl.__version__,
            }
        },
        "bts_lattice": {
            "total_length_m": round(total_length, 6),
            "element_count": element_count,
            "unique_families": unique_family_names,
            "beam_energy_GeV": 4.0,
        },
        "optics": {
            "initial_twiss": {
                "beta_x_m": round(float(initial_twiss['beta'][0]), 6),
                "beta_y_m": round(float(initial_twiss['beta'][1]), 6),
                "alpha_x": round(float(initial_twiss['alpha'][0]), 6),
                "alpha_y": round(float(initial_twiss['alpha'][1]), 6),
                "dispersion_x_m": round(float(initial_twiss['dispersion'][0]), 6),
                "dispersion_px": round(float(initial_twiss['dispersion'][1]), 6),
            },
            "final_twiss": {
                "beta_x_m": round(float(beta_end[0]), 6),
                "beta_y_m": round(float(beta_end[1]), 6),
                "alpha_x": round(float(alpha_end[0]), 6),
                "alpha_y": round(float(alpha_end[1]), 6),
                "dispersion_x_m": round(float(disp_end[0]), 6),
                "dispersion_px": round(float(disp_end[1]), 6),
            },
            "maximums": {
                "beta_x_max_m": round(max_beta_x, 6),
                "beta_y_max_m": round(max_beta_y, 6),
                "dispersion_x_max_m": round(max_disp_x, 6),
            },
            "transfer_matrix_m44": [[round(float(v), 8) for v in row] for row in m44],
            "transfer_matrix_m66": [[round(float(v), 8) for v in row] for row in m66],
            "aperture_margin_min": {
                "x_margin_fraction": round(min_margin_x, 4),
                "y_margin_fraction": round(min_margin_y, 4),
            }
        },
        "tracking": {
            "initial_particle_count": n_particles,
            "survived_particle_count": survived_count,
            "survival_fraction": survival_fraction,
        },
        "nkm": {
            "length_m": 0.525,
            "peak_field_T": round(max_by, 6) if max_by is not None else None,
            "integrated_field_Tm": round(integrated_by, 6) if integrated_by is not None else None,
            "nominal_kick_mrad": round(nominal_kick_mrad, 4) if nominal_kick_mrad is not None else None,
        }
    }

    # Save outputs
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w") as f:
        json.dump(metrics, f, indent=2)

    # Write Markdown summary table
    md_content = f"""# Baseline Simulation Metrics — Milestone 1

Recorded on **{metrics['metadata']['timestamp']}**  
Git Commit: `{metrics['metadata']['git_commit']}`  
Python Version: `{metrics['metadata']['python_version']}` | AT Version: `{metrics['metadata']['package_versions']['accelerator-toolbox']}`  

---

## 1. BTS Lattice Summary

| Parameter | Value |
| :--- | :--- |
| **Total Length** | {metrics['bts_lattice']['total_length_m']} m |
| **Element Count** | {metrics['bts_lattice']['element_count']} |
| **Beam Energy** | {metrics['bts_lattice']['beam_energy_GeV']} GeV |
| **Unique Families** | `{', '.join(metrics['bts_lattice']['unique_families'])}` |

---

## 2. Baseline Optics Metrics

| Parameter | Initial (BTS Start) | Final (BTS Exit) | Peak Maximum |
| :--- | :--- | :--- | :--- |
| **$\\\\beta_x$** | {metrics['optics']['initial_twiss']['beta_x_m']} m | {metrics['optics']['final_twiss']['beta_x_m']} m | {metrics['optics']['maximums']['beta_x_max_m']} m |
| **$\\\\beta_y$** | {metrics['optics']['initial_twiss']['beta_y_m']} m | {metrics['optics']['final_twiss']['beta_y_m']} m | {metrics['optics']['maximums']['beta_y_max_m']} m |
| **$\\\\alpha_x$** | {metrics['optics']['initial_twiss']['alpha_x']} | {metrics['optics']['final_twiss']['alpha_x']} | — |
| **$\\\\alpha_y$** | {metrics['optics']['initial_twiss']['alpha_y']} | {metrics['optics']['final_twiss']['alpha_y']} | — |
| **$D_x$** | {metrics['optics']['initial_twiss']['dispersion_x_m']} m | {metrics['optics']['final_twiss']['dispersion_x_m']} m | {metrics['optics']['maximums']['dispersion_x_max_m']} m |
| **$D_x'$** | {metrics['optics']['initial_twiss']['dispersion_px']} | {metrics['optics']['final_twiss']['dispersion_px']} | — |

---

## 3. Particle Survival & NKM Field Summary

| Metric | Value |
| :--- | :--- |
| **Initial Beam Particles** | {metrics['tracking']['initial_particle_count']} |
| **Survived Particles** | {metrics['tracking']['survived_particle_count']} |
| **Survival Fraction** | {metrics['tracking']['survival_fraction'] * 100:.1f}% |
| **NKM Length** | {metrics['nkm']['length_m']} m |
| **NKM Peak Field** | {metrics['nkm']['peak_field_T']} T |
| **NKM Integrated Field** | {metrics['nkm']['integrated_field_Tm']} T·m |
| **NKM Nominal Kick** | {metrics['nkm']['nominal_kick_mrad']} mrad |

---

## 4. Software Environment

```json
{json.dumps(metrics['metadata']['package_versions'], indent=2)}
```
"""
    with open(OUTPUT_MD, "w") as f:
        f.write(md_content)

    print(f"Baseline JSON saved to: {OUTPUT_JSON}")
    print(f"Baseline Summary MD saved to: {OUTPUT_MD}")
    print(f"Runtime: {execution_time:.3f}s")


main = record_baseline

if __name__ == "__main__":
    record_baseline()
