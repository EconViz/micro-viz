"""Renderer-neutral short-run cost functions.

Notation (outputs and costs are per period):

* ``FC`` fixed cost, ``VC(q)`` variable cost, ``TC(q) = FC + VC(q)`` total cost;
* ``AFC = FC / q``, ``AVC = VC / q``, ``ATC = TC / q`` for ``q > 0``;
* ``MC(q) = dVC/dq`` marginal cost, the same as ``dTC/dq``.

Two families are provided. :class:`CubicCost` has ``VC = bq + cq^2 + dq^3`` (``b, d > 0``) and
U-shaped MC and AVC curves. :class:`PiecewiseCost` is defined by its marginal cost, built from
segments that may jump up where a further shift or processing unit starts; its output is
limited by the last segment's end (the capacity).
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass


class CostError(ValueError):
    """Raised when a cost model or a cost analysis input is invalid."""


def _finite(name: str, value: float) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise CostError(f"{name} must be finite.")
    return number


class CostFunction(ABC):
    """A short-run cost function: fixed cost plus a variable cost with its marginal cost."""

    output_symbol: str
    fixed_cost: float

    @abstractmethod
    def variable_cost(self, output: float) -> float:
        """Variable cost ``VC(q)`` of a nonnegative output."""

    @abstractmethod
    def marginal_cost(self, output: float) -> float:
        """Marginal cost ``MC(q)``; at a jump the value is the one just above ``q``."""

    @property
    def capacity(self) -> float:
        """The largest feasible output (``inf`` when there is no capacity limit)."""
        return math.inf

    def total_cost(self, output: float) -> float:
        """``TC(q) = FC + VC(q)``."""
        return self.fixed_cost + self.variable_cost(output)

    def average_fixed_cost(self, output: float) -> float | None:
        """``FC / q``; undefined (``None``) at zero output."""
        return None if self._output(output) == 0 else self.fixed_cost / output

    def average_variable_cost(self, output: float) -> float | None:
        """``VC / q``; undefined (``None``) at zero output."""
        return None if self._output(output) == 0 else self.variable_cost(output) / output

    def average_total_cost(self, output: float) -> float | None:
        """``TC / q``; undefined (``None``) at zero output."""
        return None if self._output(output) == 0 else self.total_cost(output) / output

    def _output(self, output: float) -> float:
        value = float(output)
        if not math.isfinite(value):
            raise CostError("Output must be finite.")
        if value < 0:
            raise CostError("Output must be nonnegative.")
        if value > self.capacity:
            raise CostError(f"Output {value} exceeds the capacity {self.capacity}.")
        return value

    @abstractmethod
    def to_dict(self) -> dict[str, object]:
        """Serialize the parameters with the equation and sign conventions."""


@dataclass(frozen=True, slots=True)
class CubicCost(CostFunction):
    """``TC(q) = FC + bq + cq^2 + dq^3`` with ``b > 0``, ``d > 0`` and ``MC >= 0``.

    ``c`` may be negative (the usual U-shape needs ``c < 0``); marginal cost
    ``b + 2cq + 3dq^2`` stays positive when ``c^2 < 3bd``.
    """

    fixed_cost: float = 0.0
    linear: float = 1.0
    quadratic: float = 0.0
    cubic: float = 1.0
    output_symbol: str = "q"

    def __post_init__(self) -> None:
        for name in ("fixed_cost", "linear", "quadratic", "cubic"):
            _finite(name, getattr(self, name))
        if self.fixed_cost < 0:
            raise CostError("The fixed cost must be nonnegative.")
        if self.linear <= 0 or self.cubic <= 0:
            raise CostError("The linear and cubic coefficients must be positive.")
        if self.quadratic < 0 and self.quadratic**2 >= 3 * self.linear * self.cubic:
            raise CostError("Marginal cost must stay positive: need quadratic^2 < 3*linear*cubic.")
        if not self.output_symbol.strip():
            raise CostError("The output symbol must be nonempty.")

    def variable_cost(self, output: float) -> float:
        q = self._output(output)
        return self.linear * q + self.quadratic * q**2 + self.cubic * q**3

    def marginal_cost(self, output: float) -> float:
        q = self._output(output)
        return self.linear + 2 * self.quadratic * q + 3 * self.cubic * q**2

    @property
    def minimum_marginal_cost_output(self) -> float:
        """Output where MC stops falling and starts rising (``0`` when ``c >= 0``)."""
        return max(0.0, -self.quadratic / (3 * self.cubic))

    @property
    def minimum_average_variable_cost_output(self) -> float:
        """Output where AVC is lowest; there MC = AVC (``0`` when ``c >= 0``)."""
        return max(0.0, -self.quadratic / (2 * self.cubic))

    @property
    def minimum_average_total_cost_output(self) -> float:
        """Output where ATC is lowest; there MC = ATC.

        ATC' = 0 reduces to ``2d q^3 + c q^2 - FC = 0``, whose left side is negative at the
        AVC minimum and increasing beyond it, so bisection finds the single root.
        """
        if self.fixed_cost == 0:
            return self.minimum_average_variable_cost_output

        def derivative(q: float) -> float:
            return 2 * self.cubic * q**3 + self.quadratic * q**2 - self.fixed_cost

        low = self.minimum_average_variable_cost_output
        high = max(1.0, 2 * low)
        while derivative(high) < 0:
            high *= 2
        for _ in range(200):
            middle = (low + high) / 2
            if derivative(middle) < 0:
                low = middle
            else:
                high = middle
        return (low + high) / 2

    def to_dict(self) -> dict[str, object]:
        q = self.output_symbol
        return {
            "equation": f"TC({q}) = FC + b{q} + c{q}^2 + d{q}^3",
            "sign_convention": "b > 0, d > 0, c^2 < 3bd when c < 0, FC >= 0",
            "coefficients": {
                "FC": self.fixed_cost,
                "b": self.linear,
                "c": self.quadratic,
                "d": self.cubic,
            },
            "output_symbol": self.output_symbol,
        }


@dataclass(frozen=True, slots=True)
class CostSegment:
    """Marginal cost ``a + b x + c x^2`` for output ``q`` from the previous end to ``end``.

    ``x = q - start`` is the output produced within the segment. A segment starts at the
    previous segment's end (the first at zero); a higher ``a`` than the previous segment
    reaches at its end is a jump, such as an extra shift or a further processing unit.
    """

    end: float
    intercept: float
    slope: float = 0.0
    curvature: float = 0.0

    def __post_init__(self) -> None:
        for name in ("end", "intercept", "slope", "curvature"):
            _finite(name, getattr(self, name))
        if self.end <= 0:
            raise CostError("A segment must end at a positive output.")
        if self.intercept < 0:
            raise CostError("Marginal cost must be nonnegative.")

    def marginal_cost(self, within: float) -> float:
        """MC after producing ``within`` units inside the segment."""
        return self.intercept + self.slope * within + self.curvature * within**2

    def variable_cost(self, within: float) -> float:
        """Variable cost of the first ``within`` units of the segment."""
        return self.intercept * within + self.slope * within**2 / 2 + self.curvature * within**3 / 3


@dataclass(frozen=True, slots=True)
class PiecewiseCost(CostFunction):
    """A cost function given by piecewise marginal cost with a capacity limit.

    Marginal cost may be flat, rising or jump up between segments but never falls, so the
    profit-maximizing output at a price is where price meets MC, stopping at a jump when the
    price lies inside it. ``fixed_cost`` is added to total cost.
    """

    segments: tuple[CostSegment, ...]
    fixed_cost: float = 0.0
    output_symbol: str = "q"

    def __post_init__(self) -> None:
        segments = tuple(self.segments)
        object.__setattr__(self, "segments", segments)
        if not segments:
            raise CostError("At least one segment is required.")
        _finite("fixed_cost", self.fixed_cost)
        if self.fixed_cost < 0:
            raise CostError("The fixed cost must be nonnegative.")
        if not self.output_symbol.strip():
            raise CostError("The output symbol must be nonempty.")
        start = 0.0
        previous_end_cost = 0.0
        for index, segment in enumerate(segments):
            if segment.end <= start:
                raise CostError("Segment ends must be strictly increasing.")
            length = segment.end - start
            for within in (0.0, length):  # the derivative is linear, so its ends decide
                if segment.slope + 2 * segment.curvature * within < -1e-12:
                    raise CostError("Marginal cost must not fall within a segment.")
            if index and segment.intercept < previous_end_cost - 1e-12:
                raise CostError("Marginal cost must not fall between segments.")
            previous_end_cost = segment.marginal_cost(length)
            start = segment.end

    @property
    def capacity(self) -> float:
        return self.segments[-1].end

    @property
    def breakpoints(self) -> tuple[float, ...]:
        """The outputs where one segment ends and the next begins (excluding the capacity)."""
        return tuple(segment.end for segment in self.segments[:-1])

    def _starts(self) -> tuple[float, ...]:
        return (0.0, *(segment.end for segment in self.segments[:-1]))

    def variable_cost(self, output: float) -> float:
        q = self._output(output)
        total = 0.0
        for start, segment in zip(self._starts(), self.segments, strict=True):
            if q <= start:
                break
            total += segment.variable_cost(min(q, segment.end) - start)
        return total

    def marginal_cost(self, output: float) -> float:
        q = self._output(output)
        for start, segment in zip(self._starts(), self.segments, strict=True):
            if q < segment.end:
                return segment.marginal_cost(q - start)
        last = self.segments[-1]
        return last.marginal_cost(last.end - self._starts()[-1])

    def output_at_price(self, price: float) -> float:
        """The output where ``price`` meets MC; it stops at a jump that lies above the price.

        A price below the first MC gives zero output; a price above every MC gives the
        capacity.
        """
        value = _finite("price", price)
        for start, segment in zip(self._starts(), self.segments, strict=True):
            length = segment.end - start
            if value < segment.intercept:
                return start
            if value >= segment.marginal_cost(length):
                continue
            return start + _solve_rising(segment, value, length)
        return self.capacity

    def to_dict(self) -> dict[str, object]:
        q = self.output_symbol
        return {
            "equation": f"MC({q}) = a + b x + c x^2 on each segment, x = {q} - start of segment",
            "sign_convention": "MC is nondecreasing; jumps up between segments; q <= capacity",
            "fixed_cost": self.fixed_cost,
            "segments": [
                {
                    "start": start,
                    "end": segment.end,
                    "a": segment.intercept,
                    "b": segment.slope,
                    "c": segment.curvature,
                }
                for start, segment in zip(self._starts(), self.segments, strict=True)
            ],
            "capacity": self.capacity,
            "output_symbol": self.output_symbol,
        }


def _solve_rising(segment: CostSegment, price: float, length: float) -> float:
    """The ``x`` in ``[0, length]`` where the segment's MC equals ``price`` (MC nondecreasing)."""
    low, high = 0.0, length
    for _ in range(100):
        middle = (low + high) / 2
        if segment.marginal_cost(middle) < price:
            low = middle
        else:
            high = middle
    return (low + high) / 2


__all__ = ["CostError", "CostFunction", "CostSegment", "CubicCost", "PiecewiseCost"]
