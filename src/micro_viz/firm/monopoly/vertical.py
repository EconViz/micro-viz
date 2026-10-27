"""Renderer-neutral vertical-integration domain models.

The downstream firm faces the final demand ``P = a - b Q`` and spends ``c_d`` per unit on its own
processing; the upstream firm has marginal cost ``MC_u = m0 + m1 Q``. The downstream firm's *net*
marginal revenue ``NMR = a - c_d - 2 b Q`` is the upstream firm's demand when the two are
separate. A separate upstream monopolist sets its own marginal revenue equal to ``MC_u`` (a second
markup); an integrated firm sets ``NMR = MC_u``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from micro_viz.firm.perfect_competition import CompetitionError, LinearDemand


class VerticalError(CompetitionError):
    """Raised when a vertical-chain input is invalid."""


@dataclass(frozen=True, slots=True)
class ChainOutcome:
    """Quantity and prices of a vertical chain."""

    quantity: float
    transfer_price: float
    final_price: float
    upstream_profit: float
    downstream_profit: float

    @property
    def profit(self) -> float:
        return self.upstream_profit + self.downstream_profit


@dataclass(frozen=True, slots=True)
class VerticalChain:
    """Final demand, downstream unit cost and a linear upstream marginal cost."""

    demand: LinearDemand
    downstream_cost: float
    upstream_intercept: float
    upstream_slope: float = 0.0

    def __post_init__(self) -> None:
        for name in ("downstream_cost", "upstream_intercept", "upstream_slope"):
            value = getattr(self, name)
            if not math.isfinite(value) or value < 0:
                raise VerticalError(f"{name} must be finite and nonnegative.")
        if self.downstream_cost + self.upstream_intercept >= self.demand.intercept:
            raise VerticalError("Total unit cost must lie below the demand intercept.")

    def net_marginal_revenue(self, quantity: float) -> float:
        """``NMR = a - c_d - 2 b Q``: the downstream marginal revenue net of its own cost."""
        return self.demand.intercept - self.downstream_cost - 2 * self.demand.slope * quantity

    def upstream_marginal_cost(self, quantity: float) -> float:
        return self.upstream_intercept + self.upstream_slope * quantity

    def upstream_marginal_revenue(self, quantity: float) -> float:
        """Marginal revenue of the upstream firm against demand ``NMR``: ``a - c_d - 4 b Q``."""
        return self.demand.intercept - self.downstream_cost - 4 * self.demand.slope * quantity

    def _outcome(self, quantity: float, transfer_price: float) -> ChainOutcome:
        final = self.demand.intercept - self.demand.slope * quantity
        upstream_cost = self.upstream_intercept * quantity + 0.5 * self.upstream_slope * quantity**2
        return ChainOutcome(
            quantity,
            transfer_price,
            final,
            transfer_price * quantity - upstream_cost,
            (final - self.downstream_cost - transfer_price) * quantity,
        )

    def stacked(self) -> ChainOutcome:
        """Separate monopolies: upstream sets ``MR_u = MC_u`` against demand ``NMR``."""
        quantity = max(
            (self.demand.intercept - self.downstream_cost - self.upstream_intercept)
            / (4 * self.demand.slope + self.upstream_slope),
            0.0,
        )
        return self._outcome(quantity, self.net_marginal_revenue(quantity))

    def integrated(self) -> ChainOutcome:
        """One firm: ``NMR = MC_u``; the transfer price is the upstream marginal cost."""
        quantity = max(
            (self.demand.intercept - self.downstream_cost - self.upstream_intercept)
            / (2 * self.demand.slope + self.upstream_slope),
            0.0,
        )
        return self._outcome(quantity, self.upstream_marginal_cost(quantity))


@dataclass(frozen=True, slots=True)
class TransferPricingOutcome:
    """Division quantities when the intermediate good also trades at ``market_price``."""

    transfer_price: float
    upstream_quantity: float
    downstream_quantity: float

    @property
    def outside_sales(self) -> float:
        """Positive: the surplus the upstream division sells outside; negative: it is bought."""
        return self.upstream_quantity - self.downstream_quantity


def transfer_pricing(chain: VerticalChain, market_price: float) -> TransferPricingOutcome:
    """Optimal transfer price with an outside market: the market price. The upstream division
    produces where ``MC_u = P_m`` and the downstream division uses where ``NMR = P_m``."""
    if not math.isfinite(market_price) or market_price < 0:
        raise VerticalError("market_price must be finite and nonnegative.")
    if chain.upstream_slope > 0:
        upstream = max((market_price - chain.upstream_intercept) / chain.upstream_slope, 0.0)
    else:
        raise VerticalError("An outside market needs an upward-sloping upstream cost.")
    downstream = max(
        (chain.demand.intercept - chain.downstream_cost - market_price) / (2 * chain.demand.slope),
        0.0,
    )
    return TransferPricingOutcome(market_price, upstream, downstream)
