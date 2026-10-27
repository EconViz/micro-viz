"""``Cost``: formulas, coefficients and tables, checked against the older cost models."""

from __future__ import annotations

import math
import warnings
from collections.abc import Callable
from pathlib import Path

import pytest
from mosaickit.errors import LayoutWarning

from micro_viz import (
    Cost,
    CostError,
    CubicCost,
    FormulaError,
    PiecewiseCost,
    analyze_costs,
    break_even_price,
    cost_curves,
    cost_curves_grid,
    cost_curves_panels,
    profit_maximizing_output,
    shutdown_price,
    solve_competitive_firm,
    total_cost_canvas,
    unit_cost_canvas,
)
from micro_viz.firm.competition import CompetitionError

OLD = (50.0, 36.0, -8.0, 0.6)
NEW = (200.0, 120.0, -18.0, 1.0)
FORM = "TC = 200 + 120Q - 18Q^2 + Q^3"


def cubic(c: tuple[float, ...]) -> CubicCost:
    return CubicCost(c[0], c[1], c[2], c[3])


def close(a: float, b: float, tol: float = 1e-9) -> bool:
    return math.isclose(a, b, rel_tol=tol, abs_tol=tol)


def golden(function, low: float, high: float) -> float:  # type: ignore[no-untyped-def]
    ratio = (math.sqrt(5) - 1) / 2
    a, b = low, high
    for _ in range(200):
        c, d = b - ratio * (b - a), a + ratio * (b - a)
        if function(c) < function(d):
            b = d
        else:
            a = c
    return (a + b) / 2


# ---- the four ways to write the same cost ------------------------------------------------


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    "build",
    [
        lambda: Cost(FORM),
        lambda: Cost("200 + 120Q - 18Q^2 + Q^3"),
        lambda: Cost("tc = 200 + 120q - 18q^2 + q^3"),
        lambda: Cost("TC = 200 + 120Q - 18Q**2 + Q**3"),
        lambda: Cost("VC = 120Q - 18Q^2 + Q^3", fixed=200),
        lambda: Cost("MC = 120 - 36Q + 3Q^2", fixed=200),
        lambda: Cost("ATC = 200/Q + 120 - 18Q + Q^2"),
        lambda: Cost("AC = 200/Q + 120 - 18Q + Q^2"),
        lambda: Cost("AVC = 120 - 18Q + Q^2", fixed=200),
        lambda: Cost.polynomial(200, 120, -18, 1),
        lambda: Cost(FORM, fixed=200),
    ],
)
def test_every_form_gives_the_same_cost(build) -> None:  # type: ignore[no-untyped-def]
    cost = build()
    old = cubic(NEW)
    assert cost.fc == 200
    for q in (0.0, 1.0, 4.5, 9.0, 10.0, 16.0):
        assert close(cost.tc(q), old.total_cost(q))
        assert close(cost.vc(q), old.variable_cost(q))
        assert close(cost.mc(q), old.marginal_cost(q))
    assert cost.atc(0) is None and cost.ac(0) is None and cost.afc(0) is None
    assert close(cost.atc(9) or 0, old.average_total_cost(9) or 0)
    assert close(cost.avc(9) or 0, old.average_variable_cost(9) or 0)
    assert close(cost.afc(8) or 0, 25)
    assert cost.min_avc().output == pytest.approx(9.0, abs=1e-9)
    assert cost.min_avc().value == pytest.approx(39.0, abs=1e-9)
    assert cost.min_atc().output == pytest.approx(10.0, abs=1e-9)
    assert cost.min_atc().value == pytest.approx(60.0, abs=1e-9)
    assert close(cost.shutdown_price(), 39.0)
    assert close(cost.breakeven_price() or 0, 60.0)


def test_the_textbook_numbers() -> None:
    cost = Cost(FORM)
    avc, atc = cost.min_avc(), cost.min_atc()
    assert avc is not None and atc is not None
    assert (avc.output, avc.value) == pytest.approx((9.0, 39.0))
    assert (atc.output, atc.value) == pytest.approx((10.0, 60.0))
    assert cost.warnings == ()


def test_missing_fixed_cost_is_assumed_zero_and_said() -> None:
    cost = Cost("MC = 10 + 4Q")
    assert cost.fc == 0
    assert len(cost.warnings) == 1 and "FC = 0" in cost.warnings[0]
    assert Cost("VC = 10Q + 2Q^2").warnings
    assert not Cost("MC = 10 + 4Q", fixed=5).warnings
    zh = Cost("MC = 10 + 4Q", language="zh-TW")
    assert "FC = 0" in zh.warnings[0] and "固定成本" in zh.warnings[0]


