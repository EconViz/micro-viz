"""Immutable expression trees, simplifying constructors and the text and LaTeX printers."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Num:
    value: float


@dataclass(frozen=True, slots=True)
class Var:
    name: str


@dataclass(frozen=True, slots=True)
class Neg:
    arg: Node


@dataclass(frozen=True, slots=True)
class Add:
    terms: tuple[Node, ...]


@dataclass(frozen=True, slots=True)
class Mul:
    factors: tuple[Node, ...]


@dataclass(frozen=True, slots=True)
class Div:
    numerator: Node
    denominator: Node


@dataclass(frozen=True, slots=True)
class Pow:
    base: Node
    exponent: Node


@dataclass(frozen=True, slots=True)
class Call:
    function: str
    arg: Node


Node = Num | Var | Neg | Add | Mul | Div | Pow | Call

ZERO = Num(0.0)
ONE = Num(1.0)


def is_num(node: Node, value: float | None = None) -> bool:
    return isinstance(node, Num) and (value is None or node.value == value)


def depth(node: Node) -> int:
    """Height of the tree."""
    if isinstance(node, Num | Var):
        return 1
    if isinstance(node, Neg | Call):
        return 1 + depth(node.arg)
    if isinstance(node, Add):
        return 1 + max(depth(t) for t in node.terms)
    if isinstance(node, Mul):
        return 1 + max(depth(t) for t in node.factors)
    if isinstance(node, Div):
        return 1 + max(depth(node.numerator), depth(node.denominator))
    return 1 + max(depth(node.base), depth(node.exponent))


def variables_of(node: Node) -> frozenset[str]:
    """The variable names in a tree."""
    if isinstance(node, Num):
        return frozenset()
    if isinstance(node, Var):
        return frozenset((node.name,))
    if isinstance(node, Neg | Call):
        return variables_of(node.arg)
    if isinstance(node, Add):
        return frozenset().union(*(variables_of(t) for t in node.terms))
    if isinstance(node, Mul):
        return frozenset().union(*(variables_of(t) for t in node.factors))
    if isinstance(node, Div):
        return variables_of(node.numerator) | variables_of(node.denominator)
    return variables_of(node.base) | variables_of(node.exponent)


# ---- simplifying constructors ------------------------------------------------------------


def neg(arg: Node) -> Node:
    if isinstance(arg, Num):
        return Num(-arg.value) if arg.value != 0 else ZERO
    if isinstance(arg, Neg):
        return arg.arg
    return Neg(arg)


def add(*terms: Node) -> Node:
    flat: list[Node] = []
    constant = 0.0
    for term in terms:
        parts = term.terms if isinstance(term, Add) else (term,)
        for part in parts:
            if isinstance(part, Num):
                constant += part.value
            else:
                flat.append(part)
    if constant != 0 or not flat:
        flat.append(Num(constant))
    if len(flat) == 1:
        return flat[0]
    return Add(tuple(flat))


def mul(*factors: Node) -> Node:
    flat: list[Node] = []
    constant = 1.0
    for factor in factors:
        parts = factor.factors if isinstance(factor, Mul) else (factor,)
        for part in parts:
            if isinstance(part, Num):
                constant *= part.value
            elif isinstance(part, Neg):
                constant *= -1.0
                flat.append(part.arg)
            else:
                flat.append(part)
    if constant == 0:
        return ZERO
    if constant != 1 or not flat:
        flat.insert(0, Num(constant))
    if len(flat) == 1:
        return flat[0]
    return Mul(tuple(flat))


def power(base: Node, exponent: Node) -> Node:
    if is_num(exponent, 0.0):
        return ONE
    if is_num(exponent, 1.0):
        return base
    if isinstance(base, Num) and isinstance(exponent, Num):
        try:
            value = base.value**exponent.value
        except (OverflowError, ZeroDivisionError):
            return Pow(base, exponent)
        if isinstance(value, float) and math.isfinite(value):
            return Num(value)
        return Pow(base, exponent)
    if is_num(base, 1.0):
        return ONE
    if isinstance(base, Pow) and isinstance(base.exponent, Num) and isinstance(exponent, Num):
        return Pow(base.base, Num(base.exponent.value * exponent.value))
    return Pow(base, exponent)


def divide(numerator: Node, denominator: Node) -> Node:
    if isinstance(denominator, Num) and denominator.value != 0:
        return mul(Num(1.0 / denominator.value), numerator)
    if is_num(numerator, 0.0):
        return ZERO
    return Div(numerator, denominator)


# ---- printers ----------------------------------------------------------------------------


def format_number(value: float) -> str:
    if value == int(value) and abs(value) < 1e15:
        return str(int(value))
    return repr(round(value, 12)) if abs(value) < 1e15 else repr(value)


_ATOM, _POWER, _PRODUCT, _SUM = 4, 3, 2, 1


def _prec(node: Node) -> int:
    if isinstance(node, Num):
        return _ATOM if node.value >= 0 else _SUM
    if isinstance(node, Var | Call):
        return _ATOM
    if isinstance(node, Pow):
        return _POWER
    if isinstance(node, Mul | Div):
        return _PRODUCT
    return _SUM


def _wrap(text: str, node: Node, need: int) -> str:
    return f"({text})" if _prec(node) < need else text


def to_text(node: Node) -> str:
    """The formula as plain text: ``200 + 120Q - 18Q^2 + Q^3``."""
    if isinstance(node, Num):
        return format_number(node.value)
    if isinstance(node, Var):
        return node.name
    if isinstance(node, Neg):
        return "-" + _wrap(to_text(node.arg), node.arg, _POWER)
    if isinstance(node, Call):
        return f"{node.function}({to_text(node.arg)})"
    if isinstance(node, Pow):
        return (
            _wrap(to_text(node.base), node.base, _ATOM)
            + "^"
            + _wrap(to_text(node.exponent), node.exponent, _ATOM)
        )
    if isinstance(node, Div):
        return (
            _wrap(to_text(node.numerator), node.numerator, _POWER)
            + "/"
            + _wrap(to_text(node.denominator), node.denominator, _ATOM)
        )
    if isinstance(node, Mul):
        pieces: list[str] = []
        for index, factor in enumerate(node.factors):
            if index == 0 and isinstance(factor, Num):
                if factor.value == -1 and len(node.factors) > 1:
                    pieces.append("-")
                else:
                    pieces.append(format_number(factor.value))
                continue
            text = _wrap(to_text(factor), factor, _POWER)
            if isinstance(factor, Num):
                pieces.append("*" + text)
            elif pieces and pieces[-1][-1:].isalpha() and text[:1].isalpha():
                pieces.append(" " + text)  # "Q exp(Q)": adjacent letters would read as one name
            else:
                pieces.append(text)
        return "".join(pieces)
    parts: list[str] = []
    for index, term in enumerate(node.terms):
        sign, body = _signed(term)
        if index == 0:
            parts.append(("-" if sign < 0 else "") + body)
        else:
            parts.append((" - " if sign < 0 else " + ") + body)
    return "".join(parts)


def _split_sign(term: Node) -> tuple[int, Node]:
    if isinstance(term, Num) and term.value < 0:
        return -1, Num(-term.value)
    if isinstance(term, Neg):
        return -1, term.arg
    if isinstance(term, Mul) and isinstance(term.factors[0], Num) and term.factors[0].value < 0:
        return -1, mul(Num(-term.factors[0].value), *term.factors[1:])
    return 1, term


def _signed(term: Node) -> tuple[int, str]:
    sign, rest = _split_sign(term)
    text = to_text(rest)
    return sign, f"({text})" if sign < 0 and isinstance(rest, Add) else text


def to_latex(node: Node, symbols: dict[str, str] | None = None) -> str:
    """The formula as LaTeX; ``symbols`` maps a variable name to its LaTeX."""
    names = symbols or {}
    if isinstance(node, Num):
        return format_number(node.value)
    if isinstance(node, Var):
        return names.get(node.name, node.name)
    if isinstance(node, Neg):
        return "-" + _wrap_tex(node.arg, _POWER, names)
    if isinstance(node, Call):
        inner = to_latex(node.arg, names)
        if node.function == "sqrt":
            return rf"\sqrt{{{inner}}}"
        return (
            rf"\{node.function}\left({inner}\right)"
            if node.function in {"exp", "ln"}
            else (rf"\operatorname{{{node.function}}}\left({inner}\right)")
        )
    if isinstance(node, Pow):
        return _wrap_tex(node.base, _ATOM, names) + "^{" + to_latex(node.exponent, names) + "}"
    if isinstance(node, Div):
        return rf"\frac{{{to_latex(node.numerator, names)}}}{{{to_latex(node.denominator, names)}}}"
    if isinstance(node, Mul):
        pieces = []
        for index, factor in enumerate(node.factors):
            text = _wrap_tex(factor, _POWER, names)
            if index and isinstance(factor, Num):
                pieces.append(r"\cdot " + text)
            else:
                pieces.append(text)
        if isinstance(node.factors[0], Num) and node.factors[0].value == -1:
            return "-" + "".join(pieces[1:])
        return "".join(pieces)
    parts = []
    for index, term in enumerate(node.terms):
        sign, rest = _split_sign(term)
        body = to_latex(rest, names)
        if index == 0:
            parts.append(("-" if sign < 0 else "") + body)
        else:
            parts.append((" - " if sign < 0 else " + ") + body)
    return "".join(parts)


def _wrap_tex(node: Node, need: int, names: dict[str, str]) -> str:
    text = to_latex(node, names)
    return rf"\left({text}\right)" if _prec(node) < need else text
