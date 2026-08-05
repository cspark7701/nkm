"""
Unit Tests for Task 04 — Element-Resolved Aperture and Septum Losses
"""

import sys
from pathlib import Path
import numpy as np
import pytest
import at

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.nkm.beam import generate_6d_beam
from src.nkm.storage_ring_injection import (
    SeptumModel,
    ElementAperture,
    track_element_resolved_injection,
    StorageRingInjectionConfig
)


def test_septum_model_collision_logic():
    """Test physical septum wall collision bounds."""
    septum = SeptumModel(x_septum_m=-0.016, thickness_m=0.002, allowed_side="stored")

    assert septum.x_outer_m == pytest.approx(-0.018, abs=1e-6)

    # Particle positions: x = -10mm (safe stored), -17mm (inside wall), -25mm (invalid stored side)
    x_test = np.array([-0.010, -0.017, -0.025])
    collisions = septum.check_collision(x_test)

    assert collisions[0] == False  # -10 mm is safe inside stored region (x > -16mm)
    assert collisions[1] == True   # -17 mm is inside septum wall [-18mm, -16mm]
    assert collisions[2] == True   # -25 mm is past septum wall on stored side


def test_element_aperture_bounds():
    """Test element-resolved physical aperture boundary checks."""
    ap = ElementAperture(x_min=-0.030, x_max=+0.030, y_min=-0.015, y_max=+0.015)

    x_pts = np.array([0.000, 0.035, -0.040])
    y_pts = np.array([0.000, 0.005, 0.020])

    loss_xmin, loss_xmax, loss_ymin, loss_ymax = ap.check_loss(x_pts, y_pts)

    assert loss_xmin[2] == True
    assert loss_xmax[1] == True
    assert loss_ymax[2] == True
    assert loss_xmin[0] == False and loss_xmax[0] == False


def test_track_element_resolved_injection_loss_logging():
    """Test element-resolved tracking and exact loss logging on a test lattice."""
    d1 = at.Drift("DR_01", 1.0)
    q1 = at.Quadrupole("QF_01", 0.5, 0.2)
    d2 = at.Drift("DR_02", 1.0)  # Element index 2
    d3 = at.Drift("DR_03", 1.0)

    ring = at.Lattice([d1, q1, d2, d3], energy=4.0e9)

    beam = generate_6d_beam(n_particles=50, beta_x=7.56, alpha_x=0.0, emit_x=1e-7, beta_y=12.27, alpha_y=-1.65, emit_y=1e-9, seed=42)

    wide_ap = ElementAperture(x_min=-0.10, x_max=+0.10)
    tight_ap = ElementAperture(x_min=-0.0005, x_max=+0.0005)

    ap_map = {0: wide_ap, 1: wide_ap, 2: tight_ap, 3: wide_ap}

    res = track_element_resolved_injection(
        beam, ring, n_turns=1, kicker_model="off",
        element_apertures=ap_map
    )

    assert len(res.loss_log) > 0
    first_loss = res.loss_log[0]
    assert first_loss["element_index"] == 2
    assert first_loss["element_name"] == "DR_02"
    assert first_loss["turn"] == 1
    assert "aperture" in first_loss["cause"]
