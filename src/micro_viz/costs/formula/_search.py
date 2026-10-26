"""Numeric search helpers and message plumbing of ``Cost``."""

from __future__ import annotations

from collections.abc import Callable

from micro_viz.costs.model import CostError
from micro_viz.expr import ExprError, Expression
from micro_viz.formulas import FormulaError, render_message

_TOL = 1e-9
_SCAN_START = 1e-6
_SCAN_STOP = 1e9
_SCAN_FACTOR = 1.02
_BISECT_ROUNDS = 200
_GRID = 1201


def _say(key: str, language: str | None = None, **fields: object) -> str:
    return render_message(key, language, fields)


def _bisect(function: Callable[[float], float], low: float, high: float) -> float:
    """The root of ``function`` between ``low`` (negative) and ``high`` (nonnegative)."""
    for _ in range(_BISECT_ROUNDS):
        middle = (low + high) / 2
        if middle in (low, high):
            break
        if function(middle) < 0:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def _upcrossing(function: Callable[[float], float]) -> float | None:
    """The smallest ``q > 0`` where ``function`` goes from negative to nonnegative.

    ``0.0`` when it is not negative just above zero, ``None`` when it never crosses.
    """
    q = _SCAN_START
    try:
        if function(q) >= 0:
            return 0.0
        while q < _SCAN_STOP:
            nxt = q * _SCAN_FACTOR
            if function(nxt) >= 0:
                return _bisect(function, q, nxt)
            q = nxt
    except (ArithmeticError, ValueError, ExprError):
        return None
    return None


def _no_numeric(x: float) -> float:
    return 0.0


def _with_head(expression: Expression, head: str) -> Expression:
    return Expression(expression.node, expression.registry, head=head)


def _edge(function: Callable[[float], float], good: float, bad: float) -> float:
    """The boundary between a point where ``function > 0`` (``good``) and one where it does not."""
    for _ in range(_BISECT_ROUNDS):
        middle = (good + bad) / 2
        if middle in (good, bad):
            break
        if function(middle) > 0:
            good = middle
        else:
            bad = middle
    return (good + bad) / 2


def _as_cost_error(error: ExprError, language: str | None) -> CostError:
    return FormulaError(
        error.message_id,
        source=error.source,
        position=error.position,
        provider=render_message,
        language=language,
        **error.fields,
    )
