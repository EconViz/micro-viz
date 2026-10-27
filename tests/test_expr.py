"""The expression engine, tested with its own registry (it must not depend on micro-viz)."""

from __future__ import annotations

import ast
import math
import sys
import time
from pathlib import Path

import pytest

from micro_viz.core.expr import ExprError, Expression, Limits, Registry, functions, parse

ROOT = Path(__file__).parents[1] / "src" / "micro_viz" / "expr"
STDLIB = set(sys.stdlib_module_names)


def registry(**changes: object) -> Registry:
    base = Registry(
        variables={"Q": "Q", "q": "Q", "P": "P"},
        functions={"exp": functions.EXP, "ln": functions.LN, "sqrt": functions.SQRT},
        heads={"TC": "TC", "MC": "MC", "P": "P", "Q": "Q"},
        constants={"pi": math.pi},
        symbols={"Q": "Q"},
    )
    return base.evolve(**changes) if changes else base


R = registry()


def value(text: str, **at: float) -> float:
    expression = parse(text, R)
    return expression(**at) if at else expression()


def test_numbers_and_precedence() -> None:
    assert value("1 + 2 * 3") == 7
    assert value("(1 + 2) * 3") == 9
    assert value("2 ^ 3 ^ 2") == 512  # right associative
    assert value("-2 ^ 2") == -4  # unary minus binds looser than ^
    assert value("2 ^ -1") == 0.5
    assert value("2 ** 3") == 8
    assert value("10 / 4") == 2.5
    assert value("10 - 4 - 3") == 3
    assert value("1.5 + .5") == 2
    assert value("  3\t+   4  ") == 7
    assert value("- - 3") == 3
    assert value("+3") == 3
    assert value("pi") == pytest.approx(math.pi)


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    ("text", "at", "expected"),
    [
        ("36Q", 2, 72),
        ("2(Q+1)", 3, 8),
        ("Q(Q+1)", 3, 12),
        ("(Q+1)(Q-1)", 3, 8),
        ("(Q+1)Q", 3, 12),
        ("2Q^2", 3, 18),
        ("Q^2Q", 3, 27),
        ("1/2Q", 4, 2),
        ("-2Q", 4, -8),
        ("2exp(0)", 0, 2),
        ("3sqrt(Q)", 4, 6),
        ("Q sqrt(Q)", 4, 8),
        ("2pi", 0, 2 * math.pi),
        ("200 + 120Q - 18Q^2 + Q^3", 9, 200 + 1080 - 1458 + 729),
        ("exp(0.1q) - 1", 0, 0),
        ("ln(Q)", math.e, 1),
    ],
)
def test_implicit_multiplication_and_functions(text: str, at: float, expected: float) -> None:
    expression = parse(text, R)
    result = expression(at) if expression.variables else expression()
    assert result == pytest.approx(expected)


def test_variable_spellings_are_one_variable() -> None:
    assert parse("q + Q", R).variables == {"Q"}
    assert parse("2q", R)(3) == 6


def test_head_names_the_function() -> None:
    assert parse("TC = 3Q", R).head == "TC"
    assert parse("tc = 3Q", R).head == "TC"
    assert parse("3Q", R).head is None
    assert parse("q = 50 - P/2", R).head == "Q"


