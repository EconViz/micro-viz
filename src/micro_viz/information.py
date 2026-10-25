"""Renderer-neutral models of asymmetric information.

* Lemons: demand for quality ``q`` is ``P = a_q - b Q``; sellers of quality ``q`` need
  ``P >= c_q + d Q``. Uninformed buyers value the average quality, so demand for the mix with
  high-quality share ``s`` has intercept ``s a_H + (1 - s) a_L``.
* Signaling: education ``y`` costs ``k y`` with ``k_L > k_H`` and pays the wage gap ``B``.
* Moral hazard: insurance covering the share ``k`` of cost lowers the price to ``(1 - k) MC``.
* Principal-agent: a bonus on a report ``R`` of capacity ``A`` pays ``rate_r R`` plus ``rate_u
  (A - R)`` when ``R <= A`` and ``rate_r R - rate_o (R - A)`` beyond.
* Efficiency wages: the no-shirking wage ``w = n0 + n1 L`` rises with employment.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from micro_viz.competition import CompetitionError, LinearDemand


class InformationError(CompetitionError):
    """Raised when an information-economics input is invalid."""


def _positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0:
        raise InformationError(f"{name} must be finite and positive.")


@dataclass(frozen=True, slots=True)
class LemonsMarket:
    """High- and low-quality demands (same slope) and the sellers' reservation lines."""

    demand_high: LinearDemand
    demand_low: LinearDemand
    cost_high: float
    cost_low: float
    supply_slope: float

    def __post_init__(self) -> None:
        if self.demand_high.intercept <= self.demand_low.intercept:
            raise InformationError("High quality must be valued above low quality.")
        if self.cost_high <= self.cost_low or self.cost_low < 0:
            raise InformationError("Need 0 <= cost_low < cost_high.")
        _positive("supply_slope", self.supply_slope)

    def mixed_demand(self, high_share: float) -> LinearDemand:
        """Demand of buyers who cannot tell quality apart."""
        if not 0 <= high_share <= 1:
            raise InformationError("high_share must lie in [0, 1].")
        intercept = (
            high_share * self.demand_high.intercept + (1 - high_share) * self.demand_low.intercept
        )
        slope = high_share * self.demand_high.slope + (1 - high_share) * self.demand_low.slope
        return LinearDemand(intercept, slope)

    def high_quality_sells(self, high_share: float) -> bool:
        """Whether the mixed demand starts above the high-quality sellers' reservation price."""
        return self.mixed_demand(high_share).intercept > self.cost_high

    @property
    def critical_share(self) -> float:
        """The high-quality share below which high quality is driven out."""
        high, low = self.demand_high.intercept, self.demand_low.intercept
        return min(max((self.cost_high - low) / (high - low), 0.0), 1.0)


@dataclass(frozen=True, slots=True)
class Signaling:
    """Wage gap ``B`` paid for the signal ``y`` and the per-unit costs ``cost_low > cost_high``."""

    wage_gap: float
    cost_low: float
    cost_high: float

    def __post_init__(self) -> None:
        _positive("wage_gap", self.wage_gap)
        _positive("cost_high", self.cost_high)
        if self.cost_low <= self.cost_high:
            raise InformationError("cost_low must exceed cost_high.")

    @property
    def low_ceiling(self) -> float:
        """The largest signal the low-cost-disadvantaged group would still buy."""
        return self.wage_gap / self.cost_low

    @property
    def high_ceiling(self) -> float:
        return self.wage_gap / self.cost_high

    def separating(self, signal: float) -> bool:
        """Whether ``signal`` is bought only by the high group."""
        return self.low_ceiling <= signal <= self.high_ceiling

    def pooling(self, signal: float) -> bool:
        """Whether both groups find ``signal`` worth buying (a pooling signal)."""
        return 0 <= signal <= self.low_ceiling

    @property
    def separating_signal(self) -> float:
        """The midpoint of the separating range."""
        return (self.low_ceiling + self.high_ceiling) / 2


