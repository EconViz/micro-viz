"""Renderer-neutral exhaustible-resource (Hotelling) model.

A competitive owner is indifferent between extracting now and later when the price net of the
constant marginal extraction cost ``c`` grows at the interest rate ``r``:
``p(t) - c = (p0 - c) e^(r t)``. With linear demand ``Q = a - b p`` the path ends at the choke
price ``a / b`` when demand is zero, and the total extracted over ``[0, T]`` must equal the stock.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from micro_viz.firm.competition import CompetitionError

BISECTIONS = 100
"""Bisection steps of the numeric solution for the initial price."""


class CapitalError(CompetitionError):
    """Raised when a resource-path input is invalid."""


@dataclass(frozen=True, slots=True)
class ExhaustibleResourcePath:
    """Demand ``Q = demand_intercept - demand_slope p``, extraction cost, rate and stock."""

    demand_intercept: float
    demand_slope: float
    extraction_cost: float
    interest_rate: float
    stock: float

    def __post_init__(self) -> None:
        for name in ("demand_intercept", "demand_slope", "interest_rate", "stock"):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0:
                raise CapitalError(f"{name} must be finite and positive.")
        if not math.isfinite(self.extraction_cost) or self.extraction_cost < 0:
            raise CapitalError("extraction_cost must be finite and nonnegative.")
        if self.extraction_cost >= self.choke_price:
            raise CapitalError("extraction_cost must lie below the choke price.")

    @property
    def choke_price(self) -> float:
        """The price at which demand falls to zero."""
        return self.demand_intercept / self.demand_slope

    def extracted(self, initial_price: float) -> float:
        """Total extracted along the path that starts at ``initial_price`` (> cost)."""
        gap = initial_price - self.extraction_cost
        choke_gap = self.choke_price - self.extraction_cost
        if gap >= choke_gap:
            return 0.0
        r = self.interest_rate
        return (self.demand_slope / r) * (choke_gap * math.log(choke_gap / gap) - choke_gap + gap)

    @property
    def initial_price(self) -> float:
        """The starting price whose path extracts exactly the stock (bisection: extraction falls
        as the initial price rises)."""
        low = self.extraction_cost
        high = self.choke_price
        for _ in range(BISECTIONS):
            middle = (low + high) / 2
            if middle <= self.extraction_cost or self.extracted(middle) > self.stock:
                low = middle
            else:
                high = middle
        return (low + high) / 2

    def price(self, time: float) -> float:
        """The price at ``time``."""
        gap = self.initial_price - self.extraction_cost
        return self.extraction_cost + gap * math.exp(self.interest_rate * time)

    def quantity(self, time: float) -> float:
        """The quantity extracted at ``time`` (zero after the path reaches the choke price)."""
        return max(self.demand_intercept - self.demand_slope * self.price(time), 0.0)

    @property
    def exhaustion_time(self) -> float:
        """``T`` at which the price reaches the choke price and the stock runs out."""
        gap = self.initial_price - self.extraction_cost
        return math.log((self.choke_price - self.extraction_cost) / gap) / self.interest_rate
