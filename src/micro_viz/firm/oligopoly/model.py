"""Renderer-neutral oligopoly domain models.

Quantity setting uses the linear inverse demand ``P = a - b (Q1 + Q2)`` and constant marginal
costs ``c1``, ``c2``; firm ``i`` best-responds with ``q_i = (a - c_i - b q_j) / (2 b)``. Price
setting uses the linear demands ``Q_i = alpha - beta p_i + gamma p_j`` (``gamma`` < ``beta`` for
the goods to be imperfect substitutes) and costs ``c_i`` per unit; firm ``i`` best-responds with
``p_i = (alpha + beta c_i + gamma p_j) / (2 beta)``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from micro_viz.firm.perfect_competition import CompetitionError

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


@dataclass(frozen=True, slots=True)
class KinkedDemand:
    """Kinked demand through ``(quantity, price)``: the segment above the kink has the flatter
    slope ``upper_slope`` (rivals do not follow a price rise) and the one below the steeper
    ``lower_slope`` (rivals match a cut). Inverse form ``P = P0 - slope (Q - Q0)``."""

    quantity: float
    price: float
    upper_slope: float
    lower_slope: float

    def __post_init__(self) -> None:
        _positive("quantity", self.quantity)
        _positive("price", self.price)
        _positive("upper_slope", self.upper_slope)
        if self.lower_slope <= self.upper_slope:
            raise OligopolyError("The lower segment must be steeper than the upper one.")
        if self.price - self.lower_slope * self.quantity < 0:
            raise OligopolyError("Marginal revenue below the kink must stay nonnegative.")

    def demand(self, quantity: float) -> float:
        slope = self.upper_slope if quantity <= self.quantity else self.lower_slope
        return self.price - slope * (quantity - self.quantity)

    def marginal_revenue(self, quantity: float) -> float:
        """Marginal revenue: ``a - 2 slope Q`` on whichever segment applies."""
        slope = self.upper_slope if quantity <= self.quantity else self.lower_slope
        return self.price + slope * self.quantity - 2 * slope * quantity

    @property
    def gap(self) -> tuple[float, float]:
        """``(low, high)`` of the vertical marginal-revenue gap at the kink."""
        return (
            self.price - self.lower_slope * self.quantity,
            self.price - self.upper_slope * self.quantity,
        )

    def keeps_price(self, marginal_cost: float) -> bool:
        """Whether a flat marginal cost leaves the kink as the profit maximum."""
        low, high = self.gap
        return low - 1e-12 <= marginal_cost <= high + 1e-12


@dataclass(frozen=True, slots=True)
class DominantFirmOutcome:
    """Equilibrium of a dominant firm (or cartel) facing a competitive fringe."""

    price: float
    dominant_quantity: float
    fringe_quantity: float
    total_quantity: float
    marginal_revenue: float


@dataclass(frozen=True, slots=True)
class DominantFirm:
    """Market demand ``Q = demand_intercept - demand_slope P``, fringe supply
    ``Q_F = fringe_slope (P - fringe_start)`` (zero below ``fringe_start``) and the dominant
    firm's marginal cost ``MC = cost_intercept + cost_slope Q``. The dominant firm faces the
    residual demand ``D - S_F`` and sets ``MR = MC`` on it."""

    demand_intercept: float
    demand_slope: float
    fringe_start: float
    fringe_slope: float
    cost_intercept: float
    cost_slope: float = 0.0

    def __post_init__(self) -> None:
        _positive("demand_intercept", self.demand_intercept)
        _positive("demand_slope", self.demand_slope)
        _positive("fringe_slope", self.fringe_slope)
        if not math.isfinite(self.cost_slope) or self.cost_slope < 0:
            raise OligopolyError("cost_slope must be finite and nonnegative.")
        if not 0 <= self.fringe_start < self.demand_intercept / self.demand_slope:
            raise OligopolyError("fringe_start must lie in [0, choke price).")
        if not 0 <= self.cost_intercept:
            raise OligopolyError("cost_intercept must be nonnegative.")

    def market_demand(self, price: float) -> float:
        return max(self.demand_intercept - self.demand_slope * price, 0.0)

    def fringe_supply(self, price: float) -> float:
        return max(self.fringe_slope * (price - self.fringe_start), 0.0)

    def residual_demand(self, price: float) -> float:
        return max(self.market_demand(price) - self.fringe_supply(price), 0.0)

    @property
    def choke_price(self) -> float:
        return self.demand_intercept / self.demand_slope

    @property
    def residual_choke_price(self) -> float:
        """Price at which the fringe supplies all of demand (residual demand reaches zero)."""
        return (self.demand_intercept + self.fringe_slope * self.fringe_start) / (
            self.demand_slope + self.fringe_slope
        )

    @property
    def kink_quantity(self) -> float:
        """Residual quantity at the fringe's start price, where its slope changes."""
        return self.market_demand(self.fringe_start)

    def residual_segments(self) -> tuple[tuple[float, float], tuple[float, float]]:
        """Inverse residual demand ``P = A - B Q`` as ``(A, B)`` for the upper segment (below the
        kink quantity, fringe active) and the lower segment (fringe inactive)."""
        total = self.demand_slope + self.fringe_slope
        upper = (self.residual_choke_price, 1.0 / total)
        lower = (self.choke_price, 1.0 / self.demand_slope)
        return upper, lower

    def inverse_residual(self, quantity: float) -> float:
        upper, lower = self.residual_segments()
        a, b = upper if quantity <= self.kink_quantity else lower
        return a - b * quantity

    def solve(self) -> DominantFirmOutcome:
        """Try each segment of residual demand for ``MR = MC`` inside its quantity range."""
        upper, lower = self.residual_segments()
        k = self.kink_quantity
        for (a, b), low, high in ((upper, 0.0, k), (lower, k, self.demand_intercept)):
            quantity = (a - self.cost_intercept) / (2 * b + self.cost_slope)
            if low - 1e-12 <= quantity <= high + 1e-12 and quantity >= 0:
                price = a - b * quantity
                return DominantFirmOutcome(
                    price=price,
                    dominant_quantity=quantity,
                    fringe_quantity=self.fringe_supply(price),
                    total_quantity=self.market_demand(price),
                    marginal_revenue=a - 2 * b * quantity,
                )
        # MR = MC falls in the vertical gap at the kink: the kink quantity is optimal.
        price = self.fringe_start
        return DominantFirmOutcome(price, k, 0.0, self.market_demand(price), price)
