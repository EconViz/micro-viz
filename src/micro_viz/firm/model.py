"""High-level object-oriented interface for a firm."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Protocol, runtime_checkable

from micro_viz.firm.perfect_competition import CompetitiveOutcome, solve_competitive_firm


@runtime_checkable
class CostModel(Protocol):
    """Cost behavior required by :class:`Firm`."""

    fixed_cost: float

    def variable_cost(self, output: float) -> float: ...

    def total_cost(self, output: float) -> float: ...

    def marginal_cost(self, output: float) -> float: ...

    def average_variable_cost(self, output: float) -> float | None: ...

    def average_total_cost(self, output: float) -> float | None: ...


@dataclass(frozen=True, slots=True)
class Firm:
    """A firm composed from cost, production, and optional market models.

    ``Firm`` is deliberately a thin domain facade. Specialized calculations remain in the
    production, costs, and market-structure packages, while this object provides the operations
    shared by all firms.
    """

    cost: CostModel
    production: object | None = None
    market: object | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.cost, CostModel):
            raise TypeError("cost must provide the micro-viz cost model interface.")

    def total_cost(self, output: float) -> float:
        """Return total cost at ``output``."""
        return self.cost.total_cost(output)

    def average_cost(self, output: float) -> float | None:
        """Return average total cost, or ``None`` at zero output."""
        return self.cost.average_total_cost(output)

    def marginal_cost(self, output: float) -> float:
        """Return marginal cost at ``output``."""
        return self.cost.marginal_cost(output)

    def revenue(self, output: float, price: float) -> float:
        """Return ``price × output`` after validating both values."""
        quantity = self._nonnegative("output", output)
        unit_price = self._nonnegative("price", price)
        return unit_price * quantity

    def profit(self, output: float, price: float) -> float:
        """Return revenue minus total cost at a constant unit price."""
        return self.revenue(output, price) - self.total_cost(output)

    def competitive_outcome(self, price: float) -> CompetitiveOutcome:
        """Solve this firm's short-run outcome as a price taker."""
        return solve_competitive_firm(self.cost, price)  # type: ignore[arg-type]

    def in_market(self, market: object) -> Firm:
        """Return a copy associated with ``market``."""
        return replace(self, market=market)

    @staticmethod
    def _nonnegative(name: str, value: float) -> float:
        number = float(value)
        if not math.isfinite(number) or number < 0:
            raise ValueError(f"{name} must be finite and nonnegative.")
        return number


__all__ = ["CostModel", "Firm"]
