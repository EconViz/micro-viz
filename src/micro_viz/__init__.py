"""Producer theory and market-structure diagrams for EconViz."""

from micro_viz.config import Config, default_theme
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
from micro_viz.visuals import average_marginal_product_canvas, total_product_canvas

__version__ = "0.1.0.dev0"

__all__ = [
    "Config",
    "MarginalReturns",
    "PlotTheme",
    "ProductionAnalysis",
    "ProductionError",
    "ProductionPoint",
    "ReturnsRegion",
    "ShortRunProductionFunction",
    "__version__",
    "analyze_production",
    "average_marginal_product_canvas",
    "default_theme",
    "shared_theme",
    "total_product_canvas",
]
