# NKM Project Milestone Summaries & Executive Execution Plans

This directory (`docs/exec-plans/completed/`) contains the complete, ordered record of all 8 refactoring and simulation milestones achieved in the NKM (Nonlinear Kicker Magnet) Booster-to-Storage Ring (BTS) project.

> **Project Policy**: From this point forward, all newly completed milestones, tasks, or execution plan documentation must be recorded and archived in this directory (`docs/exec-plans/completed/`).

---

## Completed Milestones Index (In Order)

1. [**Milestone 01 — Baseline Repository Safeguards & Inventory**](file:///home/cspark/Work/projects/nkm/docs/exec-plans/completed/01_baseline_repository_inventory.md)
   - Established protected input scientific data SHA256 manifest, internal physics unit conventions, and unoptimized reference baseline optics/field metrics.

2. [**Milestone 02 — BTS Lattice Construction & Optics Propagation Validation**](file:///home/cspark/Work/projects/nkm/docs/exec-plans/completed/02_bts_optics_validation.md)
   - Implemented modular pyAT BTS lattice constructor (`src/nkm/lattice.py`), linear transfer matrix propagation, symplecticity verification ($\max |M^T J M - J| < 10^{-14}$), and uncoupled 2D phase-space mismatch metric formulation ($\mathcal{M}_u$).

3. [**Milestone 03 — RADIA Magnetic Field Map Ingestion & Validation**](file:///home/cspark/Work/projects/nkm/docs/exec-plans/completed/03_nkm_fieldmap_ingestion.md)
   - Created 1D/2D field map evaluators (`NKMFieldMap1D`, `NKMKickMap2D`), enforced strict domain bounds with zero silent extrapolation, verified odd symmetry in $x$ ($\text{residual} < 10^{-12}$), and confirmed Lorentz kick sign ($\Delta x' = -5.749\text{ mrad}$ at $x = -16.0\text{ mm}$).

4. [**Milestone 04 — Deterministic Constrained BTS Optics Matching**](file:///home/cspark/Work/projects/nkm/docs/exec-plans/completed/04_bts_deterministic_optimization.md)
   - Developed single-objective SLSQP/trust-constr optics optimization (`src/nkm/optics_optimizer.py`), reducing vertical peak beta $\beta_{y,\max}$ from $242.61\text{ m}$ down to $59.25\text{ m}$ (satisfying $\le 60.0\text{ m}$ constraint) and lowering vertical mismatch to $\mathcal{M}_y = 4.5790$.

5. [**Milestone 05 — NKM Particle Tracking & 6D Injection Dynamics**](file:///home/cspark/Work/projects/nkm/docs/exec-plans/completed/05_nkm_injection_tracking.md)
   - Implemented 6D Gaussian particle distribution generator (`src/nkm/beam.py`), thin-kick and RK4 integration (`src/nkm/tracking.py`), confirming $100.0\%$ injected beam transmission and $< 0.05\text{ }\mu\text{rad}$ stored beam kick perturbation.

6. [**Milestone 06 — Robustness, Tolerances, and Error Budget Analysis**](file:///home/cspark/Work/projects/nkm/docs/exec-plans/completed/06_robustness_tolerances.md)
   - Built 200-seed Monte Carlo error budget evaluator (`src/nkm/errors.py`) covering quad gradient errors ($0.1\%$), misalignments ($100\text{ }\mu\text{m}$), roll tilts ($0.5\text{ mrad}$), and energy errors ($0.1\%$). MOGA knee-point solution achieved $100.0\%$ feasibility.

7. [**Milestone 07 — NSGA-II Multi-Objective Genetic Algorithm (MOGA) Optimization**](file:///home/cspark/Work/projects/nkm/docs/exec-plans/completed/07_moga_pareto_optimization.md)
   - Implemented 3-objective NSGA-II Pareto optimization (`src/nkm/moga.py`), identifying a knee-point design that achieves a $61.5\times$ reduction in total exit mismatch ($\mathcal{M}_x + \mathcal{M}_y = 0.6061$) and reduces peak beta to $25.14\text{ m}$.

8. [**Milestone 08 — Publication-Quality Validation, Paper Reproduction & Release**](file:///home/cspark/Work/projects/nkm/docs/exec-plans/completed/08_publication_release.md)
   - Built automated paper table/figure generator (`src/nkm/paper.py`), one-command reproduction runner (`scripts/reproduce_paper.py`), regression test suite (`tests/test_paper_regression.py`), and authored/compiled Journal of Instrumentation (JINST) paper manuscript ([`docs/jinst-paper/paper.pdf`](file:///home/cspark/Work/projects/nkm/docs/jinst-paper/paper.pdf)).
