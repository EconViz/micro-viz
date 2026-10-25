"""Renderer-neutral duopoly models: Cournot, Stackelberg and differentiated Bertrand.

Quantity setting uses the linear inverse demand ``P = a - b (Q1 + Q2)`` and constant marginal
costs ``c1``, ``c2``; firm ``i`` best-responds with ``q_i = (a - c_i - b q_j) / (2 b)``. Price
setting uses the linear demands ``Q_i = alpha - beta p_i + gamma p_j`` (``gamma`` < ``beta`` for
the goods to be imperfect substitutes) and costs ``c_i`` per unit; firm ``i`` best-responds with
``p_i = (alpha + beta c_i + gamma p_j) / (2 beta)``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from micro_viz.competition import CompetitionError

Point = tuple[float, float]


class OligopolyError(CompetitionError):
    """Raised when a duopoly input is invalid."""


def _positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0:
        raise OligopolyError(f"{name} must be finite and positive.")


@dataclass(frozen=True, slots=True)
class Duopoly:
    """Linear demand ``P = intercept - slope (Q1 + Q2)`` and the marginal costs of two firms."""

    intercept: float
    slope: float
    cost_1: float
    cost_2: float

    def __post_init__(self) -> None:
        _positive("intercept", self.intercept)
        _positive("slope", self.slope)
        for name, cost in (("cost_1", self.cost_1), ("cost_2", self.cost_2)):
            if not math.isfinite(cost) or cost < 0 or cost >= self.intercept:
                raise OligopolyError(f"{name} must lie in [0, intercept).")

    def price(self, total: float) -> float:
        return self.intercept - self.slope * total

    def best_response_1(self, q2: float) -> float:
        """Firm 1's profit-maximising output given the rival's output ``q2``."""
        return max((self.intercept - self.cost_1 - self.slope * q2) / (2 * self.slope), 0.0)

    def best_response_2(self, q1: float) -> float:
        return max((self.intercept - self.cost_2 - self.slope * q1) / (2 * self.slope), 0.0)

    def profit(self, q1: float, q2: float) -> tuple[float, float]:
        price = self.price(q1 + q2)
        return (price - self.cost_1) * q1, (price - self.cost_2) * q2

    @property
    def reach_1(self) -> float:
        """Output of firm 1 at which price falls to its marginal cost (the axis reach)."""
        return (self.intercept - self.cost_1) / self.slope

    @property
    def reach_2(self) -> float:
        return (self.intercept - self.cost_2) / self.slope

    def residual_demand(self, q2: float) -> tuple[float, float]:
        """Firm 1's residual demand ``P = a - b q2 - b q1`` as ``(intercept, slope)``."""
        return self.intercept - self.slope * q2, self.slope

    def residual_marginal_revenue(self, q2: float) -> tuple[float, float]:
        """``MR1 = a - b q2 - 2 b q1`` as ``(intercept, slope)``."""
        return self.intercept - self.slope * q2, 2 * self.slope


@dataclass(frozen=True, slots=True)
class CournotEquilibrium:
    """Cournot-Nash outputs, price and profits."""

    q1: float
    q2: float
    price: float
    profit_1: float
    profit_2: float


def cournot(duopoly: Duopoly) -> CournotEquilibrium:
    """The Cournot-Nash equilibrium (closed form; interior when both outputs are positive)."""
    a, b, c1, c2 = duopoly.intercept, duopoly.slope, duopoly.cost_1, duopoly.cost_2
    q1 = max((a - 2 * c1 + c2) / (3 * b), 0.0)
    q2 = max((a - 2 * c2 + c1) / (3 * b), 0.0)
    if q1 == 0.0:
        q2 = duopoly.best_response_2(0.0)
    elif q2 == 0.0:
        q1 = duopoly.best_response_1(0.0)
    p1, p2 = duopoly.profit(q1, q2)
    return CournotEquilibrium(q1, q2, duopoly.price(q1 + q2), p1, p2)


@dataclass(frozen=True, slots=True)
class StackelbergEquilibrium:
    """Stackelberg outputs: the leader commits first and the follower best-responds."""

    leader: int
    q1: float
    q2: float
    price: float
    profit_1: float
    profit_2: float


def stackelberg(duopoly: Duopoly, leader: int = 1) -> StackelbergEquilibrium:
    """Firm ``leader`` (1 or 2) maximises profit along the follower's reaction curve."""
    if leader not in (1, 2):
        raise OligopolyError("leader must be 1 or 2.")
    a, b = duopoly.intercept, duopoly.slope
    if leader == 1:
        q1 = max((a - 2 * duopoly.cost_1 + duopoly.cost_2) / (2 * b), 0.0)
        q2 = duopoly.best_response_2(q1)
    else:
        q2 = max((a - 2 * duopoly.cost_2 + duopoly.cost_1) / (2 * b), 0.0)
        q1 = duopoly.best_response_1(q2)
    p1, p2 = duopoly.profit(q1, q2)
    return StackelbergEquilibrium(leader, q1, q2, duopoly.price(q1 + q2), p1, p2)


