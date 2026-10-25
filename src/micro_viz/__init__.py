"""Producer theory and market-structure diagrams for EconViz."""

from micro_viz.config import Config, default_theme
from micro_viz.costs import (
    CostAnalysis,
    CostError,
    CostFunction,
    CostPoint,
    CostSegment,
    CubicCost,
    Extremum,
    PiecewiseCost,
    analyze_costs,
)
from micro_viz.production import (
    MarginalReturns,
    ProductionAnalysis,
    ProductionError,
    ProductionPoint,
    ReturnsRegion,
    ShortRunProductionFunction,
    analyze_production,
)
from micro_viz.theme import PlotTheme, shared_theme
from micro_viz.visuals import (
    average_marginal_product_canvas,
    cost_curves_grid,
    piecewise_cost_canvas,
    total_cost_canvas,
    total_product_canvas,
    unit_cost_canvas,
)

__version__ = "0.2.0.dev0"

__all__ = [
    "Config",
    "CostAnalysis",
    "CostError",
    "CostFunction",
    "CostPoint",
    "CostSegment",
    "CubicCost",
    "Extremum",
    "PiecewiseCost",
    "MarginalReturns",
    "PlotTheme",
    "ProductionAnalysis",
    "ProductionError",
    "ProductionPoint",
    "ReturnsRegion",
    "ShortRunProductionFunction",
    "__version__",
    "analyze_costs",
    "analyze_production",
    "average_marginal_product_canvas",
    "cost_curves_grid",
    "piecewise_cost_canvas",
    "total_cost_canvas",
    "unit_cost_canvas",
    "default_theme",
    "shared_theme",
    "total_product_canvas",
]
