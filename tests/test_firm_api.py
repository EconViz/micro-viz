from __future__ import annotations

import pytest

from micro_viz import Firm
from micro_viz.firm import Cost, ProductionFunction
from micro_viz.firm.production import ProductionError, analyze_production


def test_public_oop_imports_compose_a_firm() -> None:
    cost = Cost("TC = 10 + Q^2")
    production = ProductionFunction("Q = 6L + 3L^2 - 0.5L^3")
    firm = Firm(cost=cost, production=production)

    assert firm.total_cost(2.0) == pytest.approx(14.0)
    assert firm.average_cost(2.0) == pytest.approx(7.0)
    assert firm.marginal_cost(2.0) == pytest.approx(4.0)
    assert firm.revenue(2.0, 8.0) == pytest.approx(16.0)
    assert firm.profit(2.0, 8.0) == pytest.approx(2.0)
    assert firm.production is production


def test_formula_production_exposes_total_average_and_marginal_products() -> None:
    production = ProductionFunction("Q = 6L + 3L^2 - 0.5L^3")

    assert production.total_product(2.0) == pytest.approx(20.0)
    assert production.average_product(2.0) == pytest.approx(10.0)
    assert production.marginal_product(2.0) == pytest.approx(12.0)
    assert production.formula == "Q = 6L + 3L^2 - 0.5L^3"


def test_callable_production_uses_a_numerical_marginal_product() -> None:
    production = ProductionFunction.from_callable(lambda labor: 4 * labor**0.5)

    assert production.total_product(4.0) == pytest.approx(8.0)
    assert production.average_product(4.0) == pytest.approx(2.0)
    assert production.marginal_product(4.0) == pytest.approx(1.0, rel=1e-5)


def test_table_production_interpolates_tp_and_uses_interval_mp() -> None:
    production = ProductionFunction.from_table(
        labor=[0, 1, 2, 3],
        output=[0, 8, 14, 17],
    )

    assert production.total_product(1.5) == pytest.approx(11.0)
    assert production.average_product(2.0) == pytest.approx(7.0)
    assert production.marginal_product(1.5) == pytest.approx(6.0)
    assert production.capacity == pytest.approx(3.0)
    with pytest.raises(ProductionError, match="capacity"):
        production.total_product(4.0)


def test_generic_production_function_can_be_analyzed() -> None:
    production = ProductionFunction("Q = 6L + 3L^2 - 0.5L^3")

    analysis = analyze_production(production, input_range=(0.0, 6.0), samples=61)

    assert analysis.points[20].total_product == pytest.approx(20.0)
    assert analysis.inflection_input == pytest.approx(2.0)
    assert analysis.average_product_max_input == pytest.approx(3.0)
    assert analysis.total_product_max_input == pytest.approx(4.8)


def test_firm_can_be_associated_with_a_market_without_mutation() -> None:
    firm = Firm(Cost("TC = 10 + Q^2"))
    market = object()

    associated = firm.in_market(market)

    assert firm.market is None
    assert associated.market is market
    assert associated.cost is firm.cost


@pytest.mark.parametrize(("name", "value"), [("output", -1.0), ("price", float("inf"))])
def test_revenue_rejects_invalid_inputs(name: str, value: float) -> None:
    firm = Firm(Cost("TC = 10 + Q^2"))
    output, price = (value, 1.0) if name == "output" else (1.0, value)

    with pytest.raises(ValueError, match=name):
        firm.revenue(output, price)
