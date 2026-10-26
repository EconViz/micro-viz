"""A small, safe formula engine: parse, evaluate, differentiate, integrate.

This subpackage is self-contained and is meant to be extracted into its own package later.
It uses only the standard library and imports nothing else from ``micro_viz``; the rest of
micro-viz reaches it only through the names exported here. What a formula may contain (variable
spellings, functions, constants, left-hand names, limits) and the words of its error messages
are supplied by the caller through a :class:`Registry`, so another package can register its own
variables (``Y``, ``C``) and functions without touching the parser.

The text is read by a hand-written tokenizer and parser. Nothing is passed to ``eval``,
``exec``, ``compile`` or ``ast``.

::

    from micro_viz.expr import Registry, functions, parse

    registry = Registry(variables={"Q": "Q", "q": "Q"}, functions={"exp": functions.EXP})
    cost = parse("TC = 200 + 120Q - 18Q^2 + Q^3", registry.evolve(heads={"TC": "TC"}))
    cost(9), cost.derivative()(9)
"""

from micro_viz.expr import functions
from micro_viz.expr.errors import ExprError, MessageProvider, default_messages
from micro_viz.expr.expression import Expression, parse
from micro_viz.expr.registry import Function, Limits, Registry

__all__ = [
    "ExprError",
    "Expression",
    "Function",
    "Limits",
    "MessageProvider",
    "Registry",
    "default_messages",
    "functions",
    "parse",
]
