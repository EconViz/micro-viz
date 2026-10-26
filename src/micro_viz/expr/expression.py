"""The public :class:`Expression`: evaluate, differentiate, integrate and print a formula."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Union

from micro_viz.expr import polynomial
from micro_viz.expr.calculus import antiderivative, derivative, quadrature, tidy
from micro_viz.expr.errors import ExprError
from micro_viz.expr.nodes import (
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
    to_latex,
    to_text,
    variables_of,
)
from micro_viz.expr.parser import parse_text
from micro_viz.expr.registry import Registry

Operand = Union["Expression", float, int]


class Expression:
    """A parsed formula. Immutable; calling it evaluates it.

    ``f = parse("100 - Q", registry)`` then ``f(30) == 70``. ``f.derivative()`` and
    ``f.integral()`` return new expressions (exact where the rules allow), ``f.variables`` is
    the set of canonical variable names, ``f.head`` the name left of ``=`` (or ``None``).
    """

    __slots__ = ("_node", "_poly_cache", "head", "registry", "source")

    def __init__(
        self, node: Node, registry: Registry, *, head: str | None = None, source: str | None = None
    ) -> None:
        self._node = node
        self.registry = registry
        self.head = head
        self.source = source if source is not None else to_text(node)
        self._poly_cache: dict[str, polynomial.Poly | None] = {}

    # ---- construction ----
    @classmethod
    def constant(cls, value: float, registry: Registry) -> Expression:
        return cls(Num(float(value)), registry)

    @classmethod
    def variable(cls, name: str, registry: Registry) -> Expression:
        canonical = registry.variable(name)
        if canonical is None:
            raise ExprError(
                "expr.unknown_name",
                source=name,
                position=0,
                provider=registry.messages,
                name=name,
                allowed=", ".join(sorted(set(registry.variables.values()))),
            )
        return cls(Var(canonical), registry)

    @classmethod
    def from_polynomial(
        cls, coefficients: Mapping[float, float], variable: str, registry: Registry
    ) -> Expression:
        """``sum(c * variable**k)`` from ``{k: c}``."""
        canonical = registry.variable(variable) or variable
        return cls(
            polynomial.from_poly({float(k): float(c) for k, c in coefficients.items()}, canonical),
            registry,
        )

    # ---- inspection ----
    @property
    def node(self) -> Node:
        return self._node

    @property
    def variables(self) -> frozenset[str]:
        """The canonical names of the variables the formula uses."""
        return variables_of(self._node)

    def _only(self, variable: str | None) -> str:
        names = sorted(self.variables)
        if variable is not None:
            return self.registry.variable(variable) or variable
        if len(names) == 1:
            return names[0]
        if not names:
            return sorted(set(self.registry.variables.values()))[0]
        raise ExprError(
            "expr.too_many_variables", provider=self.registry.messages, names=", ".join(names)
        )

    def coefficients(self, variable: str | None = None) -> dict[float, float] | None:
        """``{exponent: coefficient}`` for a polynomial in ``variable``, else ``None``."""
        name = self._only(variable)
        if name not in self._poly_cache:
            self._poly_cache[name] = polynomial.to_poly(self._node, name)
        poly = self._poly_cache[name]
        return None if poly is None else dict(poly)

    @property
    def is_polynomial(self) -> bool:
        return self.coefficients() is not None

    @property
    def degree(self) -> float | None:
        poly = self.coefficients()
        return None if poly is None else polynomial.degree(poly)

    # ---- evaluation ----
    def __call__(self, *args: float, **named: float) -> float:
        env = self._bind(args, named)
        poly = None
        names = self.variables
        if len(names) <= 1:
            (name,) = names or (None,)
            poly = self.coefficients(name) if name else None
            if poly is not None and name is not None:
                try:
                    value = polynomial.evaluate(poly, env[name])
                except (OverflowError, ValueError, ZeroDivisionError):
                    raise self._domain(env) from None
                return self._finite(value, env)
        return self._finite(self._eval(self._node, env), env)

    def _bind(self, args: tuple[float, ...], named: Mapping[str, float]) -> dict[str, float]:
        names = sorted(self.variables)
        env: dict[str, float] = {}
        for key, value in named.items():
            canonical = self.registry.variable(key) or key
            env[canonical] = float(value)
        if args and names:
            if len(args) > len(names):
                raise TypeError(f"expected at most {len(names)} argument(s), got {len(args)}")
            for name, value in zip(names, args, strict=False):
                env[name] = float(value)
        missing = [name for name in names if name not in env]
        if missing:
            raise TypeError(f"missing value for {', '.join(missing)}")
        return env

    def _domain(self, env: Mapping[str, float]) -> ExprError:
        return ExprError(
            "expr.not_finite",
            source=self.source,
            provider=self.registry.messages,
            at=", ".join(f"{k}={v:g}" for k, v in env.items()),
        )

    def _finite(self, value: float, env: Mapping[str, float]) -> float:
        if isinstance(value, complex) or not math.isfinite(value):
            raise self._domain(env)
        return float(value)

    def _eval(self, node: Node, env: Mapping[str, float]) -> float:
        try:
            return self._eval_unchecked(node, env)
        except ZeroDivisionError:
            raise ExprError(
                "expr.divide_by_zero_at",
                source=self.source,
                provider=self.registry.messages,
                at=", ".join(f"{k}={v:g}" for k, v in env.items()),
            ) from None
        except (ValueError, OverflowError):
            raise self._domain(env) from None

    def _eval_unchecked(self, node: Node, env: Mapping[str, float]) -> float:
        if isinstance(node, Num):
            return node.value
        if isinstance(node, Var):
            return env[node.name]
        if isinstance(node, Neg):
            return -self._eval_unchecked(node.arg, env)
        if isinstance(node, Add):
            return math.fsum(self._eval_unchecked(t, env) for t in node.terms)
        if isinstance(node, Mul):
            product = 1.0
            for factor in node.factors:
                product *= self._eval_unchecked(factor, env)
            return product
        if isinstance(node, Div):
            return self._eval_unchecked(node.numerator, env) / self._eval_unchecked(
                node.denominator, env
            )
        if isinstance(node, Pow):
            value = self._eval_unchecked(node.base, env) ** self._eval_unchecked(node.exponent, env)
            if isinstance(value, complex):
                raise ValueError("complex")
            return float(value)
        function = self.registry.functions[node.function]
        return float(function.evaluate(self._eval_unchecked(node.arg, env)))

    # ---- calculus ----
    def derivative(self, variable: str | None = None) -> Expression:
        """``d/d variable`` as a new expression (exact)."""
        name = self._only(variable)
        return Expression(derivative(self._node, name, self.registry.functions), self.registry)

    def integral(self, variable: str | None = None, *, lower: float = 0.0) -> Expression:
        """The antiderivative that is zero at ``variable = lower``; raises :class:`ExprError`
        when the formula has no closed-form antiderivative among the supported rules."""
        name = self._only(variable)
        try:
            anti = antiderivative(self._node, name, self.registry.functions)
        except ExprError as error:
            raise error.with_context(source=self.source, provider=self.registry.messages) from None
        result = Expression(anti, self.registry)
        offset = result(**{name: lower}) if lower is not None else 0.0
        if offset != 0:
            result = result - offset
        return result

    def integral_between(self, low: float, high: float, variable: str | None = None) -> float:
        """The definite integral: exact when an antiderivative exists, else by quadrature."""
        name = self._only(variable)
        try:
            anti = antiderivative(self._node, name, self.registry.functions)
        except ExprError:
            return quadrature(lambda x: self(**{name: x}), low, high)
        result = Expression(anti, self.registry)
        return result(**{name: high}) - result(**{name: low})

    def substitute(self, variable: str, value: Operand) -> Expression:
        """Replace ``variable`` by a number or expression."""
        name = self.registry.variable(variable) or variable
        replacement = value.node if isinstance(value, Expression) else Num(float(value))
        return Expression(tidy(_substitute(self._node, name, replacement)), self.registry)

    # ---- arithmetic (same registry) ----
    def _lift(self, other: Operand) -> Node:
        return other.node if isinstance(other, Expression) else Num(float(other))

    def __add__(self, other: Operand) -> Expression:
        return Expression(tidy(add(self._node, self._lift(other))), self.registry)

    __radd__ = __add__

    def __sub__(self, other: Operand) -> Expression:
        return Expression(tidy(add(self._node, neg(self._lift(other)))), self.registry)

    def __rsub__(self, other: Operand) -> Expression:
        return Expression(tidy(add(self._lift(other), neg(self._node))), self.registry)

    def __mul__(self, other: Operand) -> Expression:
        return Expression(tidy(mul(self._node, self._lift(other))), self.registry)

    __rmul__ = __mul__

    def __truediv__(self, other: Operand) -> Expression:
        return Expression(tidy(divide(self._node, self._lift(other))), self.registry)

    def __neg__(self) -> Expression:
        return Expression(tidy(neg(self._node)), self.registry)

    # ---- output ----
    def to_latex(self) -> str:
        """The formula as LaTeX, with the registry's symbols for the variables."""
        return to_latex(self._node, dict(self.registry.symbols))

    def __str__(self) -> str:
        return to_text(self._node)

    def __repr__(self) -> str:
        return f"Expression({to_text(self._node)!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Expression) and self._node == other._node

    def __hash__(self) -> int:
        return hash(self._node)


def _substitute(node: Node, name: str, replacement: Node) -> Node:
    if isinstance(node, Var):
        return replacement if node.name == name else node
    if isinstance(node, Num):
        return node
    if isinstance(node, Neg):
        return neg(_substitute(node.arg, name, replacement))
    if isinstance(node, Add):
        return add(*(_substitute(t, name, replacement) for t in node.terms))
    if isinstance(node, Mul):
        return mul(*(_substitute(t, name, replacement) for t in node.factors))
    if isinstance(node, Div):
        return divide(
            _substitute(node.numerator, name, replacement),
            _substitute(node.denominator, name, replacement),
        )
    if isinstance(node, Pow):
        return Pow(_substitute(node.base, name, replacement), node.exponent)
    return Call(node.function, _substitute(node.arg, name, replacement))


def parse(text: str, registry: Registry, *, language: str | None = None) -> Expression:
    """Read ``text`` (an expression, or ``HEAD = expression``) into an :class:`Expression`.

    Raises :class:`~micro_viz.expr.errors.ExprError` for anything that is not a valid formula
    under ``registry``; the formula is read by this module's parser and is never executed.
    """
    parsed = parse_text(text, registry, language)
    return Expression(tidy(parsed.node), registry, head=parsed.head, source=parsed.source)
