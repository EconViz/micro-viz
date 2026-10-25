"""Renderer-neutral choice under uncertainty: expected utility, risk premium and risk-return.

Utility of income is ``u(I) = I^e`` with exponent ``e``: concave (``e < 1``, risk averse), linear
(``e = 1``, risk neutral) or convex (``e > 1``, risk loving). A gamble pays ``low`` or ``high``
with probability ``p`` of ``high``. In the income-standard-deviation plane an investor has
mean-variance utility ``U = mean - (lambda / 2) sd^2`` and faces the line ``mean = rf + s sd``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

Point = tuple[float, float]


class UncertaintyError(ValueError):
    """Raised when an uncertainty input is invalid."""


def _positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0:
        raise UncertaintyError(f"{name} must be finite and positive.")


@dataclass(frozen=True, slots=True)
class IncomeUtility:
    """Utility of income ``u(I) = I^exponent``."""

    exponent: float

    def __post_init__(self) -> None:
        _positive("exponent", self.exponent)

    def utility(self, income: float) -> float:
        if income < 0:
            raise UncertaintyError("Income must be nonnegative.")
        return float(income**self.exponent)

    def inverse(self, utility: float) -> float:
        return float(utility ** (1.0 / self.exponent))

    @property
    def attitude(self) -> str:
        """``"averse"``, ``"neutral"`` or ``"loving"``."""
        if math.isclose(self.exponent, 1.0):
            return "neutral"
        return "averse" if self.exponent < 1.0 else "loving"


@dataclass(frozen=True, slots=True)
class Gamble:
    """Income ``high`` with probability ``probability``, otherwise ``low``."""

    low: float
    high: float
    probability: float = 0.5

    def __post_init__(self) -> None:
        if (
            not (math.isfinite(self.low) and math.isfinite(self.high))
            or not 0 <= self.low < self.high
        ):
            raise UncertaintyError("Need 0 <= low < high.")
        if not 0 < self.probability < 1:
            raise UncertaintyError("probability must lie in (0, 1).")

    @property
    def expected_income(self) -> float:
        return self.probability * self.high + (1 - self.probability) * self.low

    def expected_utility(self, utility: IncomeUtility) -> float:
        return self.probability * utility.utility(self.high) + (
            1 - self.probability
        ) * utility.utility(self.low)

    def certainty_equivalent(self, utility: IncomeUtility) -> float:
        """The sure income with the same utility as the gamble."""
        return utility.inverse(self.expected_utility(utility))

    def risk_premium(self, utility: IncomeUtility) -> float:
        """Expected income less the certainty equivalent (positive for a risk-averse person)."""
        return self.expected_income - self.certainty_equivalent(utility)

    def chord(self, utility: IncomeUtility) -> tuple[Point, Point]:
        """The chord of ``u`` between the two outcomes: expected utility lies on it."""
        return (
            (self.low, utility.utility(self.low)),
            (self.high, utility.utility(self.high)),
        )


@dataclass(frozen=True, slots=True)
class MeanVarianceInvestor:
    """Utility ``U = mean - (risk_aversion / 2) sd^2``: indifference curves
    ``mean = U + (risk_aversion / 2) sd^2`` are steeper for larger ``risk_aversion``."""

    risk_aversion: float

    def __post_init__(self) -> None:
        _positive("risk_aversion", self.risk_aversion)

    def indifference_mean(self, level: float, sd: float) -> float:
        return level + 0.5 * self.risk_aversion * sd**2

    def utility(self, mean: float, sd: float) -> float:
        return mean - 0.5 * self.risk_aversion * sd**2

    def slope(self, sd: float) -> float:
        """Marginal rate of substitution of mean for risk: ``lambda sd``."""
        return self.risk_aversion * sd


@dataclass(frozen=True, slots=True)
class RiskReturnLine:
    """The risk-return budget line ``mean = risk_free + price_of_risk * sd``."""

    risk_free: float
    price_of_risk: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.risk_free) or self.risk_free < 0:
            raise UncertaintyError("risk_free must be finite and nonnegative.")
        _positive("price_of_risk", self.price_of_risk)

    def mean(self, sd: float) -> float:
        return self.risk_free + self.price_of_risk * sd

    def choice(self, investor: MeanVarianceInvestor) -> Point:
        """The tangency ``(sd, mean)``: ``sd = price_of_risk / risk_aversion``."""
        sd = self.price_of_risk / investor.risk_aversion
        return sd, self.mean(sd)

    def borrows(self, investor: MeanVarianceInvestor, market_sd: float) -> bool:
        """Whether the choice lies beyond the market portfolio ``market_sd`` (leverage)."""
        return self.choice(investor)[0] > market_sd
