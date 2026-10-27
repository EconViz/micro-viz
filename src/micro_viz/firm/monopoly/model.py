"""Renderer-neutral single-price monopoly.

The monopolist faces the market demand ``P = a - b Q`` (so ``AR = P``) and marginal revenue
``MR = a - 2 b Q``. It chooses the output where ``MR = MC`` on the falling part of
``MR - MC``. Notation: ``Q`` output, ``P`` price, ``profit = (P - ATC) Q``, the Lerner index
``L = (P - MC) / P = 1 / |e|`` and the deadweight loss is the area between demand and MC from
the monopoly to the competitive output.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from micro_viz.firm.costs import Cost, CostFunction
from micro_viz.firm.perfect_competition import (
    CompetitionError,
    LinearDemand,
    profit_maximizing_output,
)
from micro_viz.markets.demand import Demand, DemandLike, as_demand

STEPS = 4000
"""Grid points of the numeric searches and integrals."""


class MonopolyError(CompetitionError):
    """Raised when a monopoly model or input is invalid."""


def marginal_revenue(demand: DemandLike, quantity: float) -> float:
    """``MR(Q) = a - 2 b Q`` for a straight line, ``P(Q) + Q P'(Q)`` for any other demand."""
    if isinstance(demand, Demand):
        return demand.marginal_revenue(quantity)
    return demand.intercept - 2 * demand.slope * quantity


def elasticity(demand: DemandLike, quantity: float) -> float:
    """Price elasticity of demand ``e = -(1 / b) P / Q`` (negative; ``-inf`` at ``Q = 0``)."""
    if isinstance(demand, Demand):
        return demand.elasticity(quantity)
    if quantity <= 0:
        return -math.inf
    return -demand.price(quantity) / (demand.slope * quantity)


def _bisect(function, low: float, high: float) -> float:  # type: ignore[no-untyped-def]
    above = function(low) > 0  # the sign at ``low`` only changes when ``low`` moves, and then stays
    for _ in range(80):
        middle = (low + high) / 2
        if above == (function(middle) > 0):
            low = middle
        else:
            high = middle
    return (low + high) / 2


def _roots(function, high: float) -> list[float]:  # type: ignore[no-untyped-def]
    """Sign changes of ``function`` on ``(0, high)``."""
    grid = [high * index / STEPS for index in range(STEPS + 1)]
    roots: list[float] = []
    value = function(grid[0])
    for index in range(STEPS):
        # every grid point closes one cell and opens the next, so it is evaluated once
        last = index + 1 == STEPS
        following = value if last and value <= 0 else function(grid[index + 1])
        if value > 0 >= following:
            roots.append(_bisect(function, grid[index], grid[index + 1]))
        value = following
    return roots


@dataclass(frozen=True, slots=True)
class MonopolyOutcome:
    """The profit-maximising choice of a monopolist and its welfare comparison."""

    demand: DemandLike
    cost: CostFunction
    quantity: float
    price: float
    marginal_revenue: float
    marginal_cost: float
    average_total_cost: float | None
    profit: float
    lerner_index: float
    elasticity: float
    competitive_quantity: float
    competitive_price: float
    deadweight_loss: float
    transfer: float

    def to_dict(self) -> dict[str, object]:
        return {
            "quantity": self.quantity,
            "price": self.price,
            "profit": self.profit,
            "lerner_index": self.lerner_index,
            "elasticity": self.elasticity,
            "competitive_quantity": self.competitive_quantity,
            "competitive_price": self.competitive_price,
            "deadweight_loss": self.deadweight_loss,
            "transfer": self.transfer,
        }


