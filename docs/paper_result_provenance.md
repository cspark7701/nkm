# Fully Data-Driven Paper Pipeline & Result Provenance Report

## 1. Executive Summary

This document specifies the data provenance architecture, cryptographic verification, and single-command reproduction pipeline for all figures, tables, and numerical metrics presented in the journal manuscript. All hard-coded scientific numbers and unverified manual values have been eliminated.

---

## 2. Result Schema Directory Layout

Simulation outputs and publication deliverables follow the standardized schema layout (`src/nkm/results_schema.py`):

```text
results/paper/<run-id>/
├── config.yaml
├── metrics.json
├── lattice_parameters.csv
├── fieldmap_validation.json
├── optimization_history.csv
├── injection_summary.json
├── monte_carlo_summary.json
├── figures/
│   ├── fig1_bts_optics.png
│   └── fig2_beam_envelopes.png
├── tables/
│   ├── table1_bts_parameters.md
│   └── table2_quad_strengths.md
├── environment.txt
├── git_commit.txt
└── input_hashes.json
```

---

## 3. Cryptographic Input File Hashes

To prevent silent data corruption or unverified input modifications, every execution verifies the SHA-256 hashes of authoritative scientific input files:

- `By.txt`: SHA-256 calculated on run
- `kickmap_file.txt`: SHA-256 calculated on run
- `K4GSR_HBIv4-1.mat`: SHA-256 calculated on run
- `storage_ring_lattice_nkm.mat`: SHA-256 calculated on run

If any input file is missing or corrupted, the paper pipeline terminates immediately with an explicit error.

---

## 4. Statistically Consistent RMS Beam Envelope Formula

Transverse beam envelopes are computed using the statistically consistent total RMS envelope equation:

$$\sigma_x(s) = \sqrt{\epsilon_x \beta_x(s) + \left[ D_x(s) \cdot \sigma_\delta \right]^2}$$

Total $n\sigma$ physical boundary:

$$\text{Envelope}_x(s) = n_{\sigma} \cdot \sigma_x(s)$$

where $n_{\sigma} = 3.0$, design horizontal emittance $\epsilon_x = 0.1\ \mu\text{m}\cdot\text{rad}$, and energy spread $\sigma_\delta = 1.1 \times 10^{-3}$.

---

## 5. Single-Command Paper Reproduction

All publication figures and tables are regenerated using a single command:

```bash
python3 scripts/reproduce_paper.py
```

Execution outputs verified figures, tables, JSON metrics summaries, and environment/git commit logs under `results/paper/paper_run_<timestamp>/`.
