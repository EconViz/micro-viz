"""Renderer-neutral short-run production functions."""

from __future__ import annotations

import math
from dataclasses import dataclass


class ProductionError(ValueError):
    """Raised when a production model or analysis input is invalid."""


@dataclass(frozen=True, slots=True)
class ShortRunProductionFunction:
    """A textbook S-shaped short-run production function.

    The equation is ``Q(L) = aL + bL^2 + cL^3`` with ``a >= 0``, ``b > 0``
    and ``c < 0``. Under this sign convention marginal product first increases,
    then diminishes, and eventually becomes negative.
    """

    linear: float
    quadratic: float
    cubic: float
    input_symbol: str = "L"
    output_symbol: str = "Q"

    def __post_init__(self) -> None:
        coefficients = (self.linear, self.quadratic, self.cubic)
        if not all(math.isfinite(value) for value in coefficients):
            raise ProductionError("Production coefficients must be finite.")
        if self.linear < 0:
            raise ProductionError("The linear coefficient must be nonnegative.")
        if self.quadratic <= 0:
            raise ProductionError("The quadratic coefficient must be positive.")
        if self.cubic >= 0:
            raise ProductionError("The cubic coefficient must be negative.")
        if not self.input_symbol.strip() or not self.output_symbol.strip():
            raise ProductionError("Input and output symbols must be nonempty.")

    def total_product(self, variable_input: float) -> float:
        """Return total product ``Q(L)`` at a nonnegative input quantity."""
        value = self._input(variable_input)
        return self.linear * value + self.quadratic * value**2 + self.cubic * value**3

    def average_product(self, variable_input: float) -> float | None:
        """Return ``Q(L) / L``; it is undefined and represented by ``None`` at zero."""
        value = self._input(variable_input)
        if value == 0:
            return None
        return self.linear + self.quadratic * value + self.cubic * value**2

    def marginal_product(self, variable_input: float) -> float:
        """Return the derivative ``dQ/dL`` at a nonnegative input quantity."""
        value = self._input(variable_input)
        return self.linear + 2 * self.quadratic * value + 3 * self.cubic * value**2

    @property
    def inflection_input(self) -> float:
        """Input where marginal product stops increasing and starts diminishing."""
        return -self.quadratic / (3 * self.cubic)

    @property
    def total_product_max_input(self) -> float:
        """Positive input where marginal product is zero and total product peaks."""
        discriminant = (2 * self.quadratic) ** 2 - 12 * self.cubic * self.linear
        return (-2 * self.quadratic - math.sqrt(discriminant)) / (6 * self.cubic)

    def to_dict(self) -> dict[str, object]:
        """Serialize coefficients together with the equation and sign convention."""
        variable = self.input_symbol
        return {
            "equation": (
                f"{self.output_symbol}({variable}) = a{variable} + b{variable}^2 + c{variable}^3"
            ),
            "sign_convention": "a >= 0, b > 0, c < 0",
            "coefficients": {
                "a": self.linear,
                "b": self.quadratic,
                "c": self.cubic,
            },
            "input_symbol": self.input_symbol,
            "output_symbol": self.output_symbol,
        }

    @staticmethod
    def _input(variable_input: float) -> float:
        value = float(variable_input)
        if not math.isfinite(value):
            raise ProductionError("Variable input must be finite.")
        if value < 0:
            raise ProductionError("Variable input must be nonnegative.")
        return value


__all__ = ["ProductionError", "ShortRunProductionFunction"]
