"""The grammar as data: variables, functions, constants, left-hand names and limits."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace

from micro_viz.core.expr.errors import MessageProvider, default_messages
from micro_viz.core.expr.nodes import Node


@dataclass(frozen=True, slots=True)
class Function:
    """A function a formula may call, such as ``exp``.

    ``derivative(u)`` returns ``f'(u)`` as a tree in the argument ``u``; the engine applies the
    chain rule. ``antiderivative(u)`` returns ``F(u)`` with ``F' = f`` and is optional (without
    it an integral of a formula that uses the function is only found numerically).
    """

    name: str
    evaluate: Callable[[float], float]
    derivative: Callable[[Node], Node]
    antiderivative: Callable[[Node], Node] | None = None
    latex: str | None = None


@dataclass(frozen=True, slots=True)
class Limits:
    """Bounds that keep a formula cheap to read and to evaluate."""

    max_length: int = 200
    max_depth: int = 24
    max_exponent: float = 20.0
    max_number: float = 1e12
    max_variables: int = 1


@dataclass(frozen=True, slots=True)
class Registry:
    """What a formula may contain.

    ``variables`` maps every spelling to the canonical variable (``{"Q": "Q", "q": "Q"}``),
    ``heads`` every spelling of a name allowed left of ``=`` to its canonical name,
    ``constants`` names a number (``{"pi": 3.14159...}``), ``functions`` maps a name to a
    :class:`Function` and ``symbols`` gives the LaTeX of a canonical variable. ``messages``
    renders error texts (see :data:`micro_viz.core.expr.errors.MessageProvider`).
    """

    variables: Mapping[str, str]
    functions: Mapping[str, Function] = field(default_factory=dict)
    constants: Mapping[str, float] = field(default_factory=dict)
    heads: Mapping[str, str] = field(default_factory=dict)
    symbols: Mapping[str, str] = field(default_factory=dict)
    limits: Limits = field(default_factory=Limits)
    messages: MessageProvider = default_messages

    def variable(self, name: str) -> str | None:
        """The canonical variable spelled ``name``, or ``None``."""
        return self.variables.get(name)

    def head(self, name: str) -> str | None:
        """The canonical left-hand name spelled ``name`` (exact, else upper case), or ``None``."""
        return self.heads.get(name) or self.heads.get(name.upper())

    def function(self, name: str) -> Function | None:
        """The function called ``name`` (exact, else lower case), or ``None``."""
        return self.functions.get(name) or self.functions.get(name.lower())

    def evolve(self, **changes: object) -> Registry:
        """A copy with some fields replaced."""
        return replace(self, **changes)  # type: ignore[arg-type]
