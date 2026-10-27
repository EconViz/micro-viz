"""Alternative short-run production forms used in textbook TP/AP/MP panels."""

from __future__ import annotations

import math
from dataclasses import dataclass

from micro_viz.firm.production.model import ProductionError


def _positive(name: str, value: float) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ProductionError(f"{name} must be finite and positive.")
    return number


def _input(variable_input: float) -> float:
    value = float(variable_input)
    if not math.isfinite(value):
        raise ProductionError("Variable input must be finite.")
    if value < 0:
        raise ProductionError("Variable input must be nonnegative.")
    return value


@dataclass(frozen=True, slots=True)
class QuadraticProductionFunction:
    """A concave total product ``Q(L) = productivity L - curvature L^2``."""

    productivity: float
    curvature: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "productivity", _positive("productivity", self.productivity))
        object.__setattr__(self, "curvature", _positive("curvature", self.curvature))

    def total_product(self, variable_input: float) -> float:
        value = _input(variable_input)
        return self.productivity * value - self.curvature * value**2

    def average_product(self, variable_input: float) -> float | None:
        value = _input(variable_input)
        return None if value == 0 else self.productivity - self.curvature * value

    def marginal_product(self, variable_input: float) -> float:
        value = _input(variable_input)
        return self.productivity - 2 * self.curvature * value

    @property
    def total_product_max_input(self) -> float:
        return self.productivity / (2 * self.curvature)

    @property
    def zero_output_input(self) -> float:
        return self.productivity / self.curvature


@dataclass(frozen=True, slots=True)
class CapacityConstrainedProductionFunction:
    """Linear total product up to a fixed capacity: ``Q(L) = min(aL, Q0)``."""

    productivity: float
    capacity: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "productivity", _positive("productivity", self.productivity))
        object.__setattr__(self, "capacity", _positive("capacity", self.capacity))

    def total_product(self, variable_input: float) -> float:
        value = _input(variable_input)
        return min(self.productivity * value, self.capacity)

    def average_product(self, variable_input: float) -> float | None:
        value = _input(variable_input)
        return None if value == 0 else self.total_product(value) / value

    def marginal_product(self, variable_input: float) -> float | None:
        """Marginal product; undefined exactly at the capacity kink."""
        value = _input(variable_input)
        if math.isclose(value, self.capacity_input, rel_tol=0.0, abs_tol=1e-12):
            return None
        return self.productivity if value < self.capacity_input else 0.0

    @property
    def capacity_input(self) -> float:
        return self.capacity / self.productivity


__all__ = ["CapacityConstrainedProductionFunction", "QuadraticProductionFunction"]
