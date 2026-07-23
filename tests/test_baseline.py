import json
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.inventory_protected_hashes import verify_hash_manifest, OUTPUT_MANIFEST
from scripts.record_baseline_metrics import OUTPUT_JSON


@pytest.fixture
def baseline_metrics():
    """Load baseline metrics JSON file."""
    assert OUTPUT_JSON.is_file(), f"Baseline metrics JSON missing at {OUTPUT_JSON}"
    with open(OUTPUT_JSON, "r") as f:
        return json.load(f)


def test_protected_files_manifest():
    """Verify that all protected files remain unchanged and match their SHA256 manifest."""
    assert OUTPUT_MANIFEST.is_file(), "Protected file manifest missing!"
    assert verify_hash_manifest(OUTPUT_MANIFEST), "Protected file hash verification failed!"


def test_baseline_lattice_parameters(baseline_metrics):
    """Verify core BTS lattice baseline parameters."""
    bts = baseline_metrics["bts_lattice"]
    assert pytest.approx(bts["total_length_m"], abs=1e-3) == 21.789
    assert bts["element_count"] == 36
    assert bts["beam_energy_GeV"] == 4.0
    assert "sept_in" in bts["unique_families"]
    assert "sept_ex" in bts["unique_families"]


def test_baseline_optics_parameters(baseline_metrics):
    """Verify linear optics and maximum beta values."""
    optics = baseline_metrics["optics"]
    initial = optics["initial_twiss"]
    final = optics["final_twiss"]
    maxima = optics["maximums"]

    # Initial Twiss
    assert pytest.approx(initial["beta_x_m"], abs=1e-4) == 7.560
    assert pytest.approx(initial["beta_y_m"], abs=1e-4) == 12.269
    assert pytest.approx(initial["alpha_x"], abs=1e-4) == 1.5231
    assert pytest.approx(initial["alpha_y"], abs=1e-4) == -1.6547

    # Final optics
    assert pytest.approx(final["beta_x_m"], abs=1e-2) == 44.98
    assert pytest.approx(final["beta_y_m"], abs=1e-1) == 242.61

    # Maximums
    assert maxima["beta_x_max_m"] <= 60.0
    assert maxima["beta_y_max_m"] > 200.0


def test_baseline_tracking_survival(baseline_metrics):
    """Verify baseline beam tracking survival."""
    tracking = baseline_metrics["tracking"]
    assert tracking["initial_particle_count"] == 1000
    assert tracking["survived_particle_count"] == 1000
    assert pytest.approx(tracking["survival_fraction"]) == 1.0


def test_nkm_field_and_kick(baseline_metrics):
    """Verify NKM integrated field and nominal kick angle."""
    nkm = baseline_metrics["nkm"]
    assert nkm["length_m"] == 0.525
    assert pytest.approx(nkm["peak_field_T"], abs=1e-3) == 0.146
    assert pytest.approx(nkm["nominal_kick_mrad"], abs=1e-2) == 5.75
