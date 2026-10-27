"""A production function from a formula, callable, or production schedule."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

from micro_viz.core.expr import ExprError, Expression, Limits, Registry, functions, parse
from micro_viz.core.formulas import render_message
from micro_viz.firm.production.model import ProductionError

_LABOR = "L"
_OUTPUT = "Q"
_REGISTRY = Registry(
    variables={"L": _LABOR, "l": _LABOR},
    functions={"exp": functions.EXP, "ln": functions.LN, "sqrt": functions.SQRT},
    heads={"Q": _OUTPUT, "q": _OUTPUT},
    symbols={_LABOR: "L", _OUTPUT: "Q"},
    limits=Limits(),
    messages=render_message,
)


class ProductionFunction:
    """A one-input production function ``Q = f(L)``.

    Construct it from a textbook formula, or use :meth:`from_callable` or
    :meth:`from_table`. Table rows are joined by straight segments so diagrams and marginal
    products remain defined between observations.
    """

    _expression: Expression | None
    _marginal_expression: Expression | None
    _callable: Callable[[float], float] | None
    _table: tuple[tuple[float, ...], tuple[float, ...]] | None

    def __init__(
        self,
        formula: str | Expression,
        *,
        input_symbol: str = "L",
        output_symbol: str = "Q",
        language: str | None = None,
    ) -> None:
        try:
            expression = (
                formula
                if isinstance(formula, Expression)
                else parse(formula, _REGISTRY, language=language)
            )
        except ExprError as error:
            raise ProductionError(str(error)) from None
        if expression.head not in (None, _OUTPUT):
            raise ProductionError("A production formula must define Q.")
        if expression.variables - {_LABOR}:
            raise ProductionError("A production formula may only use labor L.")
        self.input_symbol = self._symbol("input_symbol", input_symbol)
        self.output_symbol = self._symbol("output_symbol", output_symbol)
        self._expression = expression
        self._marginal_expression = expression.derivative(_LABOR)
        self._callable: Callable[[float], float] | None = None
        self._table: tuple[tuple[float, ...], tuple[float, ...]] | None = None

    @classmethod
    def from_callable(
        cls,
        function: Callable[[float], float],
        *,
        input_symbol: str = "L",
        output_symbol: str = "Q",
    ) -> ProductionFunction:
        """Build a continuous production function from a Python callable."""
        if not callable(function):
            raise TypeError("function must be callable.")
        self = cls.__new__(cls)
        self.input_symbol = cls._symbol("input_symbol", input_symbol)
        self.output_symbol = cls._symbol("output_symbol", output_symbol)
        self._expression = None
        self._marginal_expression = None
        self._callable = function
        self._table = None
        self._evaluate_callable(0.0)
        return self

    @classmethod
    def from_table(
        cls,
        *,
        labor: Sequence[float],
        output: Sequence[float],
        input_symbol: str = "L",
        output_symbol: str = "Q",
    ) -> ProductionFunction:
        """Build a production schedule from increasing labor and nonnegative output rows."""
        inputs = tuple(float(value) for value in labor)
        outputs = tuple(float(value) for value in output)
        invalid = (
            len(inputs) != len(outputs)
            or len(inputs) < 2
            or inputs[0] != 0
            or any(right <= left for left, right in zip(inputs, inputs[1:], strict=False))
            or any(not math.isfinite(value) for value in (*inputs, *outputs))
            or any(value < 0 for value in outputs)
        )
        if invalid:
            raise ProductionError(
                "labor and output must have equal lengths, start at labor 0, and contain "
                "finite, increasing labor with nonnegative output."
            )
        self = cls.__new__(cls)
        self.input_symbol = cls._symbol("input_symbol", input_symbol)
        self.output_symbol = cls._symbol("output_symbol", output_symbol)
        self._expression = None
        self._marginal_expression = None
        self._callable = None
        self._table = (inputs, outputs)
        return self

    @property
    def capacity(self) -> float:
        """Largest tabulated input, or infinity for a formula or callable."""
        return self._table[0][-1] if self._table is not None else math.inf

    @property
    def formula(self) -> str:
        """Human-readable source of the production function."""
        if self._expression is not None:
            return f"{self.output_symbol} = {self._expression}"
        if self._table is not None:
            return f"{self.output_symbol} from a table of {len(self._table[0])} rows"
        return f"{self.output_symbol} = f({self.input_symbol})"

    def total_product(self, variable_input: float) -> float:
        """Return total product at a nonnegative input."""
        value = self._input(variable_input)
        if self._expression is not None:
            result = self._expression(value)
        elif self._table is not None:
            result, _ = self._interpolate(value)
        else:
            result = self._evaluate_callable(value)
        if result < 0:
            raise ProductionError("Total product must be nonnegative.")
        return result

    def average_product(self, variable_input: float) -> float | None:
        """Return ``Q(L) / L``, or ``None`` at zero input."""
        value = self._input(variable_input)
        return None if value == 0 else self.total_product(value) / value

    def marginal_product(self, variable_input: float) -> float:
        """Return exact, piecewise, or numerically differentiated marginal product."""
        value = self._input(variable_input)
        if self._marginal_expression is not None:
            return self._marginal_expression(value)
        if self._table is not None:
            return self._interpolate(value)[1]
        step = 1e-5 * max(1.0, value)
        if value < step:
            return (self._evaluate_callable(value + step) - self._evaluate_callable(value)) / step
        return (self._evaluate_callable(value + step) - self._evaluate_callable(value - step)) / (
            2 * step
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize the source and symbols."""
        data: dict[str, object] = {
            "formula": self.formula,
            "input_symbol": self.input_symbol,
            "output_symbol": self.output_symbol,
        }
        if self._table is not None:
            data["labor"], data["output"] = (list(values) for values in self._table)
        return data

    def _input(self, variable_input: float) -> float:
        value = float(variable_input)
        if not math.isfinite(value) or value < 0:
            raise ProductionError("Variable input must be finite and nonnegative.")
        if value > self.capacity:
            raise ProductionError(f"Variable input {value} exceeds the table capacity.")
        return value

    def _interpolate(self, value: float) -> tuple[float, float]:
        assert self._table is not None
        inputs, outputs = self._table
        if value == inputs[-1]:
            low = len(inputs) - 2
        else:
            low, high = 0, len(inputs) - 1
            while high - low > 1:
                middle = (low + high) // 2
                if inputs[middle] <= value:
                    low = middle
                else:
                    high = middle
        slope = (outputs[low + 1] - outputs[low]) / (inputs[low + 1] - inputs[low])
        return outputs[low] + slope * (value - inputs[low]), slope

    def _evaluate_callable(self, value: float) -> float:
        assert self._callable is not None
        try:
            result = float(self._callable(value))
        except (TypeError, ValueError, OverflowError) as error:
            raise ProductionError(f"Production callable failed at {value:g}: {error}") from None
        if not math.isfinite(result):
            raise ProductionError(f"Production callable must be finite at {value:g}.")
        return result

    @staticmethod
    def _symbol(name: str, value: str) -> str:
        if not value.strip():
            raise ProductionError(f"{name} must be nonempty.")
        return value


__all__ = ["ProductionFunction"]
