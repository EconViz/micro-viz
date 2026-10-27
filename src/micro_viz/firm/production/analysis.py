"""Typed analysis results for short-run production."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, cast

from micro_viz.firm.production.model import ProductionError, ShortRunProductionFunction


class ProductionModel(Protocol):
    """One-input production behavior consumed by the analysis layer."""

    @property
    def input_symbol(self) -> str: ...

    @property
    def output_symbol(self) -> str: ...

    def total_product(self, variable_input: float) -> float: ...

    def average_product(self, variable_input: float) -> float | None: ...

    def marginal_product(self, variable_input: float) -> float: ...

    def to_dict(self) -> dict[str, object]: ...


class MarginalReturns(str, Enum):
    """The direction and sign of marginal product over an input interval."""

    INCREASING = "increasing"
    DIMINISHING = "diminishing"
    NEGATIVE = "negative"


@dataclass(frozen=True, slots=True)
class ProductionPoint:
    """TP, AP, and MP evaluated at one variable-input quantity."""

    variable_input: float
    total_product: float
    average_product: float | None
    marginal_product: float

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation of the point."""
        return {
            "variable_input": self.variable_input,
            "total_product": self.total_product,
            "average_product": self.average_product,
            "marginal_product": self.marginal_product,
        }


@dataclass(frozen=True, slots=True)
class ReturnsRegion:
    """A closed input interval with one marginal-returns classification."""

    kind: MarginalReturns
    start_input: float
    end_input: float

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation of the interval."""
        return {
            "kind": self.kind.value,
            "start_input": self.start_input,
            "end_input": self.end_input,
        }


@dataclass(frozen=True, slots=True)
class ProductionAnalysis:
    """Sampled products and exact or sample-estimated boundaries for a production function."""

    production_function: ProductionModel
    input_range: tuple[float, float]
    points: tuple[ProductionPoint, ...]
    regions: tuple[ReturnsRegion, ...]
    inflection_input: float
    average_product_max_input: float
    total_product_max_input: float

    def to_dict(self) -> dict[str, object]:
        """Serialize the model, sampled products, and marginal-return regions."""
        return {
            "production_function": self.production_function.to_dict(),
            "input_range": list(self.input_range),
            "points": [point.to_dict() for point in self.points],
            "regions": [region.to_dict() for region in self.regions],
            "inflection_input": self.inflection_input,
            "average_product_max_input": self.average_product_max_input,
            "total_product_max_input": self.total_product_max_input,
        }


def analyze_production(
    production_function: ProductionModel,
    *,
    input_range: tuple[float, float],
    samples: int = 201,
) -> ProductionAnalysis:
    """Evaluate TP/AP/MP and classify marginal returns over ``input_range``."""
    start, end = (float(value) for value in input_range)
    if not math.isfinite(start) or not math.isfinite(end):
        raise ProductionError("The input range must be finite.")
    if start < 0:
        raise ProductionError("The input range must be nonnegative.")
    if end <= start:
        raise ProductionError("The input range must be strictly increasing.")
    if isinstance(samples, bool) or not isinstance(samples, int) or samples < 2:
        raise ProductionError("samples must be an integer of at least 2.")

    step = (end - start) / (samples - 1)
    inputs = tuple(start + step * index for index in range(samples))
    points = tuple(
        ProductionPoint(
            variable_input=value,
            total_product=production_function.total_product(value),
            average_product=production_function.average_product(value),
            marginal_product=production_function.marginal_product(value),
        )
        for value in inputs
    )
    if isinstance(production_function, ShortRunProductionFunction):
        inflection = production_function.inflection_input
        average_maximum = production_function.average_product_max_input
        maximum = production_function.total_product_max_input
    else:
        inflection = max(points, key=lambda point: point.marginal_product).variable_input
        average_maximum = max(
            (point for point in points if point.average_product is not None),
            key=lambda point: cast(float, point.average_product),
        ).variable_input
        maximum = max(points, key=lambda point: point.total_product).variable_input
    candidate_regions = (
        (MarginalReturns.INCREASING, 0.0, inflection),
        (MarginalReturns.DIMINISHING, inflection, maximum),
        (MarginalReturns.NEGATIVE, maximum, math.inf),
    )
    regions = tuple(
        ReturnsRegion(kind, max(start, lower), min(end, upper))
        for kind, lower, upper in candidate_regions
        if max(start, lower) < min(end, upper)
    )
    return ProductionAnalysis(
        production_function=production_function,
        input_range=(start, end),
        points=points,
        regions=regions,
        inflection_input=inflection,
        average_product_max_input=average_maximum,
        total_product_max_input=maximum,
    )


__all__ = [
    "MarginalReturns",
    "ProductionAnalysis",
    "ProductionModel",
    "ProductionPoint",
    "ReturnsRegion",
    "analyze_production",
]