def test_formula_text_and_expressions_are_exact() -> None:
    cost = Cost("MC = 120 - 36Q + 3Q^2", fixed=200)
    assert cost.formula == FORM
    assert str(cost.expression("mc")) == "120 - 36Q + 3Q^2"
    assert str(cost.expression("vc")) == "120Q - 18Q^2 + Q^3"
    assert cost.to_dict()["fixed_cost"] == 200
    assert repr(cost) == f"Cost({FORM!r})"
    assert Cost(FORM) == Cost.polynomial(200, 120, -18, 1)
    assert Cost(FORM) != Cost.polynomial(200, 120, -18, 2)
    assert len({Cost(FORM), Cost.polynomial(200, 120, -18, 1)}) == 1


# ---- regression against CubicCost, old and new defaults ----------------------------------


@pytest.mark.parametrize("coefficients", [OLD, NEW])  # type: ignore[untyped-decorator]
def test_cost_reproduces_cubic_cost_analysis(coefficients: tuple[float, ...]) -> None:
    old = cubic(coefficients)
    new = Cost.polynomial(*coefficients)
    assert new.as_cubic() == old
    span = (1.0, 11.0 if coefficients is OLD else 16.0)
    a, b = analyze_costs(old, output_range=span), analyze_costs(new, output_range=span)
    assert len(a.points) == len(b.points)
    for x, y in zip(a.points, b.points, strict=True):
        assert x.to_dict() == pytest.approx(y.to_dict(), rel=1e-12)
    assert [v for pt in a.marginal_cost_path for v in pt] == pytest.approx(
        [v for pt in b.marginal_cost_path for v in pt], rel=1e-12
    )
    for name in (
        "minimum_average_variable_cost",
        "minimum_average_total_cost",
        "minimum_marginal_cost",
    ):
        left, right = getattr(a, name), getattr(b, name)
        assert (left is None) == (right is None)
        if left is not None:
            assert left.to_dict() == pytest.approx(right.to_dict(), rel=1e-12)


@pytest.mark.parametrize("coefficients", [OLD, NEW])  # type: ignore[untyped-decorator]
def test_competition_results_match(coefficients: tuple[float, ...]) -> None:
    old = cubic(coefficients)
    new = Cost.polynomial(*coefficients)
    assert close(shutdown_price(new), shutdown_price(old))
    assert close(break_even_price(new) or 0, break_even_price(old) or 0)
    top = break_even_price(old) or 50
    for price in (0.0, 5.0, top * 0.5, top, top * 1.5, top * 3):
        assert close(profit_maximizing_output(new, price), profit_maximizing_output(old, price))
        a, b = solve_competitive_firm(old, price), solve_competitive_firm(new, price)
        assert a.regime == b.regime
        assert close(a.profit, b.profit) and close(a.output, b.output)


def test_unit_tax_and_no_fixed_cost() -> None:
    cost = Cost(FORM)
    taxed = cost.with_unit_tax(5)
    assert close(taxed.mc(3), cost.mc(3) + 5)
    assert close(taxed.fc, 200)
    lowest = taxed.min_avc()
    assert lowest is not None
    assert close(
        lowest.value, cubic(NEW).with_unit_tax(5).variable_cost(lowest.output) / lowest.output
    )
    bare = cost.without_fixed_cost()
    assert bare.fc == 0 and close(bare.tc(4), cost.vc(4))
    assert close(Cost("MC = 10 + 4Q", fixed=7).with_unit_tax(2).mc(1), 16)
    assert Cost("MC = 10 + 4Q", fixed=7).without_fixed_cost().fc == 0


# ---- other shapes: closed forms and numeric minima to 1e-9 -------------------------------