@dataclass(frozen=True, slots=True)
class MoralHazardOutcome:
    """Efficient and insured quantities of a service."""

    efficient_quantity: float
    insured_quantity: float
    deadweight_loss: float


@dataclass(frozen=True, slots=True)
class MoralHazard:
    """Demand for a service with marginal cost ``marginal_cost`` when insurance pays the share
    ``coverage`` of it."""

    demand: LinearDemand
    marginal_cost: float
    coverage: float

    def __post_init__(self) -> None:
        _positive("marginal_cost", self.marginal_cost)
        if not 0 < self.coverage < 1:
            raise InformationError("coverage must lie in (0, 1).")
        if self.marginal_cost >= self.demand.intercept:
            raise InformationError("marginal_cost must lie below the demand intercept.")

    @property
    def insured_price(self) -> float:
        return (1 - self.coverage) * self.marginal_cost

    def solve(self) -> MoralHazardOutcome:
        efficient = (self.demand.intercept - self.marginal_cost) / self.demand.slope
        insured = (self.demand.intercept - self.insured_price) / self.demand.slope
        loss = 0.5 * (insured - efficient) * (self.marginal_cost - self.insured_price)
        return MoralHazardOutcome(efficient, insured, loss)


@dataclass(frozen=True, slots=True)
class BonusSchedule:
    """Bonus on reported size ``R`` given actual capacity ``A``; truthful reporting is optimal
    when ``over_rate > report_rate > under_rate``."""

    report_rate: float
    under_rate: float
    over_rate: float

    def __post_init__(self) -> None:
        _positive("report_rate", self.report_rate)
        if not 0 <= self.under_rate < self.report_rate < self.over_rate:
            raise InformationError("Need 0 <= under_rate < report_rate < over_rate.")

    def bonus(self, report: float, actual: float) -> float:
        if report <= actual:
            return self.report_rate * report + self.under_rate * (actual - report)
        return self.report_rate * report - self.over_rate * (report - actual)

    def best_report(self, actual: float) -> float:
        """The report that maximises the bonus: the truth."""
        return actual


@dataclass(frozen=True, slots=True)
class EfficiencyWageOutcome:
    """Equilibrium with a no-shirking constraint."""

    wage: float
    employment: float
    labor_supplied: float
    competitive_wage: float
    competitive_employment: float

    @property
    def unemployment(self) -> float:
        return self.labor_supplied - self.employment


@dataclass(frozen=True, slots=True)
class EfficiencyWage:
    """Labor demand ``w = a - b L``, supply ``w = s0 + s1 L`` and the no-shirking wage
    ``w = n0 + n1 L`` (workers shirk less when jobs are scarce, so it rises with employment)."""

    demand_intercept: float
    demand_slope: float
    supply_intercept: float
    supply_slope: float
    shirk_intercept: float
    shirk_slope: float

    def __post_init__(self) -> None:
        for name in ("demand_intercept", "demand_slope", "supply_slope", "shirk_slope"):
            _positive(name, getattr(self, name))
        if self.supply_intercept < 0 or self.shirk_intercept < 0:
            raise InformationError("Intercepts must be nonnegative.")

    def solve(self) -> EfficiencyWageOutcome:
        a, b = self.demand_intercept, self.demand_slope
        employment = (a - self.shirk_intercept) / (b + self.shirk_slope)
        wage = a - b * employment
        competitive_l = (a - self.supply_intercept) / (b + self.supply_slope)
        competitive_w = a - b * competitive_l
        if employment <= 0:
            raise InformationError("No-shirking wage lies above demand.")
        supplied = max((wage - self.supply_intercept) / self.supply_slope, 0.0)
        if wage < competitive_w:
            raise InformationError("The no-shirking wage must exceed the competitive wage.")
        return EfficiencyWageOutcome(wage, employment, supplied, competitive_w, competitive_l)