INVALID = [
    ("", "expr.empty"),
    ("   ", "expr.empty"),
    ("36Q 5", "expr.missing_operator"),
    ("Q2", "expr.missing_operator"),
    ("2 3", "expr.missing_operator"),
    ("(Q+1)2", "expr.missing_operator"),
    ("1 +", "expr.ends_early"),
    ("TC =", "expr.ends_early"),
    ("*Q", "expr.cannot_start"),
    ("Q * * 2", "expr.expected_operand"),
    ("()", "expr.expected_operand"),
    ("(Q", "expr.expected_rparen"),
    ("Q)", "expr.unmatched_rparen"),
    ("TC = Q = 1", "expr.equals_twice"),
    ("100 = Q", "expr.equals_twice"),
    ("XX = Q", "expr.bad_head"),
    ("Z + 1", "expr.unknown_name"),
    ("QP", "expr.unknown_name_product"),
    ("sqrt Q", "expr.function_needs_parens"),
    ("Q^Q", "expr.exponent_not_number"),
    ("Q^21", "expr.exponent_too_large"),
    ("Q^-21", "expr.exponent_too_large"),
    ("1/0", "expr.divide_by_zero"),
    ("0^-1", "expr.divide_by_zero"),
    ("ln(0)", "expr.domain"),
    ("sqrt(-1)", "expr.domain"),
    ("1.2.3", "expr.number_malformed"),
    (".", "expr.number_malformed"),
    ("1,5", "expr.comma"),
    ("Q + 1;", "expr.unexpected_char"),
    ("Q & 1", "expr.unexpected_char"),
    ("Q + Z1", "expr.unknown_name"),
    ("P + Q", "expr.too_many_variables"),
    ("１+２", "expr.fullwidth"),
    ("Q ＋ 1", "expr.fullwidth"),
    ("Q ， 1", "expr.fullwidth"),
    ("（Q）", "expr.fullwidth"),
    ("Q × 2", "expr.fullwidth"),
    ("Q − 1", "expr.fullwidth"),
    ("1e3", "expr.unknown_name"),
]


@pytest.mark.parametrize(("text", "message_id"), INVALID)  # type: ignore[untyped-decorator]
def test_invalid_formulas_raise_our_error(text: str, message_id: str) -> None:
    with pytest.raises(ExprError) as caught:
        parse(text, R)
    assert caught.value.message_id == message_id
    assert isinstance(caught.value, ValueError)


def test_error_points_at_the_offending_character() -> None:
    with pytest.raises(ExprError) as caught:
        parse("TC = 200 + 120Q 18Q^2", R)
    error = caught.value
    assert error.position == "TC = 200 + 120Q 18Q^2".index("18")
    assert error.fields["after"] == "120Q"
    rendered = error.render()
    lines = rendered.splitlines()
    assert lines[1].strip() == "TC = 200 + 120Q 18Q^2"
    assert lines[2].index("^") == lines[1].index("18")


def test_messages_come_from_the_provider_not_the_engine() -> None:
    calls: list[tuple[str, str | None, dict[str, object]]] = []

    def provider(message_id: str, language: str | None, fields: object) -> str:
        calls.append((message_id, language, dict(fields)))  # type: ignore[call-overload]
        return f"<{message_id}@{language}>"

    custom = registry(messages=provider)
    with pytest.raises(ExprError) as caught:
        parse("36Q 5", custom, language="zh-TW")
    assert "<expr.missing_operator@zh-TW>" in str(caught.value)
    assert calls[-1][2] == {"after": "36Q"}
    # without a provider the engine still names the problem by id
    with pytest.raises(ExprError) as bare:
        parse("(", registry(messages=Registry(variables={}).messages))
    assert "expr." in str(bare.value)


# ---- security ----------------------------------------------------------------------------

HOSTILE = [
    "__import__('os').system('true')",
    "Q.__class__",
    "Q.__class__.__mro__",
    "().__class__",
    "exec('1')",
    "eval('1')",
    "open('/etc/passwd')",
    "lambda: 1",
    "[x for x in range(9)]",
    "import os",
    "os.system",
    "Q; 1",
    "Q\n+ 1",
    "9" * 400,
    "Q^" + "9" * 50,
    "1" + "0" * 50,
    "Q^99999999",
    "9^9^9^9",
    "(" * 500 + "Q" + ")" * 500,
    "-" * 500 + "Q",
    "Q" + "+Q" * 500,
    "exp(" * 100 + "Q" + ")" * 100,
    "{}",
    "Q if 1 else 2",
    "Q @ 2",
    "Q // 2",
    "Q % 2",
    "Q ** ** 2",
    "'abc'",
    "`id`",
    "$(id)",
    "Q" * 10_000,
    "‮ Q",
    "Q\x00",
]