def test_quadratic_atc_minimum_is_closed_form() -> None:
    cost = Cost("TC = 100 + 10Q + 2Q^2")
    assert cost.min_avc() is None  # AVC rises from the start
    assert cost.shutdown_price() == 10
    low = cost.min_atc()
    assert low is not None
    assert low.output == pytest.approx(math.sqrt(50), abs=1e-12)
    assert low.value == pytest.approx(10 + 4 * math.sqrt(50), abs=1e-12)
    assert close(cost.mc(low.output), low.value)  # MC = ATC at the minimum


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    "text",
    [
        "TC = 80 + 30Q - 6Q^2 + 0.5Q^3",
        "TC = 500 + 40Q - 5Q^2 + 0.25Q^3 + 0.001Q^4",
        "TC = 90 + 5exp(0.1Q) + 20Q",
        "TC = 120 + 10Q + Q^2 + 20ln(Q + 1)",
        "TC = 300 + 8Q + 0.02Q^3 + 6sqrt(Q + 1)",
    ],
)
def test_minima_match_a_direct_search_to_1e9(text: str) -> None:
    cost = Cost(text)
    for low, unit, curve in (
        (cost.min_atc(), cost.atc, "atc"),
        (cost.min_avc(), cost.avc, "avc"),
    ):
        if low is None:
            continue

        def at(q: float, u: Callable[[float], float | None] = unit) -> float:
            value = u(q)
            assert value is not None
            return value

        found = golden(at, max(low.output * 0.5, 1e-3), low.output * 1.5 + 1)
        assert at(low.output) <= at(found) + 1e-9, curve
        assert close(at(low.output), low.value, 1e-12)
        assert close(cost.mc(low.output), low.value, 1e-9)  # MC crosses the average at its minimum


def test_output_at_price_solves_price_equals_mc() -> None:
    for text in ("TC = 100 + 10Q + 2Q^2", "TC = 90 + 5exp(0.1Q) + 20Q", "MC = 6 + 0.5Q + 0.02Q^2"):
        cost = Cost(text, fixed=40) if text.startswith("MC") else Cost(text)
        for price in (cost.mc(0) + 1, cost.mc(0) + 30, cost.mc(0) + 200):
            q = cost.output_at_price(price)
            assert q > 0
            assert close(cost.mc(q), price, 1e-9)
    assert Cost("TC = 100 + 10Q + 2Q^2").output_at_price(3) == 0
    with pytest.raises(CostError):
        Cost("TC = 50 + 3Q").output_at_price(10)  # MC never reaches the price


def test_cost_given_by_mc_without_closed_form_integral_uses_quadrature() -> None:
    cost = Cost("MC = 10 + Q exp(Q/10)", fixed=5)
    assert cost.expression("vc") is None
    # int_0^q x e^{x/10} dx = 10 q e^{q/10} - 100 e^{q/10} + 100
    q = 6.0
    exact = 10 * q + 10 * q * math.exp(q / 10) - 100 * math.exp(q / 10) + 100
    assert cost.vc(q) == pytest.approx(exact, rel=1e-10)
    assert cost.tc(q) == pytest.approx(exact + 5, rel=1e-10)


def test_table_cost() -> None:
    cost = Cost.from_table(q=[0, 1, 2, 3, 4], tc=[10, 18, 24, 33, 50])
    assert cost.fc == 10 and cost.capacity == 4
    assert cost.tc(2) == 24 and cost.tc(2.5) == pytest.approx(28.5)
    assert cost.mc(0.5) == 8 and cost.mc(2.5) == 9 and cost.mc(3.5) == 17
    assert cost.avc(2) == 7
    low = cost.min_avc()
    assert low is not None and low.output == 2 and low.value == 7
    assert cost.output_at_price(10) == 3
    assert cost.output_at_price(1) == 0
    with pytest.raises(CostError):
        cost.tc(5)  # beyond the table
    analysis = analyze_costs(cost, output_range=(1.0, 4.0), samples=7)
    assert analysis.points[0].output == 1.0
    for q, tc in (
        ([1, 2], [1, 2]),
        ([0, 2, 1], [1, 2, 3]),
        ([0, 1], [1]),
        ([0], [1]),
        ([0, 1], [5, 3]),
        ([0, 1], [-1, 3]),
    ):
        with pytest.raises(CostError):
            Cost.from_table(q=q, tc=tc)


# ---- economics checks and friendly errors ------------------------------------------------


def test_negative_fixed_cost_is_refused() -> None:
    with pytest.raises(CostError, match="TC\\(0\\) = -5"):
        Cost("TC = -5 + 2Q")
    with pytest.raises(CostError):
        Cost("MC = 4", fixed=-1)


def test_marginal_cost_must_be_positive_on_the_plotted_range() -> None:
    cost = Cost("TC = 10 - 20Q + Q^2")
    with pytest.raises(CostError) as caught:
        analyze_costs(cost, output_range=(1.0, 16.0))
    message = str(caught.value)
    assert "between 1 and 10" in message
    with pytest.raises(CostError):
        cost_curves(cost, output=(1, 16))
    analyze_costs(cost, output_range=(11.0, 16.0))  # fine where MC > 0
    cost.validate((11.0, 16.0))


