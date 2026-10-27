"""Compatibility imports for production-form visual builders.

New code may import these builders from :mod:`micro_viz.firm.production.visuals`.
"""

from micro_viz.firm.production.visuals.forms import (
    capacity_production_grid,
    quadratic_production_grid,
)
from micro_viz.firm.production.visuals.rational import rational_production_region_grid

__all__ = [
    "capacity_production_grid",
    "quadratic_production_grid",
    "rational_production_region_grid",
]
