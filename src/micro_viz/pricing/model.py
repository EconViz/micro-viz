"""Renderer-neutral pricing domain models.

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


@dataclass(frozen=True, slots=True)
class IntertemporalOutcome:
    """Prices and quantities of a seller that serves the high-valuation buyers first."""

    first_price: float
    first_quantity: float
    second_price: float
    second_quantity: float
    profit: float


@dataclass(frozen=True, slots=True)
class IntertemporalPricing:
    """Two buyer groups with linear demands (``first`` buys early, ``second`` later) and a
    constant marginal cost: each group is priced where its own ``MR = MC``."""

    first: LinearDemand
    second: LinearDemand
    marginal_cost: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.marginal_cost) or self.marginal_cost < 0:
            raise PricingError("marginal_cost must be finite and nonnegative.")
        if self.second.intercept > self.first.intercept:
            raise PricingError("The later group must value the good less than the early group.")

    def _optimum(self, demand: LinearDemand) -> tuple[float, float]:
        quantity = max((demand.intercept - self.marginal_cost) / (2 * demand.slope), 0.0)
        return quantity, demand.intercept - demand.slope * quantity

    def solve(self) -> IntertemporalOutcome:
        q1, p1 = self._optimum(self.first)
        q2, p2 = self._optimum(self.second)
        profit = (p1 - self.marginal_cost) * q1 + (p2 - self.marginal_cost) * q2
        return IntertemporalOutcome(p1, q1, p2, q2, profit)


@dataclass(frozen=True, slots=True)
class PeakLoadOutcome:
    """Peak-load prices; ``shared_capacity`` is true when both periods use all the capacity."""

    peak_price: float
    peak_quantity: float
    off_peak_price: float
    off_peak_quantity: float
    capacity: float
    shared_capacity: bool


@dataclass(frozen=True, slots=True)
class PeakLoadPricing:
    """Peak and off-peak demands, a running cost ``marginal_cost`` per unit in each period and a
    capacity cost ``capacity_cost`` per unit of capacity. When the off-peak optimum fits within
    peak capacity the whole capacity cost falls on the peak (``MR_P = MC + MC_K``,
    ``MR_O = MC``); otherwise both periods fill capacity and ``MR_P + MR_O = 2 MC + MC_K``."""

    peak: LinearDemand
    off_peak: LinearDemand
    marginal_cost: float
    capacity_cost: float

    def __post_init__(self) -> None:
        for name, value in (
            ("marginal_cost", self.marginal_cost),
            ("capacity_cost", self.capacity_cost),
        ):
            if not math.isfinite(value) or value < 0:
                raise PricingError(f"{name} must be finite and nonnegative.")

    def solve(self) -> PeakLoadOutcome:
        mc, k = self.marginal_cost, self.capacity_cost
        peak_q = max((self.peak.intercept - mc - k) / (2 * self.peak.slope), 0.0)
        off_q = max((self.off_peak.intercept - mc) / (2 * self.off_peak.slope), 0.0)
        shared = off_q > peak_q
        if shared:
            peak_q = off_q = max(
                (self.peak.intercept + self.off_peak.intercept - 2 * mc - k)
                / (2 * (self.peak.slope + self.off_peak.slope)),
                0.0,
            )
        return PeakLoadOutcome(
            peak_price=self.peak.intercept - self.peak.slope * peak_q,
            peak_quantity=peak_q,
            off_peak_price=self.off_peak.intercept - self.off_peak.slope * off_q,
            off_peak_quantity=off_q,
            capacity=max(peak_q, off_q),
            shared_capacity=shared,
        )
