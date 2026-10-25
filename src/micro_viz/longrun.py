"""Renderer-neutral long-run costs and long-run competition.

Plants differ by design output ``s``. A plant of size ``s`` has the short-run average cost
``SAC_s(Q) = m(s) + k (Q - s)^2 / s`` with ``m(s) = C_min + c (s - E)^2 / E``: the best plant
is cheapest at ``Q = s`` and bigger or smaller plants cost more. The long-run average cost is
the lower envelope ``LAC(Q) = min_s SAC_s(Q)``, lowest (``C_min``) at the efficient scale
``E``; long-run marginal cost is ``LMC = d(Q LAC)/dQ``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from micro_viz.competition import CompetitionError

SEARCH_STEPS = 120
"""Iterations of the numeric searches."""
DERIVATIVE_STEP = 1e-4
"""Relative step of the numeric derivative of long-run total cost."""
PHI = (math.sqrt(5) - 1) / 2


class LongRunError(CompetitionError):
    """Raised when a long-run cost or entry input is invalid."""


def _positive(name: str, value: float) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise LongRunError(f"{name} must be finite and positive.")
    return number


@dataclass(frozen=True, slots=True)
class PlantFamily:
    """Plants of every size ``s`` and the long-run costs they envelope."""

    efficient_scale: float
    minimum_cost: float
    scale_curvature: float
    steepness: float

    def __post_init__(self) -> None:
        for name in ("efficient_scale", "minimum_cost", "scale_curvature", "steepness"):
            _positive(name, getattr(self, name))

    def plant_minimum(self, size: float) -> float:
        """The lowest SAC of the plant of size ``s``."""
        e = self.efficient_scale
        return self.minimum_cost + self.scale_curvature * (size - e) ** 2 / e

    def sac(self, size: float, output: float) -> float:
        """Short-run average cost of the plant of size ``size``."""
        return self.plant_minimum(size) + self.steepness * (output - size) ** 2 / size

    def smc(self, size: float, output: float) -> float:
        """Short-run marginal cost ``SAC + Q dSAC/dQ`` of that plant."""
        return self.sac(size, output) + output * 2 * self.steepness * (output - size) / size

    def best_plant(self, output: float) -> float:
        """The plant size that minimises SAC at ``output`` (golden-section search)."""
        _positive("output", output)
        low, high = output * 1e-3, max(output, self.efficient_scale) * 4
        a, b = high - PHI * (high - low), low + PHI * (high - low)
        fa, fb = self.sac(a, output), self.sac(b, output)
        for _ in range(SEARCH_STEPS):
            if fa < fb:
                high, b, fb = b, a, fa
                a = high - PHI * (high - low)
                fa = self.sac(a, output)
            else:
                low, a, fa = a, b, fb
                b = low + PHI * (high - low)
                fb = self.sac(b, output)
        return (low + high) / 2

    def tangent_output(self, size: float) -> float:
        """The output where the plant of ``size`` is the best plant, so its SAC touches LAC."""
        _positive("size", size)
        low, high = size * 1e-3, max(size, self.efficient_scale) * 8
        for _ in range(SEARCH_STEPS // 2):
            middle = (low + high) / 2
            if self.best_plant(middle) < size:
                low = middle
            else:
                high = middle
        return (low + high) / 2

    def lac(self, output: float) -> float:
        """Long-run average cost."""
        return self.sac(self.best_plant(output), output)

    def lmc(self, output: float) -> float:
        """Long-run marginal cost, the slope of long-run total cost ``Q LAC(Q)``."""
        h = DERIVATIVE_STEP * max(output, self.efficient_scale)

        def total(q: float) -> float:
            return q * self.lac(q)

        return (total(output + h) - total(max(output - h, 1e-9))) / (
            output + h - max(output - h, 1e-9)
        )

    def output_at_lmc(self, price: float, *, upper: float | None = None) -> float:
        """The output on the rising part of LMC where ``LMC = price`` (bisection)."""
        low = self.efficient_scale
        high = upper if upper is not None else self.efficient_scale * 4
        if price < self.lmc(low):
            raise LongRunError("The price is below the lowest long-run marginal cost.")
        if self.lmc(high) < price:
            raise LongRunError("The price is not reached below the upper output.")
        for _ in range(SEARCH_STEPS):
            middle = (low + high) / 2
            if self.lmc(middle) < price:
                low = middle
            else:
                high = middle
        return (low + high) / 2


@dataclass(frozen=True, slots=True)
class EnvelopeFigure:
    """A quadratic LAC enveloping three quadratic SAC curves, set by where they touch.

    ``LAC(Q) = C_min + k (Q - Q_e)^2`` is lowest (``minimum_cost``) at ``minimum_output``
    ``Q_e``; ``k`` follows from ``left_cost``, the LAC at the left tangency ``left_tangent``.
    SAC1 and SAC3 touch LAC at ``left_tangent`` and ``right_tangent`` with their own lowest
    points at ``left_minimum`` and ``right_minimum`` (outputs strictly between ``Q_e`` and the
    tangency, so the SAC lies above LAC); SAC2 has its lowest point on LAC's and passes the
    point ``(Q_1, upper_cost)`` where ``Q_1`` is the output at which SAC1 comes back up to
    ``left_cost``. ``SAC_i`` and ``SMC_i = d(Q SAC_i)/dQ`` are quadratics in ``Q``.
    """

    minimum_cost: float
    minimum_output: float
    left_tangent: float
    left_cost: float
    right_tangent: float
    left_minimum: float
    right_minimum: float
    upper_cost: float

    def __post_init__(self) -> None:
        for name in ("minimum_cost", "minimum_output", "left_tangent", "right_tangent"):
            _positive(name, getattr(self, name))
        if not 0 < self.left_tangent < self.left_minimum < self.minimum_output:
            raise LongRunError("Need 0 < left_tangent < left_minimum < minimum_output.")
        if not self.minimum_output < self.right_minimum < self.right_tangent:
            raise LongRunError("Need minimum_output < right_minimum < right_tangent.")
        if self.left_cost <= self.minimum_cost:
            raise LongRunError("left_cost must exceed minimum_cost.")
        if self.upper_cost <= self.left_cost:
            raise LongRunError("upper_cost must exceed left_cost.")

    @property
    def curvature(self) -> float:
        """``k`` of ``LAC``."""
        return (self.left_cost - self.minimum_cost) / (self.minimum_output - self.left_tangent) ** 2

    def lac(self, output: float) -> float:
        return self.minimum_cost + self.curvature * (output - self.minimum_output) ** 2

    def lmc(self, output: float) -> float:
        slope = 2 * self.curvature * (output - self.minimum_output)
        return self.lac(output) + output * slope

    def _plant(self, index: int) -> tuple[float, float, float]:
        """``(lowest output, lowest cost, curvature)`` of SAC ``index`` (1, 2 or 3)."""
        if index == 2:
            q1 = self.upper_output_for(self.left_cost)
            curvature = (self.upper_cost - self.minimum_cost) / (self.minimum_output - q1) ** 2
            return self.minimum_output, self.minimum_cost, curvature
        tangent, low = (
            (self.left_tangent, self.left_minimum)
            if index == 1
            else (self.right_tangent, self.right_minimum)
        )
        curvature = self.curvature * (tangent - self.minimum_output) / (tangent - low)
        cost = self.lac(tangent) - curvature * (tangent - low) ** 2
        return low, cost, curvature

    def upper_output_for(self, cost: float) -> float:
        """The output right of SAC1's lowest point where SAC1 equals ``cost``."""
        low = self.left_minimum
        k = self.curvature * (self.left_tangent - self.minimum_output) / (self.left_tangent - low)
        floor = self.lac(self.left_tangent) - k * (self.left_tangent - low) ** 2
        if cost <= floor:
            raise LongRunError("cost must exceed the lowest SAC1.")
        return low + math.sqrt((cost - floor) / k)

    def minimum_point(self, index: int) -> tuple[float, float]:
        """Lowest point of SAC ``index``."""
        output, cost, _ = self._plant(index)
        return output, cost

    def sac(self, index: int, output: float) -> float:
        low, cost, curvature = self._plant(index)
        return cost + curvature * (output - low) ** 2

    def smc(self, index: int, output: float) -> float:
        low, _, curvature = self._plant(index)
        return self.sac(index, output) + output * 2 * curvature * (output - low)

    @property
    def right_output(self) -> float:
        """``Q_1``: where SAC1 is back at ``left_cost``, on its rising branch."""
        return self.upper_output_for(self.left_cost)
