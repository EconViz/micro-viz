"""Renderer-neutral short-run perfect competition.

A price-taking firm faces the horizontal demand ``d = P = AR = MR`` and chooses the output
where ``MR = MC`` on the rising part of marginal cost, provided price covers average variable
cost. Notation: ``R = P q`` revenue, ``VC`` variable cost, ``FC`` fixed cost,
``profit = R - VC - FC`` and ``producer surplus = R - VC``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from micro_viz.firm.costs import Cost, CostFunction, CubicCost, PiecewiseCost


class CompetitionError(ValueError):
    """Raised when a competition model or analysis input is invalid."""


class Regime(str, Enum):
    """How the firm fares at a price."""

    PROFIT = "profit"
    BREAK_EVEN = "break_even"
    LOSS = "loss"
    SHUTDOWN = "shutdown"


def _price(value: float) -> float:
    price = float(value)
    if not math.isfinite(price) or price < 0:
        raise CompetitionError("The price must be finite and nonnegative.")
    return price


def shutdown_price(cost: CostFunction) -> float:
    """The lowest average variable cost: below this price the firm produces nothing."""
    if isinstance(cost, Cost):
        return cost.shutdown_price()
    if isinstance(cost, CubicCost):
        q = cost.minimum_average_variable_cost_output
        return cost.variable_cost(q) / q if q > 0 else cost.linear
    top = cost.capacity if math.isfinite(cost.capacity) else None
    if top is None:
        raise CompetitionError("Cannot find the lowest AVC of a cost function with no capacity.")
    grid = [top * index / 2000 for index in range(1, 2001)]
    return min(cost.variable_cost(q) / q for q in grid)


def break_even_price(cost: CostFunction) -> float | None:
    """The lowest average total cost, or ``None`` when it is not known in closed form."""
    if isinstance(cost, Cost):
        return cost.breakeven_price()
    if isinstance(cost, CubicCost):
        q = cost.minimum_average_total_cost_output
        return cost.total_cost(q) / q
    return None


def profit_maximizing_output(cost: CostFunction, price: float) -> float:
    """Output where ``P = MC`` on the rising part of MC, before the shutdown rule.

    Zero when price lies below marginal cost everywhere.
    """
    value = _price(price)
    if isinstance(cost, Cost):
        return cost.output_at_price(value)
    if isinstance(cost, CubicCost):
        b, c, d = cost.linear, cost.quadratic, cost.cubic
        discriminant = 4 * c * c - 12 * d * (b - value)
        if discriminant < 0:
            return 0.0
        return max(0.0, (-2 * c + math.sqrt(discriminant)) / (6 * d))
    if isinstance(cost, PiecewiseCost):
        return cost.output_at_price(value)
    raise CompetitionError("Unsupported cost function; use CubicCost or PiecewiseCost.")


@dataclass(frozen=True, slots=True)
class CompetitiveOutcome:
    """The price-taking firm's choice at one price."""

    cost: CostFunction
    price: float
    output: float
    regime: Regime
    total_revenue: float
    variable_cost: float
    fixed_cost: float
    total_cost: float
    profit: float
    producer_surplus: float
    average_total_cost: float | None
    average_variable_cost: float | None
    shutdown_price: float
    break_even_price: float | None

    def to_dict(self) -> dict[str, object]:
        """Serialize the outcome with the cost model and sign conventions."""
        return {
            "cost": self.cost.to_dict(),
            "price": self.price,
            "output": self.output,
            "regime": self.regime.value,
            "total_revenue": self.total_revenue,
            "variable_cost": self.variable_cost,
            "fixed_cost": self.fixed_cost,
            "total_cost": self.total_cost,
            "profit": self.profit,
            "producer_surplus": self.producer_surplus,
            "average_total_cost": self.average_total_cost,
            "average_variable_cost": self.average_variable_cost,
            "shutdown_price": self.shutdown_price,
            "break_even_price": self.break_even_price,
            "convention": "profit = R - VC - FC; producer surplus = R - VC",
        }


