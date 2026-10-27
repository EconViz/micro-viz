"""Renderer-neutral monopoly-regulation domain models.

A ceiling ``P_max`` caps the price, so average revenue is ``min(P_max, a - b Q)`` and marginal
revenue equals ``P_max`` up to the output ``Q_max`` where demand meets the ceiling, then jumps
down to the unregulated ``MR``. For a natural monopoly (ATC falling where demand crosses it)
three prices are compared: the unregulated one (``MR = MC``), marginal-cost pricing (``P = MC``,
a loss of ``(ATC - MC) Q``) and average-cost pricing (``P = ATC``, zero profit).
"""

from __future__ import annotations

from dataclasses import dataclass

from micro_viz.competition import CompetitionError, LinearDemand
from micro_viz.costs import CostFunction
from micro_viz.demand import linear_demand
from micro_viz.monopoly import Monopolist, MonopolyOutcome, marginal_revenue

STEPS = 4000
"""Grid points of the numeric searches."""


@dataclass(frozen=True, slots=True)
class CeilingOutcome:
    """A monopolist facing a price ceiling."""

    ceiling: float
    ceiling_quantity: float
    quantity: float
    price: float
    profit: float
    unregulated: MonopolyOutcome

    def marginal_revenue(self, quantity: float) -> float:
        """Marginal revenue under the ceiling (flat at the ceiling, then the unregulated MR)."""
        if quantity < self.ceiling_quantity:
            return self.ceiling
        return marginal_revenue(self.unregulated.demand, quantity)


def price_ceiling_outcome(firm: Monopolist, ceiling: float) -> CeilingOutcome:
    """Best output when the price may not exceed ``ceiling``."""
    if ceiling <= 0:
        raise CompetitionError("The ceiling must be positive.")
    demand, cost = firm.demand, firm.cost
    top = demand.quantity_intercept
    ceiling_quantity = demand.quantity(ceiling)

    def profit(q: float) -> float:
        return min(ceiling, demand.price(q)) * q - cost.total_cost(q)

    grid = [top * index / STEPS for index in range(STEPS + 1)]
    quantity = max(grid, key=profit)
    return CeilingOutcome(
        ceiling=ceiling,
        ceiling_quantity=ceiling_quantity,
        quantity=quantity,
        price=min(ceiling, demand.price(quantity)),
        profit=profit(quantity),
        unregulated=firm.solve(),
    )


@dataclass(frozen=True, slots=True)
class PricingPoint:
    """An output and the price charged for it."""

    quantity: float
    price: float
    profit: float


@dataclass(frozen=True, slots=True)
class NaturalMonopolyPricing:
    """Unregulated, marginal-cost and average-cost pricing of a natural monopoly."""

    demand: LinearDemand
    cost: CostFunction
    unregulated: PricingPoint
    marginal_cost: PricingPoint
    average_cost: PricingPoint


def natural_monopoly_pricing(firm: Monopolist) -> NaturalMonopolyPricing:
    """The three prices of ``firm``; needs ATC to fall below demand at some output."""
    demand, cost = firm.demand, firm.cost
    top = demand.quantity_intercept
    unregulated = firm.solve()

    def point(q: float) -> PricingPoint:
        return PricingPoint(q, demand.price(q), firm.profit(q))

    grid = [top * index / STEPS for index in range(1, STEPS)]

    def gap(q: float) -> float:
        return demand.price(q) - (cost.average_total_cost(q) or 0.0)

    inside = [q for q in grid if gap(q) >= 0]
    if not inside:
        raise CompetitionError("Demand never reaches average cost; no price covers the cost.")
    average_q = max(inside)
    mc_q = top
    for q in grid:
        if demand.price(q) <= cost.marginal_cost(q):
            mc_q = q
            break
    return NaturalMonopolyPricing(
        demand=linear_demand(demand),
        cost=cost,
        unregulated=PricingPoint(unregulated.quantity, unregulated.price, unregulated.profit),
        marginal_cost=point(mc_q),
        average_cost=point(average_q),
    )
