"""Renderer-neutral production extensions: learning, scope, technical progress and frontiers.

* Learning curve: input per unit of output ``L(N) = A + B N^(-beta)`` falls with cumulative
  output ``N`` toward the floor ``A``.
* Average cost of a firm that learns: ``AC(q) = c + k (q - q0)^2`` with its minimum lowered by a
  learning factor.
* Product transformation curve: ``(Q1 / M1)^s + (Q2 / M2)^s = 1`` with bow ``s``; ``s > 1`` bows
  outward (economies of scope), ``s = 1`` is a straight line, ``s < 1`` bows inward.
* Technical progress scales total product up; a production frontier ``Q = A L^alpha`` has
  inefficient points strictly below it.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from micro_viz.production.model import ProductionError, ShortRunProductionFunction

Point = tuple[float, float]


def _positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0:
        raise ProductionError(f"{name} must be finite and positive.")


@dataclass(frozen=True, slots=True)
class LearningCurve:
    """Input per unit of output against cumulative output ``N``: ``L = A + B N^(-beta)``."""

    floor: float
    gain: float
    rate: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.floor) or self.floor < 0:
            raise ProductionError("floor must be finite and nonnegative.")
        _positive("gain", self.gain)
        _positive("rate", self.rate)

    def input_per_unit(self, cumulative: float) -> float:
        if cumulative <= 0:
            raise ProductionError("Cumulative output must be positive.")
        return float(self.floor + self.gain * cumulative ** (-self.rate))

    def curve(self, start: float, stop: float, samples: int = 80) -> tuple[Point, ...]:
        """Points ``(N, L(N))`` on an even grid from ``start`` to ``stop``."""
        if not 0 < start < stop or samples < 2:
            raise ProductionError("Need 0 < start < stop and at least two samples.")
        step = (stop - start) / (samples - 1)
        return tuple(
            (start + i * step, self.input_per_unit(start + i * step)) for i in range(samples)
        )

    def learning_index(self, cumulative: float) -> float:
        """Share of the first-unit input still needed at ``cumulative`` output."""
        return self.input_per_unit(cumulative) / self.input_per_unit(1.0)


@dataclass(frozen=True, slots=True)
class LearningAverageCost:
    """U-shaped average cost ``AC(q) = c + k (q - q0)^2``; learning scales ``c`` by
    ``1 - learning`` so the whole curve shifts down (the minimum stays at ``q0``)."""

    minimum_cost: float
    minimum_output: float
    curvature: float

    def __post_init__(self) -> None:
        _positive("minimum_cost", self.minimum_cost)
        _positive("minimum_output", self.minimum_output)
        _positive("curvature", self.curvature)

    def cost(self, output: float, learning: float = 0.0) -> float:
        if not 0 <= learning < 1:
            raise ProductionError("learning must lie in [0, 1).")
        base = self.minimum_cost * (1 - learning)
        return base + self.curvature * (output - self.minimum_output) ** 2


@dataclass(frozen=True, slots=True)
class ProductTransformation:
    """Two outputs from fixed inputs: ``(Q1 / M1)^bow + (Q2 / M2)^bow = 1``."""

    max_1: float
    max_2: float
    bow: float

    def __post_init__(self) -> None:
        _positive("max_1", self.max_1)
        _positive("max_2", self.max_2)
        _positive("bow", self.bow)

    def output_2(self, output_1: float) -> float:
        share = min(max(output_1 / self.max_1, 0.0), 1.0)
        return float(self.max_2 * (1.0 - share**self.bow) ** (1.0 / self.bow))

    def curve(self, samples: int = 80) -> tuple[Point, ...]:
        step = self.max_1 / (samples - 1)
        return tuple((i * step, self.output_2(i * step)) for i in range(samples))

    @property
    def economies_of_scope(self) -> bool:
        """True when the curve bows outward: producing both beats the straight-line trade-off."""
        return self.bow > 1.0

    def scope_degree(self, output_1: float, output_2: float) -> float:
        """``(cost of producing separately - joint cost) / joint cost`` with the cost of the
        resources used measured by the share of each maximum: separate production uses
        ``q1/M1 + q2/M2`` of the inputs, joint production only
        ``((q1/M1)^bow + (q2/M2)^bow)^(1/bow)``."""
        separate = output_1 / self.max_1 + output_2 / self.max_2
        joint = ((output_1 / self.max_1) ** self.bow + (output_2 / self.max_2) ** self.bow) ** (
            1.0 / self.bow
        )
        return float((separate - joint) / joint)


@dataclass(frozen=True, slots=True)
class TechnologyShift:
    """Total-product curves scaled up by each factor in ``factors`` (the first is the base)."""

    base: ShortRunProductionFunction
    factors: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.factors) < 2 or self.factors[0] != 1.0:
            raise ProductionError("Need at least two factors, the first equal to 1.")
        if list(self.factors) != sorted(self.factors) or len(set(self.factors)) != len(
            self.factors
        ):
            raise ProductionError("Factors must be strictly increasing.")

    def total_product(self, index: int, variable_input: float) -> float:
        return self.factors[index] * self.base.total_product(variable_input)


@dataclass(frozen=True, slots=True)
class ProductionFrontier:
    """Frontier ``Q = scale L^exponent`` (``0 < exponent < 1``: diminishing returns) and interior
    points ``(L, efficiency)`` with output ``efficiency * Q(L)`` and efficiency in ``(0, 1]``."""

    scale: float
    exponent: float
    interior: tuple[Point, ...] = ()

    def __post_init__(self) -> None:
        _positive("scale", self.scale)
        if not 0 < self.exponent < 1:
            raise ProductionError("exponent must lie in (0, 1).")
        for _, efficiency in self.interior:
            if not 0 < efficiency <= 1:
                raise ProductionError("efficiency must lie in (0, 1].")

    def output(self, labor: float) -> float:
        return float(self.scale * labor**self.exponent)

    def points(self) -> tuple[Point, ...]:
        """Interior points as ``(L, Q)``."""
        return tuple((labor, share * self.output(labor)) for labor, share in self.interior)

    def efficient(self, labor: float, output: float) -> bool:
        return abs(output - self.output(labor)) < 1e-9


def grid(start: float, stop: float, samples: int) -> Sequence[float]:
    """An even grid of ``samples`` values from ``start`` to ``stop``."""
    step = (stop - start) / (samples - 1)
    return [start + i * step for i in range(samples)]
