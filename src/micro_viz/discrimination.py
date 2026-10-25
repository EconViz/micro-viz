"""Renderer-neutral price discrimination.

A seller faces linear market demands ``P = a - b Q`` and a cost function with marginal cost
``MC``. First degree: every unit sells at the buyer's own price up to ``D = MC``. Block
pricing: ``n`` equal blocks, each sold at the price of its last buyer. Third degree: the
markets are separated and ``MR_1 = MR_2 = MC``; a market whose demand intercept lies below
the common marginal cost is not served (a corner solution).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from micro_viz.competition import (
    CompetitionError,
    LinearDemand,
    profit_maximizing_output,
)
from micro_viz.costs import CostFunction
from micro_viz.monopoly import Monopolist, MonopolyOutcome

BISECTIONS = 80
"""Bisection steps of the numeric searches."""


class DiscriminationError(CompetitionError):
    """Raised when a price-discrimination input is invalid."""


def _output_at_price(demand: LinearDemand, cost: CostFunction) -> float:
    """Output where demand meets marginal cost (the competitive output)."""

    def gap(q: float) -> float:
        return demand.price(q) - cost.marginal_cost(q)

    if gap(0.0) <= 0:
        return 0.0
    low, high = 0.0, demand.quantity_intercept
    for _ in range(BISECTIONS):
        middle = (low + high) / 2
        if gap(middle) > 0:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def _area_under(demand: LinearDemand, low: float, high: float) -> float:
    """Revenue from selling units ``low..high`` at the buyers' own prices."""
    return demand.intercept * (high - low) - demand.slope * (high**2 - low**2) / 2


@dataclass(frozen=True, slots=True)
class FirstDegree:
    """Perfect (first-degree) discrimination: the price follows the demand curve."""

    demand: LinearDemand
    cost: CostFunction
    quantity: float
    revenue: float
    profit: float
    single_price: MonopolyOutcome

    @property
    def extra_profit(self) -> float:
        """Profit gained over charging one monopoly price."""
        return self.profit - self.single_price.profit


def first_degree(demand: LinearDemand, cost: CostFunction) -> FirstDegree:
    """Sell every unit up to ``D = MC`` at the buyer's own price."""
    quantity = _output_at_price(demand, cost)
    revenue = _area_under(demand, 0.0, quantity)
    return FirstDegree(
        demand=demand,
        cost=cost,
        quantity=quantity,
        revenue=revenue,
        profit=revenue - cost.total_cost(quantity),
        single_price=Monopolist(demand, cost).solve(),
    )


@dataclass(frozen=True, slots=True)
class Block:
    """One block: units ``start..end`` sold at ``price``."""

    start: float
    end: float
    price: float


@dataclass(frozen=True, slots=True)
class BlockPricing:
    """Imperfect first-degree discrimination: equal quantity blocks, each at its last price."""

    demand: LinearDemand
    cost: CostFunction
    blocks: tuple[Block, ...]
    revenue: float
    profit: float


def block_pricing(demand: LinearDemand, cost: CostFunction, blocks: int) -> BlockPricing:
    """``blocks`` equal blocks up to ``D = MC``; each is priced at the demand of its last unit."""
    if isinstance(blocks, bool) or not isinstance(blocks, int) or blocks < 1:
        raise DiscriminationError("blocks must be a positive integer.")
    top = _output_at_price(demand, cost)
    edges = [top * index / blocks for index in range(blocks + 1)]
    steps = tuple(Block(edges[i], edges[i + 1], demand.price(edges[i + 1])) for i in range(blocks))
    revenue = sum(block.price * (block.end - block.start) for block in steps)
    return BlockPricing(demand, cost, steps, revenue, revenue - cost.total_cost(top))


@dataclass(frozen=True, slots=True)
class MarketSale:
    """One market of a third-degree discriminator."""

    demand: LinearDemand
    quantity: float
    price: float
    marginal_revenue: float
    served: bool


@dataclass(frozen=True, slots=True)
class ThirdDegree:
    """Separated markets with a common marginal cost."""

    cost: CostFunction
    markets: tuple[MarketSale, ...]
    marginal_cost: float
    quantity: float
    profit: float

    def summed_marginal_revenue(
        self, top: float, samples: int = 101
    ) -> tuple[tuple[float, float], ...]:
        """Points ``(Q, MR)`` of the horizontally summed marginal revenue of the served markets."""
        levels = [top * index / (samples - 1) for index in range(samples)]
        return tuple(
            (
                sum(
                    max(0.0, (m.demand.intercept - level) / (2 * m.demand.slope))
                    for m in self.markets
                ),
                level,
            )
            for level in levels
        )


def third_degree(demands: Sequence[LinearDemand], cost: CostFunction) -> ThirdDegree:
    """Output and prices with ``MR_i = MC`` in every served market."""
    if len(demands) < 2:
        raise DiscriminationError("Third-degree discrimination needs at least two markets.")

    def sold(level: float) -> float:
        return sum(max(0.0, (d.intercept - level) / (2 * d.slope)) for d in demands)

    def gap(level: float) -> float:
        return sold(level) - profit_maximizing_output(cost, level)

    low, high = 0.0, max(d.intercept for d in demands)
    for _ in range(BISECTIONS):
        middle = (low + high) / 2
        if gap(middle) > 0:
            low = middle
        else:
            high = middle
    level = (low + high) / 2
    sales: list[MarketSale] = []
    for d in demands:
        q = max(0.0, (d.intercept - level) / (2 * d.slope))
        sales.append(
            MarketSale(
                d, q, d.price(q) if q > 0 else d.intercept, level if q > 0 else d.intercept, q > 0
            )
        )
    total = sum(s.quantity for s in sales)
    revenue = sum(s.price * s.quantity for s in sales)
    if not math.isfinite(revenue):
        raise DiscriminationError("The revenue is not finite.")
    return ThirdDegree(cost, tuple(sales), level, total, revenue - cost.total_cost(total))