@dataclass(frozen=True, slots=True, init=False)
class Monopolist:
    """A monopolist with a demand curve and a cost function.

    Pass the objects (:class:`~micro_viz.firm.perfect_competition.LinearDemand` or
    :class:`~micro_viz.Demand`, and any cost function) or formulas for either:
    ``Monopolist("P = 100 - Q", "TC = 200 + 20Q")``. A straight-line ``Demand`` is held as a
    ``LinearDemand``.
    """

    demand: DemandLike
    cost: CostFunction

    def __init__(self, demand: DemandLike | str, cost: CostFunction | str) -> None:
        object.__setattr__(self, "demand", as_demand(demand))
        object.__setattr__(self, "cost", Cost(cost) if isinstance(cost, str) else cost)

    def profit(self, quantity: float) -> float:
        """``P(Q) Q - TC(Q)``."""
        return self.demand.price(quantity) * quantity - self.cost.total_cost(quantity)

    def with_demand(self, demand: DemandLike | str) -> Monopolist:
        """The same firm facing another demand curve."""
        return Monopolist(demand, self.cost)

    def with_cost(self, cost: CostFunction | str) -> Monopolist:
        """The same demand with another cost function (a tax, say)."""
        return Monopolist(self.demand, cost)

    def solve(self) -> MonopolyOutcome:
        """Output where ``MR = MC`` (the best sign change, or zero when none pays)."""
        top = self.demand.quantity_intercept

        def slack(q: float) -> float:
            return marginal_revenue(self.demand, q) - self.cost.marginal_cost(q)

        reach = top / 2 if isinstance(self.demand, LinearDemand) else top
        candidates = [0.0, *_roots(slack, reach)]
        quantity = max(candidates, key=self.profit)
        price = self.demand.price(quantity)
        competitive = self._competitive_quantity()
        loss = self._area(quantity, competitive)
        return MonopolyOutcome(
            demand=self.demand,
            cost=self.cost,
            quantity=quantity,
            price=price,
            marginal_revenue=marginal_revenue(self.demand, quantity),
            marginal_cost=self.cost.marginal_cost(quantity),
            average_total_cost=self.cost.average_total_cost(quantity),
            profit=self.profit(quantity),
            lerner_index=(price - self.cost.marginal_cost(quantity)) / price if price else 0.0,
            elasticity=elasticity(self.demand, quantity),
            competitive_quantity=competitive,
            competitive_price=self.demand.price(competitive),
            deadweight_loss=loss,
            transfer=(price - self.demand.price(competitive)) * quantity,
        )

    def _competitive_quantity(self) -> float:
        def gap(q: float) -> float:
            return self.demand.price(q) - self.cost.marginal_cost(q)

        roots = _roots(gap, self.demand.quantity_intercept)
        return max(roots) if roots else 0.0

    def _area(self, low: float, high: float) -> float:
        """Area between demand and MC from ``low`` to ``high`` (trapezoid rule)."""
        if high <= low:
            return 0.0
        step = (high - low) / STEPS
        values = [
            self.demand.price(low + step * i) - self.cost.marginal_cost(low + step * i)
            for i in range(STEPS + 1)
        ]
        return step * (sum(values) - (values[0] + values[-1]) / 2)


@dataclass(frozen=True, slots=True)
class MultiplantOutcome:
    """A multiplant monopoly at its optimum."""

    quantity: float
    price: float
    marginal_cost: float
    plant_outputs: tuple[float, ...]
    profit: float


@dataclass(frozen=True, slots=True)
class MultiplantMonopoly:
    """A monopolist producing in several plants with cost functions ``C_i``."""

    demand: LinearDemand
    plants: tuple[CostFunction, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "plants", tuple(self.plants))
        if len(self.plants) < 2:
            raise MonopolyError("A multiplant monopoly needs at least two plants.")

    def outputs_at(self, marginal_cost: float) -> tuple[float, ...]:
        """Each plant's output where its marginal cost equals ``marginal_cost``."""
        return tuple(profit_maximizing_output(plant, marginal_cost) for plant in self.plants)

    def summed_marginal_cost(
        self, top: float, samples: int = 101
    ) -> tuple[tuple[float, float], ...]:
        """Points ``(Q, MC)`` of the horizontally summed marginal cost up to level ``top``."""
        low = min(plant.marginal_cost(0.0) for plant in self.plants)
        low = min(low, top)
        levels: Sequence[float] = [low + (top - low) * i / (samples - 1) for i in range(samples)]
        return tuple((sum(self.outputs_at(level)), level) for level in levels)

    def solve(self) -> MultiplantOutcome:
        """Where ``MR = MC_1 = MC_2 = ...``."""

        def slack(level: float) -> float:
            return marginal_revenue(self.demand, sum(self.outputs_at(level))) - level

        top = self.demand.intercept
        level = _bisect(slack, 0.0, top)
        outputs = self.outputs_at(level)
        total = sum(outputs)
        price = self.demand.price(total)
        cost = sum(plant.total_cost(q) for plant, q in zip(self.plants, outputs, strict=True))
        return MultiplantOutcome(total, price, level, outputs, price * total - cost)
