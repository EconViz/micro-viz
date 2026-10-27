"""Formula-backed market demand domain model.

::

    Demand("P = 100 - Q")          # inverse form: price as a function of quantity
    Demand("Q = 50 - P/2")         # direct form: quantity as a function of price
    Demand("P = 100 - Q^2")        # nonlinear

A straight line (in either form) is also available as the older
:class:`~micro_viz.firm.perfect_competition.LinearDemand` through :attr:`Demand.linear`, and
every model that takes a ``LinearDemand`` takes a linear ``Demand`` too. A curve that is not a
straight line has its marginal revenue from exact derivatives; the direct form is inverted
numerically.
"""

from __future__ import annotations

import math
from collections.abc import Callable

from micro_viz.core.expr import ExprError, Expression
from micro_viz.core.formulas import PRICE, QUANTITY, REGISTRY, parse_formula, render_message
from micro_viz.firm.perfect_competition.model import CompetitionError, LinearDemand

_ROUNDS = 200
_GRID = 401
_REACH = 80


def _say(key: str, language: str | None = None, **fields: object) -> str:
    return render_message(key, language, fields)


class DemandError(CompetitionError):
    """Raised when a demand formula does not describe a downward-sloping demand curve."""


def _bisect(function: Callable[[float], float], low: float, high: float) -> float:
    """The root of a decreasing ``function`` with ``function(low) >= 0 >= function(high)``."""
    for _ in range(_ROUNDS):
        middle = (low + high) / 2
        if middle in (low, high):
            break
        if function(middle) > 0:
            low = middle
        else:
            high = middle
    return (low + high) / 2


