"""Renderer-neutral long-run technology: isoquants, MRTS and returns to scale.

Output is ``Q = f(L, K)``. An isoquant holds the output fixed; its slope magnitude is the
marginal rate of technical substitution ``MRTS = MP_L / MP_K`` (the capital given up for one
more unit of labour). Returns to scale compare the output of a scaled input bundle with the
scaled output.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

Point = tuple[float, float]
BISECTIONS = 80
"""Bisection steps of the numeric searches."""


class IsoquantError(ValueError):
    """Raised when a technology or an isoquant request is invalid."""


class Returns(str, Enum):
    """Returns to scale of a technology."""

    INCREASING = "increasing"
    CONSTANT = "constant"
    DECREASING = "decreasing"


def _positive(name: str, value: float) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise IsoquantError(f"{name} must be finite and positive.")
    return number


class Technology(ABC):
    """A production technology in labour ``L`` and capital ``K``."""

    labor_symbol: str = "L"
    capital_symbol: str = "K"

    @abstractmethod
    def output(self, labor: float, capital: float) -> float:
        """``Q = f(L, K)`` for nonnegative inputs."""

    @abstractmethod
    def capital_for(self, output: float, labor: float) -> float | None:
        """Capital that gives ``output`` with ``labor`` (``None`` when none does)."""

    @abstractmethod
    def mrts(self, labor: float, capital: float) -> float | None:
        """Marginal rate of technical substitution at ``(L, K)`` (``None`` at a kink)."""

    @abstractmethod
    def isoquant(self, output: float, bounds: Point, samples: int = 121) -> tuple[Point, ...]:
        """Points ``(L, K)`` of the isoquant of ``output`` inside ``0..bounds`` (L, K)."""

    def labor_for(self, output: float, capital: float) -> float | None:
        """Labour that gives ``output`` with ``capital`` (bisection on a monotone output)."""
        if self.output(0.0, capital) >= output:
            return 0.0
        high = 1.0
        while self.output(high, capital) < output:
            high *= 2
            if high > 1e12:
                return None
        low = 0.0
        for _ in range(BISECTIONS):
            middle = (low + high) / 2
            if self.output(middle, capital) < output:
                low = middle
            else:
                high = middle
        return high

    def scale_for(self, output: float, labor: float, capital: float) -> float:
        """The factor ``t`` with ``f(tL, tK) = output`` along the ray through ``(L, K)``."""
        _positive("output", output)
        high = 1.0
        while self.output(labor * high, capital * high) < output:
            high *= 2
            if high > 1e12:
                raise IsoquantError("The output is not reachable along this ray.")
        low = 0.0
        for _ in range(BISECTIONS):
            middle = (low + high) / 2
            if self.output(labor * middle, capital * middle) < output:
                low = middle
            else:
                high = middle
        return high

    def returns_to_scale(
        self, labor: float = 1.0, capital: float = 1.0, factor: float = 2.0
    ) -> Returns:
        """Compare ``f(tL, tK)`` with ``t f(L, K)`` for ``t = factor``."""
        base = self.output(labor, capital)
        scaled = self.output(labor * factor, capital * factor)
        tolerance = 1e-9 * max(1.0, scaled)
        if scaled > factor * base + tolerance:
            return Returns.INCREASING
        if scaled < factor * base - tolerance:
            return Returns.DECREASING
        return Returns.CONSTANT


def _grid(low: float, high: float, samples: int) -> list[float]:
    if isinstance(samples, bool) or not isinstance(samples, int) or samples < 2:
        raise IsoquantError("samples must be an integer of at least 2.")
    return [low + (high - low) * index / (samples - 1) for index in range(samples)]


@dataclass(frozen=True, slots=True)
class CobbDouglas(Technology):
    """``Q = A L^a K^b``: convex isoquants, MRTS ``(a / b) K / L`` falling along an isoquant."""

    labor_share: float = 0.5
    capital_share: float = 0.5
    scale: float = 1.0

    def __post_init__(self) -> None:
        for name in ("labor_share", "capital_share", "scale"):
            _positive(name, getattr(self, name))

    def output(self, labor: float, capital: float) -> float:
        return float(self.scale * labor**self.labor_share * capital**self.capital_share)

    def capital_for(self, output: float, labor: float) -> float | None:
        if labor <= 0:
            return None
        return float((output / (self.scale * labor**self.labor_share)) ** (1 / self.capital_share))

    def labor_for(self, output: float, capital: float) -> float | None:
        if capital <= 0:
            return None
        return float(
            (output / (self.scale * capital**self.capital_share)) ** (1 / self.labor_share)
        )

    def mrts(self, labor: float, capital: float) -> float | None:
        if labor <= 0:
            return None
        return self.labor_share * capital / (self.capital_share * labor)

    def isoquant(self, output: float, bounds: Point, samples: int = 121) -> tuple[Point, ...]:
        _positive("output", output)
        l_max, k_max = bounds
        start = self.labor_for(output, k_max) or 0.0
        if start >= l_max:
            return ()
        return tuple(
            (labor, self.capital_for(output, labor) or 0.0)
            for labor in _grid(start, l_max, samples)
        )


@dataclass(frozen=True, slots=True)
class PerfectSubstitutes(Technology):
    """``Q = a L + b K``: straight isoquants with a constant MRTS ``a / b``."""

    labor_weight: float = 1.0
    capital_weight: float = 1.0

    def __post_init__(self) -> None:
        _positive("labor_weight", self.labor_weight)
        _positive("capital_weight", self.capital_weight)

    def output(self, labor: float, capital: float) -> float:
        return self.labor_weight * labor + self.capital_weight * capital

    def capital_for(self, output: float, labor: float) -> float | None:
        value = (output - self.labor_weight * labor) / self.capital_weight
        return value if value >= 0 else None

    def mrts(self, labor: float, capital: float) -> float | None:
        return self.labor_weight / self.capital_weight

    def isoquant(self, output: float, bounds: Point, samples: int = 121) -> tuple[Point, ...]:
        _positive("output", output)
        l_max, k_max = bounds
        lo = max(0.0, (output - self.capital_weight * k_max) / self.labor_weight)
        hi = min(l_max, output / self.labor_weight)
        if lo >= hi:
            return ()
        return tuple((x, self.capital_for(output, x) or 0.0) for x in (lo, hi))


@dataclass(frozen=True, slots=True)
class FixedProportions(Technology):
    """``Q = min(a L, b K)``: L-shaped isoquants with kinks on the ray ``K / L = a / b``."""

    labor_weight: float = 1.0
    capital_weight: float = 1.0

    def __post_init__(self) -> None:
        _positive("labor_weight", self.labor_weight)
        _positive("capital_weight", self.capital_weight)

    @property
    def ray_slope(self) -> float:
        """Capital per unit of labour along the kinks."""
        return self.labor_weight / self.capital_weight

    def output(self, labor: float, capital: float) -> float:
        return min(self.labor_weight * labor, self.capital_weight * capital)

    def capital_for(self, output: float, labor: float) -> float | None:
        return output / self.capital_weight if self.labor_weight * labor >= output else None

    def mrts(self, labor: float, capital: float) -> float | None:
        a, b = self.labor_weight * labor, self.capital_weight * capital
        if math.isclose(a, b):
            return None
        return 0.0 if a > b else math.inf

    def corner(self, output: float) -> Point:
        """The kink ``(L, K)`` of the isoquant of ``output``."""
        return (output / self.labor_weight, output / self.capital_weight)

    def isoquant(self, output: float, bounds: Point, samples: int = 121) -> tuple[Point, ...]:
        _positive("output", output)
        l_max, k_max = bounds
        labor, capital = self.corner(output)
        if labor > l_max or capital > k_max:
            return ()
        return ((labor, k_max), (labor, capital), (l_max, capital))


def ray_points(slope: float, bounds: Point) -> tuple[Point, Point]:
    """The ray ``K = slope L`` from the origin to the edge of ``bounds``."""
    l_max, k_max = bounds
    reach = min(l_max, k_max / slope)
    return ((0.0, 0.0), (reach, slope * reach))
