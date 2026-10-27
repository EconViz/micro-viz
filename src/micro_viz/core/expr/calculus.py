"""Exact derivatives and integrals of expression trees, and numeric quadrature."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from micro_viz.core.expr.errors import ExprError
from micro_viz.core.expr.nodes import (
    ONE,
    ZERO,
    Add,
    Call,
    Div,
    Mul,
    Neg,
    Node,
    Num,
    Pow,
    Var,
    add,
    divide,
    mul,
    neg,
    power,
    variables_of,
)
from micro_viz.core.expr.polynomial import from_poly, to_poly
from micro_viz.core.expr.registry import Function


def tidy(node: Node) -> Node:
    """Rewrite a one-variable polynomial in canonical form; other trees are left as built."""
    names = variables_of(node)
    if len(names) == 1:
        (name,) = names
        poly = to_poly(node, name)
        if poly is not None:
            return from_poly(poly, name)
    elif not names:
        poly = to_poly(node, "_")
        if poly is not None:
            return Num(poly.get(0.0, 0.0))
    return node


def derivative(node: Node, variable: str, functions: Mapping[str, Function]) -> Node:
    """``d node / d variable``."""
    return tidy(_d(node, variable, functions))


def _d(node: Node, v: str, fns: Mapping[str, Function]) -> Node:
    if isinstance(node, Num):
        return ZERO
    if isinstance(node, Var):
        return ONE if node.name == v else ZERO
    if isinstance(node, Neg):
        return neg(_d(node.arg, v, fns))
    if isinstance(node, Add):
        return add(*(_d(term, v, fns) for term in node.terms))
    if isinstance(node, Mul):
        parts = []
        for i, factor in enumerate(node.factors):
            rest = [f for j, f in enumerate(node.factors) if j != i]
            parts.append(mul(_d(factor, v, fns), *rest))
        return add(*parts)
    if isinstance(node, Div):
        top, bottom = node.numerator, node.denominator
        return add(
            divide(_d(top, v, fns), bottom),
            neg(divide(mul(top, _d(bottom, v, fns)), power(bottom, Num(2.0)))),
        )
    if isinstance(node, Pow):
        if isinstance(node.exponent, Num):
            n = node.exponent.value
            return mul(Num(n), power(node.base, Num(n - 1)), _d(node.base, v, fns))
        raise ExprError("expr.derivative_unsupported")  # pragma: no cover - parser forbids it
    function = fns.get(node.function)
    if function is None:  # pragma: no cover - parser only builds registered calls
        raise ExprError("expr.derivative_unsupported")
    return mul(function.derivative(node.arg), _d(node.arg, v, fns))


def _unsupported() -> ExprError:
    return ExprError("expr.integral_unsupported")


def _is_free(node: Node, v: str) -> bool:
    return v not in variables_of(node)


def _linear(node: Node, v: str) -> tuple[float, float] | None:
    poly = to_poly(node, v)
    if poly is None or any(k not in (0.0, 1.0) for k in poly) or poly.get(1.0, 0.0) == 0:
        return None
    return poly[1.0], poly.get(0.0, 0.0)


def antiderivative(node: Node, variable: str, functions: Mapping[str, Function]) -> Node:
    """An antiderivative of ``node``; raises :class:`ExprError` when none is known."""
    return tidy(_integrate(node, variable, functions))


def _integrate(node: Node, v: str, fns: Mapping[str, Function]) -> Node:
    if _is_free(node, v):
        return mul(node, Var(v))
    poly = to_poly(node, v)
    if poly is not None:
        out: dict[float, float] = {}
        for k, c in poly.items():
            if k == -1:
                raise _unsupported()
            out[k + 1] = c / (k + 1)
        return from_poly(out, v)
    if isinstance(node, Neg):
        return neg(_integrate(node.arg, v, fns))
    if isinstance(node, Add):
        return add(*(_integrate(term, v, fns) for term in node.terms))
    if isinstance(node, Mul):
        free = [f for f in node.factors if _is_free(f, v)]
        rest = [f for f in node.factors if not _is_free(f, v)]
        if free and rest:
            return mul(*free, _integrate(mul(*rest), v, fns))
        raise _unsupported()
    if isinstance(node, Div) and _is_free(node.denominator, v):
        return divide(_integrate(node.numerator, v, fns), node.denominator)
    if isinstance(node, Pow) and isinstance(node.exponent, Num):
        line = _linear(node.base, v)
        n = node.exponent.value
        if line is not None and n != -1:
            return divide(power(node.base, Num(n + 1)), Num((n + 1) * line[0]))
        raise _unsupported()
    if isinstance(node, Call):
        function = fns.get(node.function)
        line = _linear(node.arg, v)
        if function is not None and function.antiderivative is not None and line is not None:
            return divide(function.antiderivative(node.arg), Num(line[0]))
    raise _unsupported()


_GL_X = (
    0.0,
    0.5384693101056831,
    -0.5384693101056831,
    0.9061798459386640,
    -0.9061798459386640,
)
_GL_W = (
    0.5688888888888889,
    0.4786286704993665,
    0.4786286704993665,
    0.2369268850561891,
    0.2369268850561891,
)


def quadrature(
    function: Callable[[float], float], low: float, high: float, *, tolerance: float = 1e-13
) -> float:
    """``integral of function`` over ``[low, high]`` by composite Gauss-Legendre, refined until
    two successive estimates agree to ``tolerance`` (relative)."""
    if low == high:
        return 0.0

    def estimate(panels: int) -> float:
        width = (high - low) / panels
        total = 0.0
        for index in range(panels):
            centre = low + (index + 0.5) * width
            half = width / 2
            total += half * sum(
                w * function(centre + half * x) for x, w in zip(_GL_X, _GL_W, strict=True)
            )
        return total

    previous = estimate(4)
    panels = 8
    while panels <= 4096:
        current = estimate(panels)
        if abs(current - previous) <= tolerance * max(1.0, abs(current)):
            return current
        previous, panels = current, panels * 2
    return previous


__all__ = ["antiderivative", "derivative", "quadrature", "tidy"]
