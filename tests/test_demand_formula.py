"""``Demand`` and formula input for ``Monopolist``."""

from __future__ import annotations

import math
import warnings

import pytest
from mosaickit.errors import LayoutWarning

from micro_viz import (
    Cost,
    CubicCost,
    Demand,
    DemandError,
    FormulaError,
    LinearDemand,
    Monopolist,
    analyze_costs,
    marginal_revenue,
    monopoly_canvas,
)
from micro_viz.demand import as_demand

LINEAR = "P = 100 - Q"
CURVED = "P = 100 - Q^2"
COST = "TC = 200 + 20Q"


def test_inverse_and_direct_forms_describe_the_same_line() -> None:
    inverse, direct = Demand("P = 100 - 2Q"), Demand("Q = 50 - P/2")
    assert inverse.linear == LinearDemand(100.0, 2.0)
    assert direct.linear == LinearDemand(100.0, 2.0)
    assert direct.price(10) == pytest.approx(inverse.price(10))


def test_a_straight_demand_becomes_a_linear_demand() -> None:
    assert as_demand(LINEAR) == LinearDemand(100.0, 1.0)
    assert isinstance(as_demand(CURVED), Demand)


def test_nonlinear_marginal_revenue_and_elasticity_are_exact() -> None:
    demand = Demand(CURVED)
    assert demand.marginal_revenue(4) == pytest.approx(100 - 3 * 16)
    assert demand.elasticity(4) == pytest.approx(84 / (4 * -8))
    assert demand.elasticity(0) == -math.inf


def test_direct_form_of_a_curve_is_inverted() -> None:
    demand = Demand("Q = 10 - P^2")
    assert demand.price(demand.quantity(3.0)) == pytest.approx(3.0)
    assert demand.intercept == pytest.approx(math.sqrt(10))


@pytest.mark.parametrize(
    "formula",
    ["100 - Q", "X = 100 - Q", "P = 100 - Z", "P = 100 + Q", "P = -5 - Q", "P = 100 - Q + Q^2"],
)
def test_bad_demand_formulas_are_rejected(formula: str) -> None:
    with pytest.raises((DemandError, FormulaError)):
        Demand(formula)


def test_monopolist_from_formulas_matches_objects() -> None:
    by_formula = Monopolist(LINEAR, COST).solve()
    by_object = Monopolist(LinearDemand(100.0, 1.0), Cost(COST)).solve()
    assert by_formula.quantity == pytest.approx(by_object.quantity)
    assert by_formula.price == pytest.approx(by_object.price)
    assert by_formula.quantity == pytest.approx(40.0)


def test_monopolist_accepts_a_cost_function_object() -> None:
    cost = CubicCost(50.0, 36.0, -8.0, 0.6)
    assert Monopolist(LINEAR, cost).cost is cost


def test_nonlinear_demand_satisfies_mr_equals_mc() -> None:
    outcome = Monopolist(CURVED, COST).solve()
    assert marginal_revenue(outcome.demand, outcome.quantity) == pytest.approx(20.0, abs=1e-3)
    assert outcome.price == pytest.approx(100 - outcome.quantity**2)


def test_nonlinear_monopoly_figure_renders_without_layout_warnings() -> None:
    outcome = Monopolist(CURVED, COST).solve()
    with warnings.catch_warnings():
        warnings.simplefilter("error", LayoutWarning)
        analysis = analyze_costs(outcome.cost, output_range=(1.0, 9.0), samples=81)
        assert monopoly_canvas(outcome, analysis, profit=True).snapshot().layers
