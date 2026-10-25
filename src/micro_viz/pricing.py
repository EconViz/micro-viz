"""Renderer-neutral two-part tariffs.

Buyers of several types, each with a linear demand ``P = a - b Q`` and a head count, face an
entry fee ``T`` and a usage price ``p`` per unit; the seller has a constant marginal cost
``MC``. A buyer enters when the consumer surplus at ``p`` covers ``T``. With one type the
best tariff sets ``p = MC`` and ``T`` equal to the whole surplus; with two types a usage
price above ``MC`` and an entry fee equal to the smaller surplus can earn more.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from micro_viz.competition import CompetitionError, LinearDemand

GRID = 2000
"""Points of the usage-price search."""


class PricingError(CompetitionError):
    """Raised when a pricing input is invalid."""


@dataclass(frozen=True, slots=True)
class BuyerType:
    """A group of ``count`` identical buyers with the demand ``demand``."""

    demand: LinearDemand
    count: float = 1.0

    def __post_init__(self) -> None:
        if not math.isfinite(self.count) or self.count <= 0:
            raise PricingError("count must be finite and positive.")

    def surplus(self, price: float) -> float:
        """Consumer surplus of one buyer at the usage price."""
        gap = self.demand.intercept - price
        return gap * gap / (2 * self.demand.slope) if gap > 0 else 0.0

    def quantity(self, price: float) -> float:
        return self.demand.quantity(price)


@dataclass(frozen=True, slots=True)
class TariffOutcome:
    """Profit of a tariff by component."""

    usage_fee: float
    entry_fee: float
    marginal_cost: float
    entrants: float
    entry_profit: float
    sales_profit: float

    @property
    def profit(self) -> float:
        return self.entry_profit + self.sales_profit


def evaluate_tariff(
    buyers: Sequence[BuyerType], marginal_cost: float, usage_fee: float, entry_fee: float
) -> TariffOutcome:
    """Profit when each buyer whose surplus covers the entry fee pays it and buys."""
    if marginal_cost < 0 or usage_fee < 0 or entry_fee < 0:
        raise PricingError("Fees and marginal cost must be nonnegative.")
    entering = [b for b in buyers if b.surplus(usage_fee) >= entry_fee - 1e-12]
    entrants = sum(b.count for b in entering)
    sales = sum(b.count * (usage_fee - marginal_cost) * b.quantity(usage_fee) for b in entering)
    return TariffOutcome(usage_fee, entry_fee, marginal_cost, entrants, entrants * entry_fee, sales)


def best_tariff(buyers: Sequence[BuyerType], marginal_cost: float) -> TariffOutcome:
    """The profit-maximising two-part tariff (search over usage fees; the entry fee is the
    surplus of the least-surplus buyer type served)."""
    if not buyers:
        raise PricingError("At least one buyer type is required.")
    top = max(b.demand.intercept for b in buyers)
    best: TariffOutcome | None = None
    for index in range(GRID + 1):
        price = marginal_cost + (top - marginal_cost) * index / GRID
        for member in buyers:
            fee = member.surplus(price)
            if fee <= 0:
                continue
            outcome = evaluate_tariff(buyers, marginal_cost, price, fee)
            if best is None or outcome.profit > best.profit:
                best = outcome
    if best is None:
        raise PricingError("No tariff earns a profit.")
    return best


def profit_by_entry_fee(
    buyers: Sequence[BuyerType], marginal_cost: float, usage_fee: float, fees: Sequence[float]
) -> tuple[TariffOutcome, ...]:
    """The outcome at each entry fee in ``fees`` for a fixed usage fee."""
    return tuple(evaluate_tariff(buyers, marginal_cost, usage_fee, fee) for fee in fees)