@pytest.mark.parametrize("text", HOSTILE)  # type: ignore[untyped-decorator]
def test_hostile_input_is_rejected_quickly_with_our_error(text: str) -> None:
    started = time.perf_counter()
    try:
        parse(text, R)
    except ExprError:
        pass
    assert time.perf_counter() - started < 1.0


def test_limits_are_data() -> None:
    tight = registry(limits=Limits(max_length=10, max_depth=2, max_exponent=3, max_number=100))
    for text, message_id in (
        ("1 + 1 + 1 + 1 + 1", "expr.too_long"),
        ("((Q))", "expr.too_deep"),
        ("Q^4", "expr.exponent_too_large"),
        ("101", "expr.number_too_large"),
    ):
        with pytest.raises(ExprError) as caught:
            parse(text, tight)
        assert caught.value.message_id == message_id


def test_big_but_legal_values_do_not_hang_or_crash() -> None:
    expression = parse("(Q + 1000000000000)^20", R)
    assert math.isfinite(expression(1.0))
    huge = parse("Q^20", R)
    with pytest.raises(ExprError):
        huge(1e300)  # overflows to inf, reported as our error


def test_evaluation_errors_are_ours() -> None:
    with pytest.raises(ExprError):
        parse("1/Q", R)(0)
    with pytest.raises(ExprError):
        parse("ln(Q)", R)(-1)
    with pytest.raises(ExprError):
        parse("sqrt(Q)", R)(-1)
    with pytest.raises(ExprError):
        parse("Q^0.5", R)(-1)


def test_the_engine_never_uses_dynamic_execution() -> None:
    forbidden = {"eval", "exec", "compile", "__import__", "getattr", "setattr", "globals"}
    for path in ROOT.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden, f"{path.name} calls {node.func.id}"
            if isinstance(node, ast.Import | ast.ImportFrom):
                names = (
                    [a.name for a in node.names]
                    if isinstance(node, ast.Import)
                    else [node.module or ""]
                )
                assert not any(n.split(".")[0] in {"sympy", "numpy", "scipy"} for n in names)


# ---- calculus ----------------------------------------------------------------------------

DIFFERENTIABLE = [
    "200 + 120Q - 18Q^2 + Q^3",
    "Q^2",
    "3Q^-1",
    "sqrt(Q)",
    "Q^0.5 + Q^1.5",
    "exp(0.1Q)",
    "2exp(-0.3Q) + Q",
    "ln(Q + 1)",
    "Q exp(Q/5)",
    "Q^2 ln(Q)",
    "(Q + 1)/(Q + 2)",
    "1/(1 + Q^2)",
    "sqrt(Q + 4)Q",
    "(2Q + 1)^3",
    "exp(Q)/Q",
]


@pytest.mark.parametrize("text", DIFFERENTIABLE)  # type: ignore[untyped-decorator]
def test_derivative_matches_finite_differences(text: str) -> None:
    f = parse(text, R)
    df = f.derivative()
    h = 1e-6
    for x in (0.7, 1.3, 2.9, 5.1):
        numeric = (f(x + h) - f(x - h)) / (2 * h)
        assert df(x) == pytest.approx(numeric, rel=1e-6, abs=1e-7)


INTEGRABLE = [
    "120 - 36Q + 3Q^2",
    "100 - Q",
    "2Q + 7",
    "Q^2.5",
    "exp(0.1Q)",
    "3exp(-0.5Q) + Q",
    "sqrt(Q + 1)",
    "ln(Q + 1)",
    "(2Q + 1)^3",
    "5",
]


