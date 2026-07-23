# AGENTS.md — NKM Project

## Project purpose

This repository studies a nonlinear kicker magnet (NKM), the booster-to-storage-ring (BTS) transfer beam line, and off-axis injection into a storage ring. The principal goals are:

1. improve BTS optical matching and transmission;
2. import and validate NKM fields calculated with RADIA;
3. model nonlinear kicks using realistic field data;
4. evaluate injected-beam capture while minimizing stored-beam perturbation;
5. quantify robustness against beam, magnet, alignment, and field-map errors.

## Authoritative workflows

- `bts.ipynb` is the main simulation notebook.
- `bts-moga.ipynb` is optional and must remain independently executable.
- Spreadsheet field files are scientific source data produced from RADIA calculations.

## Immutable and protected files

Do not modify these files unless the user explicitly requests a simulation that regenerates them:

- `NKM_radia.ipynb`
- `NKM_radia_y=0.ipynb`
- `nlk.py`
- `storage_ring.ipynb`
- `*.xls`, `*.xlsx`, `*.xlsm`
- `*.npy`, `*.npz`
- `*.txt`

Forbidden actions include formatting, metadata cleanup, output stripping, line-ending conversion, renaming, moving, or overwriting.

Before and after every task, run:

```bash
git status --short
git diff --name-only
```

If a protected file appears in the diff, stop and revert only the unintended protected-file change.

## Allowed development locations

Prefer creating or modifying:

- `src/nkm/`
- `tests/`
- `notebooks/`
- `docs/`
- `scripts/`
- `pyproject.toml`
- `README.md`
- `.gitignore`

Modify `bts.ipynb` only when integration into the main workflow is necessary. Do not duplicate large notebook cells when reusable functions can be imported.

## Physics conventions

Document units at every public interface.

Recommended canonical internal units:

- position: m
- angle/canonical momentum: rad
- energy: eV
- magnetic field: T
- longitudinal coordinate: m
- integrated field: T m
- kick angle: rad

For an ultra-relativistic electron beam, calculate the horizontal kick consistently from

\[
\Delta x' = \frac{q}{p_0}\int B_y\,ds,
\]

with sign conventions verified against the selected Accelerator Toolbox coordinate convention.

## Engineering requirements

- Fixed random seeds for reproducible studies.
- Configuration objects rather than hidden notebook globals.
- Explicit validation of array shape, monotonic axes, units, NaN/Inf values, duplicate coordinates, and interpolation bounds.
- No silent extrapolation outside field-map coverage.
- Save generated results under a new results directory; never overwrite source data.
- Every optimizer must report bounds, constraints, seed, termination condition, and final feasibility.
- Every tracking study must report particle count, distribution, energy spread, initial Twiss parameters, apertures, loss definition, and observation points.

## Testing expectations

At minimum test:

- lattice length and element order;
- transfer-matrix consistency;
- Twiss propagation and target mismatch;
- aperture placement and loss accounting;
- field-map parsing and unit conversion;
- interpolation at tabulated points;
- kick sign and integrated-strength consistency;
- deterministic optimizer reproducibility;
- zero-field and linear-field limiting cases;
- particle-coordinate shape conventions.

## Definition of done

A task is complete only when:

1. protected files are unchanged;
2. notebook or script executes from a clean kernel/environment;
3. tests pass;
4. generated results are separated from source inputs;
5. assumptions and units are documented;
6. numerical outputs include validation checks and tolerances.
