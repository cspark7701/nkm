"""
Unit and integration tests for fully data-driven paper pipeline (Task 08)
"""

import sys
from pathlib import Path
import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.nkm.results_schema import (
    PaperResultSchema,
    compute_file_hash,
    compute_input_data_hashes,
    compute_rms_envelope
)
from src.nkm.paper import (
    run_paper_pipeline,
    set_publication_style,
    PUBLICATION_COLORS
)


def test_input_data_hashes():
    hashes = compute_input_data_hashes(REPO_ROOT)

    assert "By.txt" in hashes
    assert "kickmap_file.txt" in hashes
    assert "K4GSR_HBIv4-1.mat" in hashes
    assert len(hashes["By.txt"]) == 64  # SHA-256 hex string length


def test_rms_envelope_formula():
    beta_m = np.array([10.0, 20.0])
    disp_m = np.array([0.1, 0.2])
    emit_mrad = 1e-7
    espread = 1.1e-3

    env_3sig = compute_rms_envelope(beta_m, disp_m, emit_mrad=emit_mrad, espread=espread, n_sigma=3.0)

    # Expected rms: sqrt( 1e-7 * 10 + (0.1 * 1.1e-3)^2 ) = sqrt( 1e-6 + 1.21e-8 ) = sqrt(1.0121e-6)
    expected_rms_0 = np.sqrt(emit_mrad * 10.0 + (0.1 * espread)**2)
    assert env_3sig[0] == pytest.approx(3.0 * expected_rms_0, rel=1e-6)


def test_paper_pipeline_execution(tmp_path):
    schema = PaperResultSchema(run_id="test_run", base_dir=tmp_path)
    schema.initialize_directories()

    assert schema.figures_dir.is_dir()
    assert schema.tables_dir.is_dir()

    summary = run_paper_pipeline(repo_root=REPO_ROOT, run_id="test_run_pipeline")
    assert summary["input_hashes_verified"] is True
    assert summary["tables_count"] >= 2
    assert summary["figures_count"] >= 2


def test_set_publication_style():
    """Verify set_publication_style configures matplotlib rc_params and color palette."""
    params = set_publication_style(font_size=11, dpi=300)
    assert params["font.size"] == 11
    assert params["figure.dpi"] == 300

    assert "beta_x" in PUBLICATION_COLORS
    assert "beta_y" in PUBLICATION_COLORS
    assert "dispersion" in PUBLICATION_COLORS

