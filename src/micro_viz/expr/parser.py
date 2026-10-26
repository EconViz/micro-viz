"""Tokenizer and recursive-descent parser. No ``eval``: the text is only ever read here."""

from __future__ import annotations

import math
from dataclasses import dataclass

from micro_viz.expr.errors import ExprError
from micro_viz.expr.nodes import (
    Call,
    Node,
    Num,
    Var,
    add,
    divide,
    is_num,
    mul,
    neg,
    power,
    variables_of,
)
from micro_viz.expr.registry import Registry

_FULLWIDTH = {
    "＋": "+",
    "－": "-",
    "−": "-",
    "＊": "*",
    "×": "*",
    "／": "/",
    "÷": "/",
    "＾": "^",
    "（": "(",
    "）": ")",
    "＝": "=",
    "，": ".",
    "．": ".",
    "、": ".",
    "　": " ",
}
_NUM, _NAME, _OP, _POW, _LP, _RP, _EQ, _END = "num", "name", "op", "pow", "(", ")", "=", "end"


@dataclass(frozen=True, slots=True)
class Token:
    kind: str
    text: str
    start: int
    end: int


@dataclass(frozen=True, slots=True)
class Parsed:
    """A parsed equation or expression: the left-hand name (or ``None``) and the tree."""

    head: str | None
    node: Node
    source: str


