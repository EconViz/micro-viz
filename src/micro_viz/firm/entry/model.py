"""Renderer-neutral competitive-industry entry domain model.

Identical price-taking firms with a short-run cost function face market demand. Firms enter
while price exceeds the lowest ATC and leave while it is below, so the long-run price is the
lowest ATC and the number of firms is demand at that price over one firm's output.
"""

from __future__ import annotations

from dataclasses import dataclass

from micro_viz.firm.competition import LinearDemand, break_even_price, solve_competitive_firm
from micro_viz.firm.costs import CubicCost
from micro_viz.firm.longrun import SEARCH_STEPS, LongRunError


@dataclass(frozen=True, slots=True)
class MarketPoint:
    """An equilibrium of the industry for a number of firms."""

    firms: float
    price: float
    quantity: float
    firm_output: float
    profit: float


@dataclass(frozen=True, slots=True)
class IndustryEntry:
    """Identical price-taking firms facing market demand; the number of firms adjusts."""

    demand: LinearDemand
    cost: CubicCost

    @property
    def long_run_price(self) -> float:
        """The lowest ATC, where profit is zero."""
        value = break_even_price(self.cost)
        assert value is not None
        return value

    def supply(self, firms: float, price: float) -> float:
        """Industry output at ``price`` with ``firms`` firms."""
        return firms * solve_competitive_firm(self.cost, price).output

    def curve(
        self, firms: float, price_max: float, samples: int = 61
    ) -> tuple[tuple[float, float], ...]:
        """Points ``(Q, p)`` of the short-run industry supply of ``firms`` firms."""
        low = solve_competitive_firm(self.cost, 0.0).shutdown_price
        prices = [low + (price_max - low) * i / (samples - 1) for i in range(samples)]
        return tuple((self.supply(firms, p), p) for p in prices)

    def equilibrium(self, firms: float, demand: LinearDemand | None = None) -> MarketPoint:
        """Price where industry supply meets demand, with the profit of each firm."""
        market = demand or self.demand
        low = solve_competitive_firm(self.cost, 0.0).shutdown_price
        high = market.intercept
        if self.supply(firms, high) < market.quantity(high) or high <= low:
            raise LongRunError("Demand and supply do not cross at a positive price.")
        for _ in range(SEARCH_STEPS):
            middle = (low + high) / 2
            if self.supply(firms, middle) < market.quantity(middle):
                low = middle
            else:
                high = middle
        price = (low + high) / 2
        outcome = solve_competitive_firm(self.cost, price)
        return MarketPoint(firms, price, market.quantity(price), outcome.output, outcome.profit)

    def long_run_firms(self, demand: LinearDemand | None = None) -> float:
        """Firms in the long run: market demand at the long-run price over one firm's output."""
        market = demand or self.demand
        price = self.long_run_price
        return market.quantity(price) / solve_competitive_firm(self.cost, price).output