def solve_competitive_firm(
    cost: CostFunction, price: float, *, tolerance: float = 1e-9
) -> CompetitiveOutcome:
    """Solve the firm's output at ``price``.

    The firm produces where ``P = MC`` if ``P`` covers AVC there, otherwise nothing
    (``SHUTDOWN``, with profit ``-FC``). With output, profit is positive, zero within
    ``tolerance`` (``BREAK_EVEN``) or negative (``LOSS``, kept because P covers AVC).
    """
    value = _price(price)
    low = shutdown_price(cost)
    quantity = profit_maximizing_output(cost, value)
    average_variable = cost.average_variable_cost(quantity) if quantity > 0 else None
    shut = quantity <= 0 or (average_variable is not None and value < average_variable - tolerance)
    if isinstance(cost, Cost | CubicCost | PiecewiseCost) and value < low - tolerance:
        shut = True
    if shut:
        return CompetitiveOutcome(
            cost=cost,
            price=value,
            output=0.0,
            regime=Regime.SHUTDOWN,
            total_revenue=0.0,
            variable_cost=0.0,
            fixed_cost=cost.fixed_cost,
            total_cost=cost.fixed_cost,
            profit=-cost.fixed_cost,
            producer_surplus=0.0,
            average_total_cost=None,
            average_variable_cost=None,
            shutdown_price=low,
            break_even_price=break_even_price(cost),
        )
    revenue = value * quantity
    variable = cost.variable_cost(quantity)
    total = cost.fixed_cost + variable
    profit = revenue - total
    scale = max(1.0, abs(revenue), abs(total))
    if abs(profit) <= tolerance * scale:
        regime = Regime.BREAK_EVEN
    else:
        regime = Regime.PROFIT if profit > 0 else Regime.LOSS
    return CompetitiveOutcome(
        cost=cost,
        price=value,
        output=quantity,
        regime=regime,
        total_revenue=revenue,
        variable_cost=variable,
        fixed_cost=cost.fixed_cost,
        total_cost=total,
        profit=profit,
        producer_surplus=revenue - variable,
        average_total_cost=total / quantity,
        average_variable_cost=variable / quantity,
        shutdown_price=low,
        break_even_price=break_even_price(cost),
    )


@dataclass(frozen=True, slots=True)
class FirmSupply:
    """A firm's short-run supply: the part of MC above the lowest AVC."""

    cost: CostFunction

    @property
    def shutdown_price(self) -> float:
        return shutdown_price(self.cost)

    def quantity(self, price: float) -> float:
        """Output supplied at ``price`` (zero below the shutdown price)."""
        return solve_competitive_firm(self.cost, price).output

    def curve(self, price_max: float, samples: int = 101) -> tuple[tuple[float, float], ...]:
        """Points ``(quantity, price)`` of the supply curve from the shutdown price up to
        ``price_max``, rising in price."""
        low = self.shutdown_price
        if price_max <= low:
            raise CompetitionError("price_max must exceed the shutdown price.")
        if isinstance(samples, bool) or not isinstance(samples, int) or samples < 2:
            raise CompetitionError("samples must be an integer of at least 2.")
        prices = [low + (price_max - low) * index / (samples - 1) for index in range(samples)]
        return tuple((self.quantity(p), p) for p in prices)


@dataclass(frozen=True, slots=True)
class IndustrySupply:
    """The horizontal sum of firm supply curves."""

    firms: tuple[CostFunction, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "firms", tuple(self.firms))
        if not self.firms:
            raise CompetitionError("An industry needs at least one firm.")

    @property
    def shutdown_prices(self) -> tuple[float, ...]:
        """Each firm's shutdown price, in the order of the firms."""
        return tuple(shutdown_price(firm) for firm in self.firms)

    def quantity(self, price: float) -> float:
        """Industry output at ``price``: the sum of the firms' outputs."""
        return sum(solve_competitive_firm(firm, price).output for firm in self.firms)

    def curve(self, price_max: float, samples: int = 201) -> tuple[tuple[float, float], ...]:
        """Points ``(quantity, price)`` rising in price; where a firm enters at its shutdown
        price the curve has a horizontal step (two points at that price)."""
        start = min(self.shutdown_prices)
        if price_max <= start:
            raise CompetitionError("price_max must exceed the lowest shutdown price.")
        if isinstance(samples, bool) or not isinstance(samples, int) or samples < 2:
            raise CompetitionError("samples must be an integer of at least 2.")
        grid = [start + (price_max - start) * index / (samples - 1) for index in range(samples)]
        entries = sorted(set(self.shutdown_prices))
        points: list[tuple[float, float]] = []
        for price in sorted({*grid, *entries}):
            if price in entries:
                before = sum(
                    solve_competitive_firm(firm, price).output
                    for firm in self.firms
                    if shutdown_price(firm) < price
                )
                points.append((before, price))
            points.append((self.quantity(price), price))
        return tuple(points)


