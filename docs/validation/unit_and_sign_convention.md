# Unit and Sign Convention Specification

## 1. Overview

This document specifies the canonical unit definitions, metadata structures, and Lorentz kick sign conventions used throughout the NKM (Nonlinear Kicker Magnet) codebase. All implicit or magnitude-based unit inference (such as checking `if abs(val) > 1`) is strictly prohibited.

---

## 2. Canonical Internal Units

The NKM python package enforces a unified SI internal unit system across all physics calculations, particle tracking, and field map processing:

| Physics Quantity | Internal Symbol | Canonical Unit | Unit Representation |
| :--- | :--- | :--- | :--- |
| Spatial position | $x, y, s$ | meters | `m` |
| Canonical momentum / Angle | $x', y'$ | radians | `rad` |
| Beam energy | $E_0$ | electron-volts | `eV` |
| Magnetic field strength | $B_y, B_x$ | Tesla | `T` |
| Integrated field | $\int B_y ds, \int B_x ds$ | Tesla-meters | `T_m` |
| Particle charge | $q$ | Coulombs | `C` (e.g. $-1.602176634\times 10^{-19}$ C) |
| Magnetic rigidity | $B\rho$ | Tesla-meters | `T_m` |

---

## 3. Metadata Model (`KickMapMetadata`)

All magnetic field and kick map representations are accompanied by an immutable `KickMapMetadata` dataclass defined in `src/nkm/units.py`:

```python
@dataclass(frozen=True)
class KickMapMetadata:
    coordinate_unit: Literal["m", "mm"]
    value_type: Literal["field", "integrated_field", "kick_angle"]
    value_unit: Literal["T", "T_m", "T_mm", "rad", "mrad"]
    beam_energy_eV: Optional[float]
    particle_charge_C: float = -1.602176634e-19
    longitudinal_unit: Optional[Literal["m", "mm"]] = "m"
    sign_convention: str = "AT"
```

### Validation Rules
1. `value_type == "field"` strictly requires `value_unit == "T"`.
2. `value_type == "integrated_field"` requires `value_unit` in `("T_m", "T_mm")`.
3. `value_type == "kick_angle"` requires `value_unit` in `("rad", "mrad")`.
4. Magnitude-based heuristics are replaced by explicit metadata lookup or conversion parameters.

---

## 4. Rigidity and Lorentz Kick Sign Conventions

For an ultra-relativistic electron beam ($E \approx p c$), the magnetic rigidity is defined as:

\[
B\rho = \frac{p_0}{|q|} = \frac{E_{\text{eV}} \cdot e}{|q| \cdot c} = \frac{E_{\text{eV}}}{c} \quad [\text{T m}]
\]

The horizontal deflection angle $\Delta x'$ in Accelerator Toolbox (AT) coordinate conventions for a particle of charge $q$ traversing vertical field $B_y$ is:

\[
\Delta x' = \frac{q}{p_0} \int B_y \, ds = \frac{q}{|q|} \frac{\int B_y \, ds}{B\rho}
\]

For electrons ($q = -e < 0$):

\[
\Delta x' = - \frac{\int B_y \, ds}{B\rho}
\]

Hence, a positive integrated vertical field ($\int B_y ds > 0$) induces a negative horizontal kick ($\Delta x' < 0$), directing the injected electron beam towards the storage ring reference axis.

---

## 5. Verification & Testing

Unit conversions, sign conventions, and metadata validity are covered by `tests/test_units.py`:
- `test_rigidity_computation`: Rigidity calculation at 4.0 GeV.
- `test_metadata_validation`: Rejection of invalid unit strings or mismatched value types.
- `test_conversions`: Conversion between `mrad` $\leftrightarrow$ `rad`, `T_mm` $\leftrightarrow$ `T_m`, and `mm` $\leftrightarrow$ `m`.
- `test_electron_and_positive_charge_signs`: Explicit verification of charge sign dependence.
- `test_roundtrip_conversions`: Exact numerical recovery across `integrated_field_to_kick` and `kick_to_integrated_field`.
- `test_rejection_of_ambiguous_input`: Raising `ValueError` when required energy/unit metadata is missing.