def competitive_total(duopoly: Duopoly) -> float:
    """Total output at ``P = MC`` of the cheaper firm."""
    return (duopoly.intercept - min(duopoly.cost_1, duopoly.cost_2)) / duopoly.slope


def collusive_total(duopoly: Duopoly) -> float:
    """Joint-profit-maximising total output (the cheaper firm's marginal cost)."""
    return competitive_total(duopoly) / 2


def split(total: float, share: float = 0.5) -> Point:
    """The outputs ``(share * total, (1 - share) * total)`` on a constant-total-output line."""
    if not 0.0 <= share <= 1.0:
        raise OligopolyError("share must lie in [0, 1].")
    return share * total, (1 - share) * total


@dataclass(frozen=True, slots=True)
class DifferentiatedDuopoly:
    """Demands ``Q_i = alpha_i - beta_i p_i + gamma_i p_j`` and unit costs of two firms."""

    alpha_1: float
    alpha_2: float
    beta_1: float
    beta_2: float
    gamma_1: float
    gamma_2: float
    cost_1: float
    cost_2: float

    def __post_init__(self) -> None:
        for name in ("alpha_1", "alpha_2", "beta_1", "beta_2", "gamma_1", "gamma_2"):
            _positive(name, getattr(self, name))
        if self.gamma_1 * self.gamma_2 >= 4 * self.beta_1 * self.beta_2:
            raise OligopolyError("Reaction curves must cross: need gamma1 gamma2 < 4 beta1 beta2.")
        if self.cost_1 < 0 or self.cost_2 < 0:
            raise OligopolyError("Costs must be nonnegative.")

    def quantity_1(self, p1: float, p2: float) -> float:
        return max(self.alpha_1 - self.beta_1 * p1 + self.gamma_1 * p2, 0.0)

    def quantity_2(self, p1: float, p2: float) -> float:
        return max(self.alpha_2 - self.beta_2 * p2 + self.gamma_2 * p1, 0.0)

    def profits(self, p1: float, p2: float) -> tuple[float, float]:
        return (
            (p1 - self.cost_1) * self.quantity_1(p1, p2),
            (p2 - self.cost_2) * self.quantity_2(p1, p2),
        )

    def best_price_1(self, p2: float) -> float:
        return (self.alpha_1 + self.beta_1 * self.cost_1 + self.gamma_1 * p2) / (2 * self.beta_1)

    def best_price_2(self, p1: float) -> float:
        return (self.alpha_2 + self.beta_2 * self.cost_2 + self.gamma_2 * p1) / (2 * self.beta_2)


@dataclass(frozen=True, slots=True)
class BertrandEquilibrium:
    """Nash and joint-profit-maximising price pairs of a differentiated duopoly."""

    nash: Point
    collusive: Point
    nash_profits: tuple[float, float]
    collusive_profits: tuple[float, float]


def _solve(a11: float, a12: float, a21: float, a22: float, b1: float, b2: float) -> Point:
    det = a11 * a22 - a12 * a21
    return (b1 * a22 - a12 * b2) / det, (a11 * b2 - b1 * a21) / det


def bertrand(duopoly: DifferentiatedDuopoly) -> BertrandEquilibrium:
    """Nash prices (both reaction curves hold) and collusive prices (first-order conditions of
    joint profit); both solve linear systems."""
    d = duopoly
    nash = _solve(
        2 * d.beta_1,
        -d.gamma_1,
        -d.gamma_2,
        2 * d.beta_2,
        d.alpha_1 + d.beta_1 * d.cost_1,
        d.alpha_2 + d.beta_2 * d.cost_2,
    )
    # d/dp1 of (p1-c1)Q1 + (p2-c2)Q2 and the analogue for p2.
    if 4 * d.beta_1 * d.beta_2 <= (d.gamma_1 + d.gamma_2) ** 2:
        raise OligopolyError("Joint profit needs (gamma1 + gamma2)^2 < 4 beta1 beta2.")
    collusive = _solve(
        2 * d.beta_1,
        -(d.gamma_1 + d.gamma_2),
        -(d.gamma_1 + d.gamma_2),
        2 * d.beta_2,
        d.alpha_1 + d.beta_1 * d.cost_1 - d.gamma_2 * d.cost_2,
        d.alpha_2 + d.beta_2 * d.cost_2 - d.gamma_1 * d.cost_1,
    )
    return BertrandEquilibrium(nash, collusive, d.profits(*nash), d.profits(*collusive))
