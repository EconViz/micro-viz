"""Renderer-neutral auctions with independent private values.

``n`` bidders draw values independently and uniformly from ``[0, max_value]``. In the
second-price auction bidding the value is a dominant strategy; in the first-price auction the
symmetric equilibrium bid is ``b(v) = (n - 1) v / n``. Both give the seller the expected revenue
``(n - 1) max_value / (n + 1)`` (revenue equivalence).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

STEPS = 2000
"""Midpoint-rule steps of the numeric expected-revenue integral."""


class AuctionError(ValueError):
    """Raised when an auction input is invalid."""


@dataclass(frozen=True, slots=True)
class Auction:
    """``bidders`` symmetric bidders with uniform private values on ``[0, max_value]``."""

    bidders: int
    max_value: float = 1.0

    def __post_init__(self) -> None:
        if self.bidders < 2:
            raise AuctionError("An auction needs at least two bidders.")
        if not math.isfinite(self.max_value) or self.max_value <= 0:
            raise AuctionError("max_value must be finite and positive.")

    def second_price_bid(self, value: float) -> float:
        """Dominant strategy: bid the value."""
        return self._check(value)

    def first_price_bid(self, value: float) -> float:
        """Symmetric equilibrium bid ``(n - 1) v / n`` (shading rises as bidders are fewer)."""
        return (self.bidders - 1) / self.bidders * self._check(value)

    def shading(self, value: float) -> float:
        """Amount a first-price bidder bids below the value."""
        return self._check(value) - self.first_price_bid(value)

    def _check(self, value: float) -> float:
        if not 0 <= value <= self.max_value:
            raise AuctionError("value must lie in [0, max_value].")
        return value

    def win_probability(self, value: float) -> float:
        """Chance of having the highest value: ``(v / max_value)^(n - 1)``."""
        return (self._check(value) / self.max_value) ** (self.bidders - 1)

    @property
    def expected_revenue(self) -> float:
        """Closed form ``(n - 1) max_value / (n + 1)``, common to both formats."""
        return (self.bidders - 1) / (self.bidders + 1) * self.max_value

    def expected_revenue_numeric(self, first_price: bool) -> float:
        """Expected winning price by integrating over the highest value (density
        ``n v^(n-1) / max_value^n``)."""
        n = self.bidders
        total = 0.0
        for i in range(STEPS):
            value = (i + 0.5) / STEPS * self.max_value
            price = self.first_price_bid(value) if first_price else self._second_highest_mean(value)
            density = n * (value / self.max_value) ** (n - 1) / self.max_value
            total += price * density
        return total * self.max_value / STEPS

    def _second_highest_mean(self, highest: float) -> float:
        """Expected second-highest value given the highest: the mean of ``n - 1`` uniforms
        conditioned below ``highest``, taken as the top order statistic."""
        return (self.bidders - 1) / self.bidders * highest

    def expected_profit(self, value: float, first_price: bool) -> float:
        """A bidder's expected profit at its equilibrium bid and value."""
        bid = self.first_price_bid(value) if first_price else self.second_price_bid(value)
        n = self.bidders
        if first_price:
            return self.win_probability(value) * (value - bid)
        # second price: pays the highest rival value when winning; E[price | win] = (n-1)/n v
        return self.win_probability(value) * (value - (n - 1) / n * value)
