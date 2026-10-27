from __future__ import annotations

import pytest

from micro_viz import Firm
from micro_viz.firm import Cost, ProductionFunction


def test_public_oop_imports_compose_a_firm() -> None:
    cost = Cost("TC = 10 + Q^2")
    production = ProductionFunction(6.0, 3.0, -0.5)
    firm = Firm(cost=cost, production=production)

    assert firm.total_cost(2.0) == pytest.approx(14.0)
    assert firm.average_cost(2.0) == pytest.approx(7.0)
    assert firm.marginal_cost(2.0) == pytest.approx(4.0)
    assert firm.revenue(2.0, 8.0) == pytest.approx(16.0)
    assert firm.profit(2.0, 8.0) == pytest.approx(2.0)
    assert firm.production is production


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
