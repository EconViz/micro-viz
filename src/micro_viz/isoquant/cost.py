"""Cost minimization with isocost lines.

An isocost line ``C = W L + R K`` collects the bundles that cost ``C`` at the input prices
``W`` (labour) and ``R`` (capital). The cheapest bundle for an output is where the lowest
isocost line touches the isoquant: tangent for smooth isoquants (``MRTS = W / R``), a corner
for straight or L-shaped ones.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from micro_viz.isoquant.model import (
    CobbDouglas,
    FixedProportions,
    IsoquantError,
    PerfectSubstitutes,
    Point,
    Technology,
)


@dataclass(frozen=True, slots=True)
class Bundle:
    """A bundle of labour and capital and what it costs."""

    labor: float
    capital: float
    cost: float


def _prices(wage: float, rent: float) -> None:
    for name, value in (("wage", wage), ("rent", rent)):
        if not math.isfinite(value) or value <= 0:
            raise IsoquantError(f"{name} must be finite and positive.")


def cost_of(labor: float, capital: float, wage: float, rent: float) -> float:
    """``W L + R K``."""
    return wage * labor + rent * capital


def cost_minimizing_bundle(tech: Technology, output: float, wage: float, rent: float) -> Bundle:
    """The cheapest bundle producing ``output`` at input prices ``wage`` and ``rent``."""
    _prices(wage, rent)
    if output <= 0:
        raise IsoquantError("output must be positive.")
    if isinstance(tech, CobbDouglas):
        ratio = tech.capital_share * wage / (tech.labor_share * rent)
        labor = tech.scale_for(output, 1.0, ratio)
        capital = ratio * labor
    elif isinstance(tech, FixedProportions):
        labor, capital = tech.corner(output)
    elif isinstance(tech, PerfectSubstitutes):
        if wage / tech.labor_weight <= rent / tech.capital_weight:
            labor, capital = output / tech.labor_weight, 0.0
        else:
            labor, capital = 0.0, output / tech.capital_weight
    else:
        raise IsoquantError(
            "Unsupported technology; use CobbDouglas, PerfectSubstitutes or FixedProportions."
        )
    return Bundle(labor, capital, cost_of(labor, capital, wage, rent))


def isocost_segment(cost: float, wage: float, rent: float, bounds: Point) -> tuple[Point, Point]:
    """The isocost line of ``cost`` clipped to the box ``0..bounds`` (L, K)."""
    _prices(wage, rent)
    l_max, k_max = bounds
    labor_low = max(0.0, (cost - rent * k_max) / wage)
    labor_high = min(l_max, cost / wage)
    if labor_low >= labor_high:
        raise IsoquantError("The isocost line lies outside the box.")
    return (
        (labor_low, (cost - wage * labor_low) / rent),
        (labor_high, (cost - wage * labor_high) / rent),
    )


def expansion_path(
    tech: Technology, outputs: tuple[float, ...], wage: float, rent: float
) -> tuple[Bundle, ...]:
    """The cheapest bundle of each output; its cost is long-run total cost."""
    return tuple(cost_minimizing_bundle(tech, q, wage, rent) for q in outputs)