class _Reader:
    def __init__(self, source: str, registry: Registry, language: str | None) -> None:
        self.source = source
        self.registry = registry
        self.language = language
        self.tokens: list[Token] = []
        self.index = 0
        self.depth = 0

    # ---- errors ----
    def error(self, message_id: str, position: int | None, **fields: object) -> ExprError:
        return ExprError(
            message_id,
            source=self.source,
            position=position,
            provider=self.registry.messages,
            language=self.language,
            **fields,
        )

    # ---- tokenizer ----
    def tokenize(self) -> None:
        text, pos, size = self.source, 0, len(self.source)
        limits = self.registry.limits
        while pos < size:
            ch = text[pos]
            if ch in " \t":
                pos += 1
            elif ch.isascii() and ch.isdigit() or ch == ".":
                pos = self._number(pos)
            elif ch.isascii() and ch.isalpha():
                end = pos
                while end < size and text[end].isascii() and text[end].isalpha():
                    end += 1
                self.tokens.append(Token(_NAME, text[pos:end], pos, end))
                pos = end
            elif ch == "*" and text[pos + 1 : pos + 2] == "*":
                self.tokens.append(Token(_POW, "**", pos, pos + 2))
                pos += 2
            elif ch in "+-*/":
                self.tokens.append(Token(_OP, ch, pos, pos + 1))
                pos += 1
            elif ch == "^":
                self.tokens.append(Token(_POW, "^", pos, pos + 1))
                pos += 1
            elif ch == "(":
                self.tokens.append(Token(_LP, ch, pos, pos + 1))
                pos += 1
            elif ch == ")":
                self.tokens.append(Token(_RP, ch, pos, pos + 1))
                pos += 1
            elif ch == "=":
                self.tokens.append(Token(_EQ, ch, pos, pos + 1))
                pos += 1
            elif ch == ",":
                raise self.error("expr.comma", pos)
            elif ch in _FULLWIDTH:
                raise self.error("expr.fullwidth", pos, char=ch, suggestion=_FULLWIDTH[ch])
            elif 0xFF10 <= ord(ch) <= 0xFF19 or 0xFF21 <= ord(ch) <= 0xFF5A:
                raise self.error("expr.fullwidth", pos, char=ch, suggestion=chr(ord(ch) - 0xFEE0))
            else:
                raise self.error("expr.unexpected_char", pos, char=ch)
            if len(self.tokens) > 4 * limits.max_length:  # defensive; length is bounded already
                raise self.error("expr.too_long", pos, limit=limits.max_length)
        self.tokens.append(Token(_END, "", size, size))

    def _number(self, pos: int) -> int:
        text, size = self.source, len(self.source)
        end, dots = pos, 0
        while end < size and (text[end].isascii() and text[end].isdigit() or text[end] == "."):
            dots += text[end] == "."
            end += 1
        shown = text[pos:end]
        if dots > 1 or shown == ".":
            raise self.error("expr.number_malformed", pos, text=shown)
        value = float(shown)
        if value > self.registry.limits.max_number:
            raise self.error(
                "expr.number_too_large", pos, text=shown, limit=self.registry.limits.max_number
            )
        self.tokens.append(Token(_NUM, shown, pos, end))
        return end

    # ---- parser helpers ----
    @property
    def current(self) -> Token:
        return self.tokens[self.index]

    @property
    def previous(self) -> Token | None:
        return self.tokens[self.index - 1] if self.index else None

    def advance(self) -> Token:
        token = self.tokens[self.index]
        self.index += 1
        return token

    def nest(self, position: int) -> None:
        self.depth += 1
        if self.depth > self.registry.limits.max_depth:
            raise self.error("expr.too_deep", position, limit=self.registry.limits.max_depth)

    def fold(self, node: Node, position: int) -> Node:
        if isinstance(node, Num) and not math.isfinite(node.value):
            raise self.error("expr.overflow", position)
        return node

    # ---- grammar ----
    def parse(self) -> Parsed:
        head: str | None = None
        if self.current.kind == _NAME and len(self.tokens) > 1 and self.tokens[1].kind == _EQ:
            name = self.current.text
            head = self.registry.head(name)
            if head is None:
                allowed = ", ".join(sorted(set(self.registry.heads.values())))
                raise self.error("expr.bad_head", self.current.start, name=name, allowed=allowed)
            self.advance()
            self.advance()
        node = self.expression()
        token = self.current
        if token.kind == _RP:
            raise self.error("expr.unmatched_rparen", token.start)
        if token.kind == _EQ:
            raise self.error("expr.equals_twice", token.start)
        if token.kind != _END:  # pragma: no cover - the term loop consumes everything else
            raise self.error("expr.unexpected_char", token.start, char=token.text)
        names = variables_of(node)
        if len(names) > self.registry.limits.max_variables:
            raise self.error("expr.too_many_variables", None, names=", ".join(sorted(names)))
        return Parsed(head, node, self.source)

    def expression(self) -> Node:
        first_start = self.current.start
        node = self.term()
        while self.current.kind == _OP and self.current.text in "+-":
            sign = self.advance().text
            right = self.term()
            node = self.fold(add(node, right if sign == "+" else neg(right)), first_start)
        return node

    def term(self) -> Node:
        start = self.current.start
        node = self.unary()
        while True:
            token = self.current
            if token.kind == _OP and token.text in "*/":
                self.advance()
                right = self.unary()
                if token.text == "*":
                    node = mul(node, right)
                else:
                    if is_num(right, 0.0):
                        raise self.error("expr.divide_by_zero", token.start)
                    node = divide(node, right)
                node = self.fold(node, token.start)
            elif token.kind in (_NAME, _LP):
                node = self.fold(mul(node, self.unary()), token.start)
            elif token.kind == _NUM:
                after = self.source[start : self.previous.end].strip() if self.previous else ""
                raise self.error("expr.missing_operator", token.start, after=after)
            else:
                return node

    def unary(self) -> Node:
        token = self.current
        self.nest(token.start)
        try:
            if token.kind == _OP and token.text in "+-":
                self.advance()
                operand = self.unary()
                return neg(operand) if token.text == "-" else operand
            return self.power()
        finally:
            self.depth -= 1

    def power(self) -> Node:
        base = self.primary()
        token = self.current
        if token.kind != _POW:
            return base
        self.advance()
        exponent_at = self.current.start
        exponent = self.unary()
        if not isinstance(exponent, Num):
            raise self.error("expr.exponent_not_number", exponent_at)
        limit = self.registry.limits.max_exponent
        if abs(exponent.value) > limit:
            raise self.error(
                "expr.exponent_too_large", exponent_at, value=exponent.value, limit=limit
            )
        if isinstance(base, Num) and base.value == 0 and exponent.value < 0:
            raise self.error("expr.divide_by_zero", token.start)
        return self.fold(power(base, exponent), token.start)

    def primary(self) -> Node:
        token = self.current
        if token.kind == _NUM:
            self.advance()
            return Num(float(token.text))
        if token.kind == _NAME:
            return self.name(token)
        if token.kind == _LP:
            self.advance()
            self.nest(token.start)
            inner = self.expression()
            self.depth -= 1
            self.close(token)
            return inner
        raise self.operand_expected()

    def close(self, opened: Token) -> None:
        token = self.current
        if token.kind != _RP:
            raise self.error("expr.expected_rparen", token.start, opened=opened.start)
        self.advance()

    def operand_expected(self) -> ExprError:
        token = self.current
        previous = self.previous
        if token.kind == _END:
            return self.error(
                "expr.ends_early", token.start, previous=previous.text if previous else ""
            )
        if previous is None:
            return self.error("expr.cannot_start", token.start, found=token.text)
        return self.error(
            "expr.expected_operand", token.start, found=token.text, previous=previous.text
        )

    def name(self, token: Token) -> Node:
        registry = self.registry
        text = token.text
        canonical = registry.variable(text)
        if canonical is not None:
            self.advance()
            return Var(canonical)
        if text in registry.constants:
            self.advance()
            return Num(float(registry.constants[text]))
        function = registry.function(text)
        if function is not None:
            self.advance()
            opened = self.current
            if opened.kind != _LP:
                raise self.error("expr.function_needs_parens", token.start, name=text)
            self.advance()
            self.nest(opened.start)
            argument = self.expression()
            self.depth -= 1
            self.close(opened)
            self.fold(argument, token.start)
            if isinstance(argument, Num):
                try:
                    value = function.evaluate(argument.value)
                except (ValueError, OverflowError, ZeroDivisionError):
                    raise self.error(
                        "expr.domain", token.start, function=function.name, value=argument.value
                    ) from None
                return self.fold(Num(float(value)), token.start)
            return Call(function.name, argument)
        names = ", ".join(sorted(set(registry.variables.values())))
        if all(ch in registry.variables for ch in text) and len(text) > 1:
            raise self.error(
                "expr.unknown_name_product", token.start, name=text, suggestion="*".join(text)
            )
        raise self.error("expr.unknown_name", token.start, name=text, allowed=names)


def parse_text(source: str, registry: Registry, language: str | None = None) -> Parsed:
    """Read an expression or an equation ``HEAD = expression`` into a tree."""
    reader = _Reader(source if isinstance(source, str) else str(source), registry, language)
    limits = registry.limits
    if len(reader.source) > limits.max_length:
        raise reader.error("expr.too_long", limits.max_length, limit=limits.max_length)
    if not reader.source.strip():
        raise reader.error("expr.empty", 0)
    reader.tokenize()
    return reader.parse()
