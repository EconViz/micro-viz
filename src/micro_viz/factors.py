"""Renderer-neutral factor-market models: monopsony, union wage setting and the two-sector market.

Linear forms throughout. A buyer of an input faces the supply (average expenditure) curve
``AE: w = s0 + s1 L`` and values the input at ``MV: w = v0 - v1 L`` (marginal revenue product);
its marginal expenditure is ``ME: w = s0 + 2 s1 L``. A competitive buyer takes the wage as given
(``ME = AE``); a monopsonist hires where ``ME = MV``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from micro_viz.competition import CompetitionError


class FactorError(CompetitionError):
    """Raised when a factor-market input is invalid."""


def _positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0:
        raise FactorError(f"{name} must be finite and positive.")


@dataclass(frozen=True, slots=True)
class LinearSupply:
    """Input supply ``w = intercept + slope L``; also the average expenditure of a monopsonist."""

    intercept: float
    slope: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.intercept) or self.intercept < 0:
            raise FactorError("Supply intercept must be finite and nonnegative.")
        _positive("slope", self.slope)

    def wage(self, quantity: float) -> float:
        return self.intercept + self.slope * quantity

    def marginal_expenditure(self, quantity: float) -> float:
        return self.intercept + 2 * self.slope * quantity

    def quantity(self, wage: float) -> float:
        return max((wage - self.intercept) / self.slope, 0.0)

    def elasticity(self, quantity: float) -> float:
        """Supply elasticity ``(dL/dw)(w/L)`` at a positive ``quantity``."""
        return self.wage(quantity) / (self.slope * quantity)


@dataclass(frozen=True, slots=True)
class LinearValue:
    """Marginal value (or MRP) ``w = intercept - slope L`` of the input."""

    intercept: float
    slope: float

    def __post_init__(self) -> None:
        _positive("intercept", self.intercept)
        _positive("slope", self.slope)

    def value(self, quantity: float) -> float:
        return self.intercept - self.slope * quantity

    @property
    def quantity_intercept(self) -> float:
        return self.intercept / self.slope


@dataclass(frozen=True, slots=True)
class MonopsonyOutcome:
    """Competitive and monopsony outcomes of one input market."""

    quantity: float
    wage: float
    marginal_expenditure: float
    marginal_value: float
    competitive_quantity: float
    competitive_wage: float
    transfer: float
    deadweight_loss: float


@dataclass(frozen=True, slots=True)
class Monopsonist:
    """A single buyer facing ``supply`` and valuing the input at ``value``."""

    supply: LinearSupply
    value: LinearValue

    def __post_init__(self) -> None:
        if self.supply.intercept >= self.value.intercept:
            raise FactorError("Supply must start below the value curve for any trade.")

    def competitive(self) -> tuple[float, float]:
        """``(quantity, wage)`` where the value curve meets supply."""
        quantity = (self.value.intercept - self.supply.intercept) / (
            self.supply.slope + self.value.slope
        )
        return quantity, self.supply.wage(quantity)

    def solve(self) -> MonopsonyOutcome:
        """Hire where ``ME = MV``; pay the supply price at that quantity."""
        quantity = (self.value.intercept - self.supply.intercept) / (
            2 * self.supply.slope + self.value.slope
        )
        wage = self.supply.wage(quantity)
        competitive_q, competitive_w = self.competitive()
        marginal_value = self.value.value(quantity)
        return MonopsonyOutcome(
            quantity=quantity,
            wage=wage,
            marginal_expenditure=self.supply.marginal_expenditure(quantity),
            marginal_value=marginal_value,
            competitive_quantity=competitive_q,
            competitive_wage=competitive_w,
            transfer=(competitive_w - wage) * quantity,
            deadweight_loss=0.5 * (competitive_q - quantity) * (marginal_value - wage),
        )


@dataclass(frozen=True, slots=True)
class UnionOutcome:
    """A union's chosen point on the labour-demand curve."""

    employment: float
    wage: float
    wage_bill: float
    rent: float
    competitive_employment: float
    competitive_wage: float


@dataclass(frozen=True, slots=True)
class UnionWageSetting:
    """Labour ``demand`` (the firm's MRP) and member ``supply``; the union picks a wage on the
    demand curve (default: the wage that maximises the wage bill)."""

    demand: LinearValue
    supply: LinearSupply

    def solve(self, wage: float | None = None) -> UnionOutcome:
        chosen = self.demand.intercept / 2 if wage is None else wage
        if not 0 < chosen <= self.demand.intercept:
            raise FactorError("wage must lie in (0, demand intercept].")
        employment = max((self.demand.intercept - chosen) / self.demand.slope, 0.0)
        workers = min(employment, self.supply.quantity(chosen))
        rent = chosen * workers - _area_under_supply(self.supply, workers)
        competitive_q = (self.demand.intercept - self.supply.intercept) / (
            self.supply.slope + self.demand.slope
        )
        return UnionOutcome(
            employment=workers,
            wage=chosen,
            wage_bill=chosen * workers,
            rent=rent,
            competitive_employment=competitive_q,
            competitive_wage=self.supply.wage(competitive_q),
        )


def _area_under_supply(supply: LinearSupply, quantity: float) -> float:
    return supply.intercept * quantity + 0.5 * supply.slope * quantity**2


@dataclass(frozen=True, slots=True)
class TwoSectorOutcome:
    """Employment and wages in an unionised and a competitive sector."""

    union_wage: float
    employment_1: float
    employment_2: float
    wage_2: float
    competitive_wage: float
    competitive_employment_1: float
    competitive_employment_2: float


@dataclass(frozen=True, slots=True)
class TwoSectorLabor:
    """Fixed labour force ``total`` split between sector 1 (demand ``demand_1``) and sector 2
    (demand ``demand_2``). Competitive wages equalise; a union wage in sector 1 above that level
    shrinks sector-1 employment and pushes the displaced workers into sector 2."""

    demand_1: LinearValue
    demand_2: LinearValue
    total: float

    def __post_init__(self) -> None:
        _positive("total", self.total)

    def competitive(self) -> tuple[float, float, float]:
        """``(wage, L1, L2)`` with ``MRP1(L1) = MRP2(total - L1)``."""
        a1, b1, a2, b2 = (
            self.demand_1.intercept,
            self.demand_1.slope,
            self.demand_2.intercept,
            self.demand_2.slope,
        )
        employment_1 = (a1 - a2 + b2 * self.total) / (b1 + b2)
        if not 0 < employment_1 < self.total:
            raise FactorError("Both sectors must employ workers at the competitive wage.")
        return self.demand_1.value(employment_1), employment_1, self.total - employment_1

    def solve(self, union_wage: float) -> TwoSectorOutcome:
        wage, c1, c2 = self.competitive()
        if union_wage < wage:
            raise FactorError("The union wage must be at least the competitive wage.")
        employment_1 = max((self.demand_1.intercept - union_wage) / self.demand_1.slope, 0.0)
        employment_2 = self.total - employment_1
        return TwoSectorOutcome(
            union_wage=union_wage,
            employment_1=employment_1,
            employment_2=employment_2,
            wage_2=self.demand_2.value(employment_2),
            competitive_wage=wage,
            competitive_employment_1=c1,
            competitive_employment_2=c2,
        )
