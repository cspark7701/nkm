"""NKM: Nonlinear Kicker Magnet & BTS Line Optimization and Tracking Package."""

__version__ = "0.1.0"

from .moga import (
    BTSMOGAConfig,
    BTSMOGAProblem,
    BTSMOGAResult,
    run_bts_moga,
    save_moga_results,
    plot_moga_summary
)
from .paper import (
    generate_paper_tables,
    generate_paper_figures,
    run_paper_pipeline,
    set_publication_style,
    PUBLICATION_COLORS
)
from .fieldmap import BaseFieldMap, NKMFieldMap1D, OutOfDomainError
from .kickmap import NKMKickMap2D
from .tracking import TrackingResult
from .units import (
    Meters,
    Millimeters,
    Radians,
    Milliradians,
    Tesla,
    TeslaMeters,
    GigaelectronVolts,
    ElectronVolts,
    validate_positive,
    validate_non_zero,
    validate_finite,
    compute_rigidity
)
from .optimization import BaseOpticsObjective, DeterministicObjective, OpticsOptimizer, BTSOptimizationEvaluator
from .robust_optimization import RobustMonteCarloObjective


