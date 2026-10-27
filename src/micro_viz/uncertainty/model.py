"""Renderer-neutral choice-under-uncertainty domain models.

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


GRID = 400
"""Points of the numeric dominance checks and crossing search."""


@dataclass(frozen=True, slots=True)
class StateClaims:
    """Two-state choice: income ``good`` (state 1, probability ``1 - loss_probability``) or
    ``bad`` (state 2). Insurance of ``K`` costs ``premium_rate K`` and pays ``K`` in the bad
    state, so consumption is ``(good - q K, bad + (1 - q) K)`` on the budget line
    ``(1 - q) C1 + q C2 = (1 - q) good + q bad``. Utility is ``u(C) = C^exponent`` with
    ``exponent < 1``; the tangency gives ``C2 / C1 = [pi (1 - q) / ((1 - pi) q)]^(1/(1-e))``."""

    good: float
    bad: float
    loss_probability: float
    exponent: float = 0.5

    def __post_init__(self) -> None:
        if (
            not math.isfinite(self.good)
            or not math.isfinite(self.bad)
            or not 0 < self.bad < self.good
        ):
            raise UncertaintyError("Need 0 < bad < good.")
        if not 0 < self.loss_probability < 1:
            raise UncertaintyError("loss_probability must lie in (0, 1).")
        if not 0 < self.exponent < 1:
            raise UncertaintyError("exponent must lie in (0, 1) for a risk-averse chooser.")

    def utility(self, c1: float, c2: float) -> float:
        p = self.loss_probability
        return float((1 - p) * c1**self.exponent + p * c2**self.exponent)

    def wealth(self, premium_rate: float) -> float:
        """Right-hand side of the budget line at ``premium_rate``."""
        return (1 - premium_rate) * self.good + premium_rate * self.bad

    def budget_c2(self, c1: float, premium_rate: float) -> float:
        return (self.wealth(premium_rate) - (1 - premium_rate) * c1) / premium_rate

    def indifference_c2(self, c1: float, level: float) -> float:
        """``C2`` on the indifference curve of utility ``level`` (``nan`` beyond its reach)."""
        rest = level - (1 - self.loss_probability) * c1**self.exponent
        if rest <= 0:
            return math.nan
        return float((rest / self.loss_probability) ** (1.0 / self.exponent))

    def is_fair(self, premium_rate: float) -> bool:
        return math.isclose(premium_rate, self.loss_probability)

    def choice(self, premium_rate: float) -> Point:
        """Optimal ``(C1, C2)`` at the premium rate ``q`` in ``(0, 1)``."""
        if not 0 < premium_rate < 1:
            raise UncertaintyError("premium_rate must lie in (0, 1).")
        p, q = self.loss_probability, premium_rate
        ratio = (p * (1 - q) / ((1 - p) * q)) ** (1.0 / (1 - self.exponent))
        c1 = self.wealth(q) / ((1 - q) + q * ratio)
        return c1, ratio * c1

    def coverage(self, premium_rate: float) -> float:
        """Insurance bought: ``K = (bad-state consumption) - bad``."""
        return self.choice(premium_rate)[1] - self.bad


@dataclass(frozen=True, slots=True)
class UniformLottery:
    """Income uniform on ``[low, high]``."""

    low: float
    high: float

    def __post_init__(self) -> None:
        if not (math.isfinite(self.low) and math.isfinite(self.high)) or self.high <= self.low:
            raise UncertaintyError("Need low < high.")

    @property
    def mean(self) -> float:
        return (self.low + self.high) / 2

    def cdf(self, income: float) -> float:
        return min(max((income - self.low) / (self.high - self.low), 0.0), 1.0)

    def integrated_cdf(self, income: float) -> float:
        """``integral of F from -inf to income`` (the area used by second-order dominance)."""
        if income <= self.low:
            return 0.0
        top = min(income, self.high)
        area = (top - self.low) ** 2 / (2 * (self.high - self.low))
        return area + max(income - self.high, 0.0)


def first_order_dominates(better: UniformLottery, worse: UniformLottery) -> bool:
    """``better`` first-order dominates ``worse`` when its CDF is nowhere above (checked on a
    grid spanning both supports)."""
    low, high = min(better.low, worse.low), max(better.high, worse.high)
    return all(
        better.cdf(low + (high - low) * i / GRID)
        <= worse.cdf(low + (high - low) * i / GRID) + 1e-12
        for i in range(GRID + 1)
    )


def second_order_dominates(better: UniformLottery, worse: UniformLottery) -> bool:
    """``better`` second-order dominates ``worse`` when the area under its CDF is nowhere larger."""
    low, high = min(better.low, worse.low), max(better.high, worse.high)
    return all(
        better.integrated_cdf(low + (high - low) * i / GRID)
        <= worse.integrated_cdf(low + (high - low) * i / GRID) + 1e-12
        for i in range(GRID + 1)
    )


def cdf_crossing(a: UniformLottery, b: UniformLottery) -> float | None:
    """The income where the two CDFs cross inside both supports (``None`` if they do not)."""
    low, high = max(a.low, b.low), min(a.high, b.high)
    if low >= high:
        return None

    def sign(x: float) -> float:
        return a.cdf(x) - b.cdf(x)

    if sign(low) * sign(high) > 0:
        return None
    left, right = low, high
    for _ in range(80):
        middle = (left + right) / 2
        if sign(left) * sign(middle) <= 0:
            right = middle
        else:
            left = middle
    return (left + right) / 2


@dataclass(frozen=True, slots=True)
class TwoAssetFrontier:
    """Mean-variance frontier of two risky assets with weight ``w`` on asset 1:
    ``mean = w m1 + (1 - w) m2`` and
    ``sd^2 = w^2 s1^2 + (1 - w)^2 s2^2 + 2 w (1 - w) rho s1 s2``."""

    mean_1: float
    sd_1: float
    mean_2: float
    sd_2: float
    correlation: float

    def __post_init__(self) -> None:
        _positive("sd_1", self.sd_1)
        _positive("sd_2", self.sd_2)
        if not -1 < self.correlation < 1:
            raise UncertaintyError("correlation must lie in (-1, 1).")
        if self.mean_1 == self.mean_2:
            raise UncertaintyError("The assets must differ in mean.")

    def portfolio(self, weight: float) -> Point:
        """``(sd, mean)`` of the portfolio with ``weight`` on asset 1."""
        w = weight
        variance = (
            w**2 * self.sd_1**2
            + (1 - w) ** 2 * self.sd_2**2
            + 2 * w * (1 - w) * self.correlation * self.sd_1 * self.sd_2
        )
        return math.sqrt(max(variance, 0.0)), w * self.mean_1 + (1 - w) * self.mean_2

    @property
    def minimum_variance_weight(self) -> float:
        cov = self.correlation * self.sd_1 * self.sd_2
        return (self.sd_2**2 - cov) / (self.sd_1**2 + self.sd_2**2 - 2 * cov)

    def minimum_variance(self) -> Point:
        return self.portfolio(self.minimum_variance_weight)

    def curve(self, low: float, high: float, samples: int = 80) -> tuple[Point, ...]:
        return tuple(self.portfolio(low + (high - low) * i / (samples - 1)) for i in range(samples))
