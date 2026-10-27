"""Ready-made :class:`Function` values a registry may include: ``exp``, ``ln`` and ``sqrt``."""

from __future__ import annotations

import math

from micro_viz.core.expr.nodes import ONE, Call, Num, Pow, add, divide, mul, neg, power
from micro_viz.core.expr.registry import Function

EXP = Function(
    "exp",
    math.exp,
    derivative=lambda u: Call("exp", u),
    antiderivative=lambda u: Call("exp", u),
)
LN = Function(
    "ln",
    math.log,
    derivative=lambda u: divide(ONE, u),
    antiderivative=lambda u: add(mul(u, Call("ln", u)), neg(u)),
)
SQRT = Function(
    "sqrt",
    math.sqrt,
    derivative=lambda u: mul(Num(0.5), power(u, Num(-0.5))),
    antiderivative=lambda u: mul(Num(2.0 / 3.0), Pow(u, Num(1.5))),
)

__all__ = ["EXP", "LN", "SQRT"]
