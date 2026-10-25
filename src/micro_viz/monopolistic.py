"""Renderer-neutral monopolistic competition.

Each firm faces a downward-sloping demand ``P = a - b Q`` and behaves like a monopolist in the
short run. Entry shifts the demand in (the intercept ``a`` falls, the slope ``b`` is kept)
until the best profit is zero: demand is tangent to ATC at the output where ``MR = MC``. There
price exceeds MC and output is below the output at minimum ATC (excess capacity).
"""

from __future__ import annotations

from dataclasses import dataclass

from micro_viz.competition import CompetitionError, LinearDemand
from micro_viz.costs import CubicCost
from micro_viz.monopoly import Monopolist, MonopolyOutcome

ITERATIONS = 80
"""Bisection steps when searching for the long-run demand."""


@dataclass(frozen=True, slots=True)
class MonopolisticOutcome:
    """Short-run and long-run equilibria of a monopolistically competitive firm."""

    short_run: MonopolyOutcome
    long_run: MonopolyOutcome
    long_run_demand: LinearDemand
    minimum_atc_output: float
    minimum_atc: float

    @property
    def excess_capacity(self) -> float:
        """Output at minimum ATC less the long-run output."""
        return self.minimum_atc_output - self.long_run.quantity

    def to_dict(self) -> dict[str, object]:
        return {
            "short_run": self.short_run.to_dict(),
            "long_run": self.long_run.to_dict(),
            "long_run_intercept": self.long_run_demand.intercept,
            "minimum_atc_output": self.minimum_atc_output,
            "minimum_atc": self.minimum_atc,
            "excess_capacity": self.excess_capacity,
        }


def long_run_demand(demand: LinearDemand, cost: CubicCost) -> LinearDemand:
    """Demand with the same slope whose best profit is zero (tangent to ATC)."""

    def best(intercept: float) -> float:
        return Monopolist(LinearDemand(intercept, demand.slope), cost).solve().profit

    high = demand.intercept
    if best(high) < 0:
        raise CompetitionError("The firm already makes a loss; there is no entry to model.")
    low = 0.0
    for _ in range(ITERATIONS):
        middle = (low + high) / 2
        if middle <= 0 or best(middle) < 0:
            low = middle
        else:
            high = middle
    return LinearDemand(high, demand.slope)


def solve_monopolistic_competition(demand: LinearDemand, cost: CubicCost) -> MonopolisticOutcome:
    """Short run at ``demand`` and the long run after entry."""
    short = Monopolist(demand, cost).solve()
    longer = long_run_demand(demand, cost)
    q = cost.minimum_average_total_cost_output
    return MonopolisticOutcome(
        short_run=short,
        long_run=Monopolist(longer, cost).solve(),
        long_run_demand=longer,
        minimum_atc_output=q,
        minimum_atc=cost.total_cost(q) / q,
    )
