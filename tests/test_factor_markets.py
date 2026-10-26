from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from micro_viz import (
    CapitalAdjustment,
    DerivedDemand,
    FactorError,
    FactorMarket,
    IndustryFactorDemand,
    InputAdjustment,
    LandMarket,
    LinearSupply,
    LinearValue,
    capital_adjustment_canvas,
    derived_demand_canvas,
    economic_rent_canvas,
    factor_equilibrium_canvas,
    firm_hiring_canvas,
    industry_factor_demand_canvas,
    land_rent_canvas,
    market_supply_canvas,
    short_long_run_canvas,
)

ROOT = Path(__file__).parents[1]
PRODUCT = LinearValue(10.0, 0.5)
SUPPLY = LinearSupply(4.0, 0.6)
COMPETITIVE = DerivedDemand(PRODUCT, 3.0)
MONOPOLY = DerivedDemand(PRODUCT, 3.0, 0.6)


def test_monopoly_mrp_lies_below_vmp() -> None:
    vmp, mrp = MONOPOLY.value_of_marginal_product, MONOPOLY.demand
    for quantity in (0.0, 5.0, 10.0):
        assert mrp.value(quantity) == pytest.approx(0.6 * vmp.value(quantity))
    assert COMPETITIVE.demand == vmp


def test_firm_hires_where_mrp_equals_wage() -> None:
    market = FactorMarket(COMPETITIVE.demand, SUPPLY)
    quantity = market.firm_hiring(12.0)
    assert COMPETITIVE.demand.value(quantity) == pytest.approx(12.0)
    assert market.firm_hiring(8.0) > quantity


def test_equilibrium_and_rent() -> None:
    market = FactorMarket(COMPETITIVE.demand, SUPPLY)
    quantity, wage = market.equilibrium()
    assert COMPETITIVE.demand.value(quantity) == pytest.approx(SUPPLY.wage(quantity))
    assert market.rent() == pytest.approx(0.5 * quantity * (wage - SUPPLY.intercept))
    monopoly_q, monopoly_w = FactorMarket(MONOPOLY.demand, SUPPLY).equilibrium()
    assert monopoly_q < quantity
    assert monopoly_w < wage


def test_industry_demand_is_steeper_than_sum_of_firms() -> None:
    industry = IndustryFactorDemand(COMPETITIVE.demand, 5, 1.0)
    anchor = 12.0
    assert industry.industry_quantity(anchor, anchor) == pytest.approx(
        industry.summed_quantity(anchor)
    )
    lower = 8.0
    gain_sum = industry.summed_quantity(lower) - industry.summed_quantity(anchor)
    gain_industry = industry.industry_quantity(lower, anchor) - industry.summed_quantity(anchor)
    assert 0 < gain_industry < gain_sum


def test_long_run_is_flatter_than_short_run() -> None:
    adjustment = InputAdjustment(10.0, 12.0, 2.0, 0.5)
    assert adjustment.short_wage(10.0) == adjustment.long_wage(10.0) == 12.0
    assert adjustment.long_wage(14.0) > adjustment.short_wage(14.0)
    with pytest.raises(FactorError):
        InputAdjustment(10.0, 12.0, 0.5, 2.0)


def test_capital_adjustment_traces_demand_locus() -> None:
    adjustment = CapitalAdjustment(COMPETITIVE.demand, (1.0, 1.5, 2.0))
    hires = [adjustment.hiring(i, 12.0) for i in range(3)]
    assert hires == sorted(hires)
    with pytest.raises(FactorError):
        CapitalAdjustment(COMPETITIVE.demand, (2.0, 1.0))


def test_land_rent_is_demand_height() -> None:
    land = LandMarket(LinearValue(30.0, 1.0), 12.0)
    assert land.rent == pytest.approx(18.0)
    with pytest.raises(FactorError):
        LandMarket(LinearValue(30.0, 1.0), 40.0).rent  # noqa: B018


def test_invalid_inputs() -> None:
    with pytest.raises(FactorError):
        DerivedDemand(PRODUCT, 3.0, 1.5)
    with pytest.raises(FactorError):
        FactorMarket(LinearValue(3.0, 1.0), LinearSupply(4.0, 1.0)).equilibrium()


def test_canvases_follow_parameters() -> None:
    market = FactorMarket(COMPETITIVE.demand, SUPPLY)
    assert derived_demand_canvas(MONOPOLY, title="T").spec.title == "T"
    assert firm_hiring_canvas(market, 12.0, 8.0) is not None
    assert capital_adjustment_canvas(
        CapitalAdjustment(COMPETITIVE.demand, (1.0, 1.5)), (14.0, 12.0)
    )
    assert industry_factor_demand_canvas(IndustryFactorDemand(COMPETITIVE.demand, 5, 1.0), 12.0)
    assert short_long_run_canvas(InputAdjustment(10.0, 12.0, 2.0, 0.5), 20.0) is not None
    assert market_supply_canvas(market) is not None
    assert factor_equilibrium_canvas(market, FactorMarket(MONOPOLY.demand, SUPPLY)) is not None
    assert economic_rent_canvas(market) is not None
    assert land_rent_canvas(LandMarket(LinearValue(30.0, 1.0), 12.0)) is not None


def test_example_runs(tmp_path: Path) -> None:
    config = tmp_path / "econ-viz.toml"
    config.write_text('base = "manual"\n', encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "scripts" / "factor_markets" / "factor_markets.py"),
            "--output-dir",
            str(tmp_path / "out"),
            "--config",
            str(config),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    assert (tmp_path / "out" / "land_rent.svg").exists()
