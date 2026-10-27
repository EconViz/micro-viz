"""Renderer-neutral advertising model for a monopolist.

Advertising costs ``A`` (a fixed outlay) and shifts demand outward. With demand
``P = a - b Q``, constant marginal cost ``c`` and fixed cost ``F`` the monopolist produces where
``MR = MC``; ``AC = c + F / Q`` and, after advertising, ``AC' = c + (F + A) / Q`` (cost rises at
every output while the average-revenue curve shifts out).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from micro_viz.competition import CompetitionError, LinearDemand


class AdvertisingError(CompetitionError):
    """Raised when an advertising input is invalid."""


@dataclass(frozen=True, slots=True)
class AdvertisingOutcome:
    """Optimum of one regime."""

    quantity: float
    price: float
    average_cost: float
    profit: float


@dataclass(frozen=True, slots=True)
class AdvertisingDecision:
    """Baseline and advertised demand, marginal cost, fixed cost and advertising spending."""

    baseline: LinearDemand
    advertised: LinearDemand
    marginal_cost: float
    fixed_cost: float
    advertising_cost: float

    def __post_init__(self) -> None:
        for name in ("marginal_cost", "fixed_cost", "advertising_cost"):
            value = getattr(self, name)
            if not math.isfinite(value) or value < 0:
                raise AdvertisingError(f"{name} must be finite and nonnegative.")
        if self.advertised.intercept < self.baseline.intercept:
            raise AdvertisingError("Advertising must not lower the demand intercept.")
        if self.marginal_cost >= self.baseline.intercept:
            raise AdvertisingError("marginal_cost must lie below the demand intercept.")

    def _solve(self, demand: LinearDemand, outlay: float) -> AdvertisingOutcome:
        quantity = max((demand.intercept - self.marginal_cost) / (2 * demand.slope), 0.0)
        price = demand.intercept - demand.slope * quantity
        average = self.marginal_cost + outlay / quantity if quantity > 0 else math.inf
        profit = (price - self.marginal_cost) * quantity - outlay
        return AdvertisingOutcome(quantity, price, average, profit)

    def before(self) -> AdvertisingOutcome:
        return self._solve(self.baseline, self.fixed_cost)

    def after(self) -> AdvertisingOutcome:
        return self._solve(self.advertised, self.fixed_cost + self.advertising_cost)

    @property
    def worthwhile(self) -> bool:
        """Whether advertising raises profit."""
        return self.after().profit > self.before().profit

    def average_cost(self, quantity: float, advertised: bool = False) -> float:
        """``AC`` (or ``AC'``) at a positive output."""
        if quantity <= 0:
            raise AdvertisingError("quantity must be positive.")
        outlay = self.fixed_cost + (self.advertising_cost if advertised else 0.0)
        return self.marginal_cost + outlay / quantity
