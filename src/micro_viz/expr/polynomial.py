"""Generalized polynomials ``{exponent: coefficient}`` in one variable (real exponents)."""

from __future__ import annotations

from micro_viz.expr.nodes import (
    ZERO,
    Add,
    Div,
    Mul,
    Neg,
    Node,
    Num,
    Pow,
    Var,
    mul,
    power,
)

Poly = dict[float, float]
MAX_POWER = 24
MAX_TERMS = 64


def _mul(left: Poly, right: Poly) -> Poly | None:
    out: Poly = {}
    for p, a in left.items():
        for q, b in right.items():
            out[p + q] = out.get(p + q, 0.0) + a * b
    out = {k: v for k, v in out.items() if v != 0}
    return out if len(out) <= MAX_TERMS else None


def _add(left: Poly, right: Poly) -> Poly:
    out = dict(left)
    for k, v in right.items():
        out[k] = out.get(k, 0.0) + v
    return {k: v for k, v in out.items() if v != 0}


def to_poly(node: Node, variable: str) -> Poly | None:
    """The tree as a polynomial in ``variable``, or ``None`` when it is not one."""
    if isinstance(node, Num):
        return {0.0: node.value} if node.value != 0 else {}
    if isinstance(node, Var):
        return {1.0: 1.0} if node.name == variable else None
    if isinstance(node, Neg):
        inner = to_poly(node.arg, variable)
        return None if inner is None else {k: -v for k, v in inner.items()}
    if isinstance(node, Add):
        total: Poly = {}
        for term in node.terms:
            part = to_poly(term, variable)
            if part is None:
                return None
            total = _add(total, part)
        return total
    if isinstance(node, Mul):
        product: Poly = {0.0: 1.0}
        for factor in node.factors:
            part = to_poly(factor, variable)
            if part is None:
                return None
            product_next = _mul(product, part)
            if product_next is None:
                return None
            product = product_next
        return product
    if isinstance(node, Div):
        top = to_poly(node.numerator, variable)
        bottom = to_poly(node.denominator, variable)
        if top is None or bottom is None or len(bottom) != 1:
            return None
        ((k, c),) = bottom.items()
        return _mul(top, {-k: 1.0 / c})
    if isinstance(node, Pow):
        if not isinstance(node.exponent, Num):
            return None
        n = node.exponent.value
        base = to_poly(node.base, variable)
        if base is None:
            return None
        if len(base) == 1:
            ((k, c),) = base.items()
            if c > 0 or n == int(n):
                return {k * n: c**n}
            return None
        if n == int(n) and 0 <= n <= MAX_POWER:
            result: Poly | None = {0.0: 1.0}
            for _ in range(int(n)):
                result = _mul(result, base)  # type: ignore[arg-type]
                if result is None:
                    return None
            return result
        return None
    return None


def from_poly(poly: Poly, variable: str) -> Node:
    """A tree for the polynomial: terms in ascending exponent, ``200 + 120Q - 18Q^2 + Q^3``."""
    terms: list[Node] = []
    for exponent in sorted(poly):
        coefficient = poly[exponent]
        if coefficient == 0:
            continue
        if exponent == 0:
            terms.append(Num(coefficient))
            continue
        base: Node = Var(variable) if exponent == 1 else power(Var(variable), Num(exponent))
        terms.append(base if coefficient == 1 else mul(Num(coefficient), base))
    if not terms:
        return ZERO
    return terms[0] if len(terms) == 1 else Add(tuple(terms))


def degree(poly: Poly) -> float:
    return max(poly, default=0.0)


def evaluate(poly: Poly, x: float) -> float:
    """Evaluate (Horner for a dense integer polynomial, else term by term)."""
    if all(k == int(k) and k >= 0 for k in poly) and poly:
        top = int(max(poly))
        if top <= MAX_POWER:
            value = 0.0
            for exponent in range(top, -1, -1):
                value = value * x + poly.get(float(exponent), 0.0)
            return value
    total = 0.0
    for k, c in poly.items():
        total += c * (x**k)
    if isinstance(total, complex):
        raise ValueError("complex")
    return total
