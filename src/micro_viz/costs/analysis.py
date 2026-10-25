"""Typed analysis of a short-run cost function: sampled curves and exact extreme points."""

from __future__ import annotations

import math
from dataclasses import dataclass

from micro_viz.costs.model import CostError, CostFunction, CubicCost, PiecewiseCost


@dataclass(frozen=True, slots=True)
class CostPoint:
    """Every cost measure at one output; averages are ``None`` at zero output."""

    output: float
    fixed_cost: float
    variable_cost: float
    total_cost: float
    marginal_cost: float
    average_fixed_cost: float | None
    average_variable_cost: float | None
    average_total_cost: float | None

    def to_dict(self) -> dict[str, object]:
        """A JSON-compatible representation of the point."""
        return {
            "output": self.output,
            "fixed_cost": self.fixed_cost,
            "variable_cost": self.variable_cost,
            "total_cost": self.total_cost,
            "marginal_cost": self.marginal_cost,
            "average_fixed_cost": self.average_fixed_cost,
            "average_variable_cost": self.average_variable_cost,
            "average_total_cost": self.average_total_cost,
        }


@dataclass(frozen=True, slots=True)
class Extremum:
    """The output where a unit-cost curve is lowest and its value there."""

    output: float
    value: float

    def to_dict(self) -> dict[str, float]:
        return {"output": self.output, "value": self.value}


@dataclass(frozen=True, slots=True)
class CostAnalysis:
    """Sampled cost curves of one cost function and its exact extreme points.

    ``marginal_cost_path`` is the MC curve as a polyline; where MC jumps (a piecewise cost
    function) the path contains both sides of the jump at the same output, so a drawing shows
    the vertical step. The minimum points are exact for :class:`CubicCost` and ``None`` for
    other cost functions.
    """

    cost: CostFunction
    output_range: tuple[float, float]
    points: tuple[CostPoint, ...]
    marginal_cost_path: tuple[tuple[float, float], ...]
    minimum_average_variable_cost: Extremum | None
    minimum_average_total_cost: Extremum | None
    minimum_marginal_cost: Extremum | None

    def to_dict(self) -> dict[str, object]:
        """Serialize the cost function, the samples and the extreme points."""

        def extremum(value: Extremum | None) -> dict[str, float] | None:
            return None if value is None else value.to_dict()

        return {
            "cost": self.cost.to_dict(),
            "output_range": list(self.output_range),
            "points": [point.to_dict() for point in self.points],
            "marginal_cost_path": [list(point) for point in self.marginal_cost_path],
            "minimum_average_variable_cost": extremum(self.minimum_average_variable_cost),
            "minimum_average_total_cost": extremum(self.minimum_average_total_cost),
            "minimum_marginal_cost": extremum(self.minimum_marginal_cost),
        }


def _point(cost: CostFunction, output: float) -> CostPoint:
    return CostPoint(
        output=output,
        fixed_cost=cost.fixed_cost,
        variable_cost=cost.variable_cost(output),
        total_cost=cost.total_cost(output),
        marginal_cost=cost.marginal_cost(output),
        average_fixed_cost=cost.average_fixed_cost(output),
        average_variable_cost=cost.average_variable_cost(output),
        average_total_cost=cost.average_total_cost(output),
    )


def _marginal_path(
    cost: CostFunction, grid: tuple[float, ...], start: float, end: float
) -> tuple[tuple[float, float], ...]:
    if not isinstance(cost, PiecewiseCost):
        return tuple((q, cost.marginal_cost(q)) for q in grid)
    path: list[tuple[float, float]] = []
    previous = 0.0
    for segment in cost.segments:
        low, high = max(start, previous), min(end, segment.end)
        if low < high:
            inside = [q for q in grid if low < q < high]
            for q in (low, *inside):
                path.append((q, segment.marginal_cost(q - previous)))
            path.append((high, segment.marginal_cost(high - previous)))
        previous = segment.end
    return tuple(path)


def analyze_costs(
    cost: CostFunction,
    *,
    output_range: tuple[float, float],
    samples: int = 201,
) -> CostAnalysis:
    """Evaluate every cost measure over ``output_range`` at ``samples`` evenly spaced outputs.

    A piecewise cost function's range must lie within its capacity. The first output may be
    zero, where the average costs are undefined.
    """
    start, end = (float(value) for value in output_range)
    if not math.isfinite(start) or not math.isfinite(end):
        raise CostError("The output range must be finite.")
    if start < 0:
        raise CostError("The output range must be nonnegative.")
    if end <= start:
        raise CostError("The output range must be strictly increasing.")
    if end > cost.capacity:
        raise CostError(f"The output range exceeds the capacity {cost.capacity}.")
    if isinstance(samples, bool) or not isinstance(samples, int) or samples < 2:
        raise CostError("samples must be an integer of at least 2.")
    step = (end - start) / (samples - 1)
    grid = tuple(start + step * index for index in range(samples))
    minimum_average_variable = minimum_average_total = minimum_marginal = None
    if isinstance(cost, CubicCost):
        q = cost.minimum_average_variable_cost_output
        minimum_average_variable = Extremum(q, cost.variable_cost(q) / q) if q > 0 else None
        q = cost.minimum_average_total_cost_output
        minimum_average_total = Extremum(q, cost.total_cost(q) / q) if q > 0 else None
        q = cost.minimum_marginal_cost_output
        minimum_marginal = Extremum(q, cost.marginal_cost(q)) if q > 0 else None
    return CostAnalysis(
        cost=cost,
        output_range=(start, end),
        points=tuple(_point(cost, q) for q in grid),
        marginal_cost_path=_marginal_path(cost, grid, start, end),
        minimum_average_variable_cost=minimum_average_variable,
        minimum_average_total_cost=minimum_average_total,
        minimum_marginal_cost=minimum_marginal,
    )


__all__ = ["CostAnalysis", "CostPoint", "Extremum", "analyze_costs"]
