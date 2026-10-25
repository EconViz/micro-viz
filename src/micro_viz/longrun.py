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
