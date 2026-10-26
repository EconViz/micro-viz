"""Lowest points, price response and range checks of ``Cost``."""

from __future__ import annotations

import math
from collections.abc import Callable

from micro_viz.costs.formula._search import (
    _GRID,
    _bisect,
    _edge,
    _say,
    _upcrossing,
)
from micro_viz.costs.model import CostError, CostFunction, CubicCost, Extremum
from micro_viz.expr import Expression


class _Extrema(CostFunction):
    """Extreme points, output choice and checks, built on the state ``Cost`` sets up."""

    _tc_expr: Expression | None
    _mc_expr: Expression | None
    _cubic: CubicCost | None
    _table: tuple[tuple[float, ...], tuple[float, ...]] | None
    _language: str | None

    # ---- extreme points ----
    def min_mc(self) -> Extremum | None:
        """Where marginal cost is lowest, or ``None`` when it never falls first."""
        if self._cubic is not None:
            q = self._cubic.minimum_marginal_cost_output
        elif self._mc_expr is not None:
            slope = self._mc_expr.derivative()
            q_found = _upcrossing(lambda x: slope(x))
            q = q_found if q_found is not None else 0.0
        else:
            return None
        return Extremum(q, self.marginal_cost(q)) if q > 0 else None

    def min_avc(self) -> Extremum | None:
        """Where average variable cost is lowest (``MC = AVC`` there), or ``None`` when it is
        lowest at zero output."""
        if self._table is not None:
            return self._table_minimum(self.average_variable_cost)
        if self._cubic is not None:
            q = self._cubic.minimum_average_variable_cost_output
        else:
            q = _upcrossing(lambda x: x * self.marginal_cost(x) - self.variable_cost(x)) or 0.0
        return Extremum(q, self.variable_cost(q) / q) if q > 0 else None

    def min_atc(self) -> Extremum | None:
        """Where average total cost is lowest (``MC = ATC`` there), or ``None`` when it keeps
        falling."""
        if self._table is not None:
            return self._table_minimum(self.average_total_cost)
        if self._cubic is not None:
            q = self._cubic.minimum_average_total_cost_output
        elif self.fixed_cost > 0 and (found := self._quadratic_atc_minimum()) is not None:
            q = found
        else:
            q_found = _upcrossing(lambda x: x * self.marginal_cost(x) - self.total_cost(x))
            if q_found is None:
                return None
            q = q_found
        return Extremum(q, self.total_cost(q) / q) if q > 0 else None

    def _quadratic_atc_minimum(self) -> float | None:
        poly = self._tc_expr.coefficients() if self._tc_expr is not None else None
        if poly is None or set(poly) - {0.0, 1.0, 2.0} or poly.get(2.0, 0.0) <= 0:
            return None
        return math.sqrt(self.fixed_cost / poly[2.0])

    def _table_minimum(self, unit: Callable[[float], float | None]) -> Extremum | None:
        assert self._table is not None
        rows = [(x, unit(x)) for x in self._table[0] if x > 0]
        best = min(rows, key=lambda row: float(row[1]))  # type: ignore[arg-type]
        return Extremum(best[0], float(best[1]))  # type: ignore[arg-type]

    def shutdown_price(self) -> float:
        """The lowest average variable cost: below this price the firm produces nothing."""
        lowest = self.min_avc()
        return lowest.value if lowest is not None else self.marginal_cost(0.0)

    def breakeven_price(self) -> float | None:
        """The lowest average total cost, or ``None`` when ATC has no lowest point."""
        lowest = self.min_atc()
        return lowest.value if lowest is not None else None

    def output_at_price(self, price: float) -> float:
        """The profit-maximising output where ``price`` meets MC on its rising part (zero when
        the price is below MC everywhere)."""
        value = float(price)
        if self._table is not None:
            outputs, totals = self._table
            best = max(range(len(outputs)), key=lambda i: (value * outputs[i] - totals[i], -i))
            return outputs[best]
        if self._cubic is not None:
            b, c, d = self._cubic.linear, self._cubic.quadratic, self._cubic.cubic
            discriminant = 4 * c * c - 12 * d * (b - value)
            return (
                0.0 if discriminant < 0 else max(0.0, (-2 * c + math.sqrt(discriminant)) / (6 * d))
            )
        lowest = self.min_mc()
        floor = lowest.output if lowest is not None else 0.0
        if value < self.marginal_cost(floor):
            return 0.0
        high = max(1.0, 2 * floor)
        for _ in range(80):
            if self.marginal_cost(high) >= value:
                break
            high *= 2
        else:
            raise CostError(_say("cost.error.unbounded", self._language, price=value))
        return (
            _bisect(lambda x: self.marginal_cost(x) - value, floor, high)
            if self.marginal_cost(floor) < value
            else floor
        )

    # ---- checks ----
    def validate(self, output: tuple[float, float]) -> None:
        """Check the cost against economics over the output range ``(low, high)``.

        Fixed cost is not negative (checked when the cost is built), marginal cost is positive
        everywhere on the range, and so ``AVC <= ATC`` and total cost rises. Raises
        :class:`~micro_viz.costs.CostError` naming the interval of output where it fails.
        """
        low, high = float(output[0]), float(output[1])
        steps = _GRID - 1
        grid = [low + (high - low) * i / steps for i in range(_GRID)]
        bad = [x for x in grid if self.marginal_cost(x) <= 0]
        if not bad:
            return
        start = bad[0]
        index = grid.index(start)
        if index > 0:
            start = _edge(self.marginal_cost, grid[index - 1], start)
        stop = bad[-1]
        index = grid.index(stop)
        if index < steps:
            stop = _edge(self.marginal_cost, grid[index + 1], stop)
        raise CostError(
            _say(
                "cost.error.mc_not_positive",
                self._language,
                symbol=self.output_symbol,
                low=start,
                high=stop,
                at=bad[len(bad) // 2],
                mc=self.marginal_cost(bad[len(bad) // 2]),
            )
        )