@dataclass(frozen=True, slots=True)
class LinearDemand:
    """Market demand ``P = a - b Q`` (``a > 0``, ``b > 0``)."""

    intercept: float
    slope: float

    def __post_init__(self) -> None:
        for name in ("intercept", "slope"):
            if not math.isfinite(getattr(self, name)) or getattr(self, name) <= 0:
                raise CompetitionError(f"The demand {name} must be finite and positive.")

    def price(self, quantity: float) -> float:
        """The price at which ``quantity`` is demanded."""
        return self.intercept - self.slope * quantity

    def quantity(self, price: float) -> float:
        """Quantity demanded at ``price`` (zero above the intercept)."""
        return max(0.0, (self.intercept - price) / self.slope)

    @property
    def quantity_intercept(self) -> float:
        """Quantity demanded at a zero price."""
        return self.intercept / self.slope

    def to_dict(self) -> dict[str, object]:
        return {"equation": "P = a - b Q", "a": self.intercept, "b": self.slope}


@dataclass(frozen=True, slots=True)
class RevenueCostPoint:
    """Revenue, cost and profit at one output."""

    output: float
    total_revenue: float
    total_cost: float
    profit: float


@dataclass(frozen=True, slots=True)
class RevenueCostAnalysis:
    """TR, TC and profit against output at one price.

    The profit-maximizing output is where the slopes of TR (the price) and TC (marginal cost)
    are equal; the break-even outputs are where profit crosses zero.
    """

    cost: CostFunction
    price: float
    output_range: tuple[float, float]
    points: tuple[RevenueCostPoint, ...]
    profit_maximizing_output: float
    break_even_outputs: tuple[float, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "cost": self.cost.to_dict(),
            "price": self.price,
            "output_range": list(self.output_range),
            "profit_maximizing_output": self.profit_maximizing_output,
            "break_even_outputs": list(self.break_even_outputs),
            "points": [[p.output, p.total_revenue, p.total_cost, p.profit] for p in self.points],
        }


def analyze_revenue_cost(
    cost: CostFunction,
    price: float,
    *,
    output_range: tuple[float, float],
    samples: int = 201,
) -> RevenueCostAnalysis:
    """Sample ``R = P q``, ``TC`` and profit over ``output_range``."""
    value = _price(price)
    start, end = (float(item) for item in output_range)
    if not math.isfinite(start) or not math.isfinite(end) or start < 0 or end <= start:
        raise CompetitionError("The output range must be finite, nonnegative and increasing.")
    if isinstance(samples, bool) or not isinstance(samples, int) or samples < 2:
        raise CompetitionError("samples must be an integer of at least 2.")
    grid = [start + (end - start) * index / (samples - 1) for index in range(samples)]

    def profit(q: float) -> float:
        return value * q - cost.total_cost(q)

    points = tuple(RevenueCostPoint(q, value * q, cost.total_cost(q), profit(q)) for q in grid)
    best = profit_maximizing_output(cost, value)
    roots: list[float] = []
    for low, high in zip(grid, grid[1:], strict=False):
        a, b = profit(low), profit(high)
        if a == 0:
            roots.append(low)
        elif a * b < 0:
            lo, hi = low, high
            for _ in range(80):
                mid = (lo + hi) / 2
                if profit(lo) * profit(mid) <= 0:
                    hi = mid
                else:
                    lo = mid
            roots.append((lo + hi) / 2)
    if profit(grid[-1]) == 0:
        roots.append(grid[-1])
    return RevenueCostAnalysis(
        cost=cost,
        price=value,
        output_range=(start, end),
        points=points,
        profit_maximizing_output=best,
        break_even_outputs=tuple(roots),
    )


__all__ = [
    "CompetitionError",
    "CompetitiveOutcome",
    "FirmSupply",
    "IndustrySupply",
    "LinearDemand",
    "Regime",
    "RevenueCostAnalysis",
    "RevenueCostPoint",
    "analyze_revenue_cost",
    "break_even_price",
    "profit_maximizing_output",
    "shutdown_price",
    "solve_competitive_firm",
]