@pytest.mark.parametrize("text", INTEGRABLE)  # type: ignore[untyped-decorator]
def test_integral_differentiates_back_and_is_zero_at_zero(text: str) -> None:
    f = parse(text, R)
    big_f = f.integral()
    assert big_f(0.0) == pytest.approx(0.0, abs=1e-12)
    for x in (0.5, 1.7, 4.0):
        assert big_f.derivative()(x) == pytest.approx(f(x), rel=1e-9)
    assert big_f(3.0) - big_f(1.0) == pytest.approx(f.integral_between(1.0, 3.0), rel=1e-9)


def test_integral_that_diverges_at_the_lower_limit_is_reported() -> None:
    with pytest.raises(ExprError):
        parse("Q^-2", R).integral()


def test_integral_without_closed_form_falls_back_to_quadrature() -> None:
    f = parse("Q exp(Q)", R)
    with pytest.raises(ExprError):
        f.integral()
    # integral of x e^x on [0, 2] is (x - 1) e^x
    assert f.integral_between(0.0, 2.0) == pytest.approx(math.e**2 + 1, rel=1e-10)
    g = parse("1/Q", R)
    with pytest.raises(ExprError):
        g.integral()
    assert g.integral_between(1.0, math.e) == pytest.approx(1.0, rel=1e-10)


def test_polynomial_structure_and_printing() -> None:
    f = parse("200 + 120Q - 18Q^2 + Q^3", R)
    assert f.coefficients() == {0.0: 200, 1.0: 120, 2.0: -18, 3.0: 1}
    assert f.degree == 3
    assert f.is_polynomial
    assert str(f) == "200 + 120Q - 18Q^2 + Q^3"
    assert str(f.derivative()) == "120 - 36Q + 3Q^2"
    assert parse("exp(Q)", R).coefficients() is None
    assert f.to_latex() == "200 + 120Q - 18Q^{2} + Q^{3}"
    assert parse("1/(Q+1)", R).to_latex() == r"\frac{1}{Q + 1}"


@pytest.mark.parametrize("text", [*DIFFERENTIABLE, *INTEGRABLE, "3Q - 2", "-Q^2 + 1"])  # type: ignore[untyped-decorator]
def test_printed_form_parses_back_to_the_same_function(text: str) -> None:
    f = parse(text, R)
    g = parse(str(f), R)
    for x in (0.4, 1.9, 3.3):
        assert g(x) == pytest.approx(f(x), rel=1e-9)


def test_arithmetic_on_expressions() -> None:
    q = Expression.variable("Q", R)
    f = parse("100 - Q", R)
    assert (f * q)(3) == 291
    assert (f + 5)(3) == 102
    assert (5 - f)(3) == -92
    assert (-f)(3) == -97
    assert (f / 2)(4) == 48
    assert f.substitute("Q", 10)() == 90
    assert Expression.from_polynomial({0: 1, 2: 3}, "Q", R)(2) == 13


# ---- the engine is detachable and extensible ---------------------------------------------


def test_another_package_can_register_other_variables_and_functions() -> None:
    custom = Registry(
        variables={"Y": "Y", "C": "C"},
        functions={"exp": functions.EXP},
        heads={"C": "C"},
        limits=Limits(max_variables=2),
    )
    expression = parse("C = 20 + 0.8Y", custom)
    assert expression.head == "C"
    assert expression.variables == {"Y"}
    assert expression(100) == 100
    two = parse("Y + 2C", custom)
    assert two(Y=1, C=2) == 5
    assert two.derivative("C")() == 2
    with pytest.raises(ExprError):
        parse("Q", custom)  # Q is not registered here


def test_engine_imports_only_the_standard_library_and_itself() -> None:
    for path in ROOT.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            elif isinstance(node, ast.ImportFrom) and node.level:
                raise AssertionError(f"{path.name} uses a relative import")
            for name in names:
                top = name.split(".")[0]
                if top == "micro_viz":
                    assert name == "micro_viz.core.expr" or name.startswith(
                        "micro_viz.core.expr."
                    ), f"{path.name} imports {name}"
                else:
                    assert top in STDLIB or top == "__future__", f"{path.name} imports {name}"