def test_other_inputs_are_refused_with_causes() -> None:
    cases = {
        "VC = 5 + 2Q": "VC(0) = 5",
        "TC = 5 + 2R": "R",
        "P = 5": "TC, VC",
        "TC = 5 + ln(Q)": "zero output",
    }
    for text, fragment in cases.items():
        with pytest.raises(CostError) as caught:
            Cost(text)
        assert fragment in str(caught.value)
    with pytest.raises(CostError, match="disagrees"):
        Cost(FORM, fixed=100)
    with pytest.raises(CostError):
        Cost.polynomial()
    with pytest.raises(CostError):
        Cost.polynomial(1, math.nan)
    with pytest.raises(CostError):
        Cost("TC = 3Q", output_symbol=" ")


def test_syntax_errors_are_friendly_and_in_both_languages() -> None:
    with pytest.raises(FormulaError) as en:
        Cost("TC = 200 + 120Q 18Q^2", language="en")
    assert isinstance(en.value, CostError) and isinstance(en.value, ValueError)
    assert "After 120Q an operator is missing" in str(en.value)
    assert "^" in str(en.value).splitlines()[-1]
    with pytest.raises(FormulaError) as zh:
        Cost("TC = 200 + 120Q 18Q^2", language="zh-TW")
    assert "少了運算符號" in str(zh.value)
    with pytest.raises(FormulaError) as cn:
        Cost("TC = 200 ＋ 120Q", language="zh-CN")
    assert "全角" in str(cn.value) or "全形" in str(cn.value)
    for text in ("__import__('os')", "Q.x", "Q" * 500, "TC = " + "(" * 100):
        with pytest.raises(FormulaError):
            Cost(text)


def test_language_follows_the_active_config_when_not_given() -> None:
    from micro_viz import Config

    Config.reset()
    try:
        Config.from_dict({"micro": {"language": "zh-TW"}}).use()
        with pytest.raises(FormulaError) as zh:
            Cost("TC = 1 +")
        assert "公式停在" in str(zh.value)
        with pytest.raises(FormulaError) as en:
            Cost("TC = 1 +", language="en")  # an explicit language wins
        assert "The formula ends" in str(en.value)
    finally:
        Config.reset()


# ---- figures -----------------------------------------------------------------------------


def test_one_step_figures_render_without_layout_warnings(tmp_path: Path) -> None:
    cost = Cost(FORM)
    with warnings.catch_warnings():
        warnings.simplefilter("error", LayoutWarning)
        for index, canvas in enumerate(
            (
                cost_curves(cost, output=(1, 16)),
                cost_curves(FORM, output=(1, 16), show=("mc", "AVC")),
                cost_curves(cost, output=(1, 16), show=("MC", "AC"), marks=False, title="t"),
                unit_cost_canvas(cost, output_range=(1, 16)),
                total_cost_canvas(cost, output_range=(1, 16)),
                cost_curves_panels(cost, output_range=(1, 16))[1],
                cost_curves_grid(cost, output_range=(1, 16)),
            )
        ):
            canvas.save(tmp_path / f"figure{index}.svg")
            assert (tmp_path / f"figure{index}.svg").stat().st_size > 0


def test_one_step_figure_equals_the_two_step_figure() -> None:
    cost = Cost(FORM)
    one = cost_curves(cost, output=(1, 16))
    two = unit_cost_canvas(analyze_costs(cubic(NEW), output_range=(1, 16), samples=201))
    assert [layer.id for layer in one.snapshot().layers] == [
        layer.id for layer in two.snapshot().layers
    ]


def test_figure_arguments_are_checked() -> None:
    with pytest.raises(TypeError, match="output"):
        unit_cost_canvas(Cost(FORM))
    with pytest.raises(ValueError, match="unknown curves"):
        cost_curves(Cost(FORM), output=(1, 16), show=("MC", "TC"))
    with pytest.raises(CompetitionError):
        profit_maximizing_output(Cost(FORM), -1)


def test_output_symbol_is_only_a_display_choice() -> None:
    cost = Cost("TC = 200 + 120q - 18q^2 + q^3", output_symbol="q")
    canvas = cost_curves(cost, output=(1, 16))
    assert cost.output_symbol == "q"
    assert canvas is not None
    default = Cost("TC = 200 + 120q - 18q^2 + q^3")
    assert default.output_symbol == "Q"


def test_piecewise_cost_still_works_as_before() -> None:
    from micro_viz import CostSegment

    stepped = PiecewiseCost((CostSegment(6, 11.4), CostSegment(9, 13.0)))
    analysis = analyze_costs(stepped, output_range=(0.0, 9.0))
    assert analysis.minimum_average_total_cost is None