class Demand:
    """A downward-sloping demand curve from a formula (see the module docstring).

    ``price(q)`` is the price at which ``q`` is demanded, ``quantity(p)`` the quantity demanded
    at ``p`` (zero above the intercept), ``intercept`` the price at zero quantity and
    ``quantity_intercept`` the quantity at a zero price. ``marginal_revenue(q)`` and
    ``elasticity(q)`` are exact.
    """

    def __init__(self, formula: str | Expression, *, language: str | None = None) -> None:
        expression = (
            formula
            if isinstance(formula, Expression)
            else parse_formula(formula, language=language)
        )
        head = expression.head
        if head not in (PRICE, QUANTITY):
            if head is None:
                raise DemandError(_say("demand.error.no_head", language))
            raise DemandError(_say("demand.error.bad_head", language, name=head))
        expected = QUANTITY if head == PRICE else PRICE
        names = expression.variables
        if names - {expected}:
            raise DemandError(
                _say(
                    "demand.error.variable",
                    language,
                    head=head,
                    expected=expected,
                    names=", ".join(sorted(names - {expected})),
                )
            )
        self._language = language
        self._head = head
        self._source = expression
        self._inverse: Expression | None = None
        self._direct: Expression | None = None
        self._linear: LinearDemand | None = None
        try:
            self._setup(expression)
        except ExprError:
            raise DemandError(_say("demand.error.undefined", language)) from None
        self._check()

    # ---- construction ----
    def _setup(self, expression: Expression) -> None:
        poly = expression.coefficients()
        straight = poly is not None and set(poly) <= {0.0, 1.0}
        if self._head == PRICE:
            self._inverse = expression
            if straight:
                assert poly is not None
                self._make_linear(poly.get(0.0, 0.0), -poly.get(1.0, 0.0))
        else:
            self._direct = expression
            if straight:
                assert poly is not None
                const, slope = poly.get(0.0, 0.0), poly.get(1.0, 0.0)
                if slope >= 0:
                    raise DemandError(_say("demand.error.upward", self._language))
                self._make_linear(-const / slope, -1.0 / slope)
                q = Expression.variable(QUANTITY, REGISTRY)
                self._inverse = self._linear_expression(q)

    def _linear_expression(self, q: Expression) -> Expression:
        assert self._linear is not None
        return self._linear.intercept - self._linear.slope * q

    def _make_linear(self, intercept: float, slope: float) -> None:
        if slope <= 0:
            raise DemandError(_say("demand.error.upward", self._language))
        if intercept <= 0:
            raise DemandError(_say("demand.error.intercept", self._language, value=intercept))
        self._linear = LinearDemand(intercept, slope)
        if self._inverse is None and self._head == PRICE:
            self._inverse = self._source

    def _check(self) -> None:
        if self._linear is not None:
            return
        start = self.price(0.0)
        if not start > 0:
            raise DemandError(_say("demand.error.intercept", self._language, value=start))
        reach = self.quantity_intercept
        grid = [reach * i / (_GRID - 1) for i in range(_GRID)]
        values = [self.price(q) for q in grid]
        for left, right, low, high in zip(values, values[1:], grid, grid[1:], strict=False):
            if right > left + 1e-12 * max(1.0, abs(left)):
                raise DemandError(
                    _say("demand.error.not_downward", self._language, low=low, high=high)
                )

    # ---- the curve ----
    @property
    def linear(self) -> LinearDemand | None:
        """The curve as ``P = a - bQ`` when it is a straight line, else ``None``."""
        return self._linear

    @property
    def formula(self) -> str:
        """The formula as written (head included)."""
        return f"{self._head} = {self._source}"

    @property
    def is_linear(self) -> bool:
        return self._linear is not None

    def price(self, quantity: float) -> float:
        """The price at which ``quantity`` is demanded."""
        q = float(quantity)
        if self._linear is not None:
            return self._linear.price(q)
        if self._inverse is not None:
            return self._inverse(q)
        assert self._direct is not None
        direct = self._direct
        top = self._choke_price()
        if q <= direct(0.0):
            if q >= direct(top):
                return _bisect(lambda p: direct(p) - q, 0.0, top)
            return top
        return 0.0

    def _choke_price(self) -> float:
        """The price where the direct form reaches zero quantity."""
        assert self._direct is not None
        direct = self._direct
        high = 1.0
        for _ in range(_REACH):
            if direct(high) <= 0:
                return _bisect(direct, 0.0, high)
            high *= 2
        raise DemandError(_say("demand.error.no_reach", self._language))

    def quantity(self, price: float) -> float:
        """The quantity demanded at ``price`` (zero at or above the intercept)."""
        p = float(price)
        if self._linear is not None:
            return self._linear.quantity(p)
        if self._direct is not None:
            return max(0.0, self._direct(p))
        assert self._inverse is not None
        inverse = self._inverse
        if p >= inverse(0.0):
            return 0.0
        high = 1.0
        for _ in range(_REACH):
            if inverse(high) <= p:
                return _bisect(lambda q: inverse(q) - p, 0.0, high)
            high *= 2
        raise DemandError(_say("demand.error.no_reach", self._language))

    @property
    def intercept(self) -> float:
        """The price at zero quantity (the choke price)."""
        if self._linear is not None:
            return self._linear.intercept
        if self._inverse is not None:
            return self._inverse(0.0)
        return self._choke_price()

    @property
    def quantity_intercept(self) -> float:
        """The quantity demanded at a zero price."""
        if self._linear is not None:
            return self._linear.quantity_intercept
        if self._direct is not None:
            return max(0.0, self._direct(0.0))
        return self.quantity(0.0)

    def price_slope(self, quantity: float) -> float:
        """``dP/dQ`` at ``quantity`` (negative)."""
        q = float(quantity)
        if self._linear is not None:
            return -self._linear.slope
        if self._inverse is not None:
            return self._inverse.derivative()(q)
        assert self._direct is not None
        return 1.0 / self._direct.derivative()(self.price(q))

    def marginal_revenue(self, quantity: float) -> float:
        """``MR(Q) = P(Q) + Q P'(Q)``."""
        q = float(quantity)
        return self.price(q) + q * self.price_slope(q)

    def elasticity(self, quantity: float) -> float:
        """The price elasticity ``e = (P / Q) / P'(Q)`` (negative; ``-inf`` at ``Q = 0``)."""
        q = float(quantity)
        if q <= 0:
            return -math.inf
        return self.price(q) / (q * self.price_slope(q))

    def to_dict(self) -> dict[str, object]:
        return {"equation": self.formula, "linear": self._linear is not None}

    def __repr__(self) -> str:
        return f"Demand({self.formula!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Demand) and self.formula == other.formula

    def __hash__(self) -> int:
        return hash(self.formula)


DemandLike = LinearDemand | Demand
"""A demand curve a model accepts: the older straight line or a formula demand."""


def as_demand(value: LinearDemand | Demand | str, *, language: str | None = None) -> DemandLike:
    """A formula or a demand object as the demand a model uses.

    A straight-line ``Demand`` becomes its :class:`LinearDemand`, so every older code path sees
    the same numbers; a nonlinear one stays a ``Demand``.
    """
    demand = Demand(value, language=language) if isinstance(value, str) else value
    if isinstance(demand, Demand) and demand.linear is not None:
        return demand.linear
    return demand


def linear_demand(value: DemandLike) -> LinearDemand:
    """The straight line ``P = a - bQ`` of a demand, for models that are built on one."""
    if isinstance(value, Demand):
        if value.linear is None:
            raise DemandError(_say("demand.error.needs_linear"))
        return value.linear
    return value


__all__ = ["Demand", "DemandError", "DemandLike", "as_demand", "linear_demand"]
