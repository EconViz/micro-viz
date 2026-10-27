from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from mosaickit import Canvas, CanvasGrid

from micro_viz import (
    CompetitionError,
    CubicCost,
    IndustrySupply,
    LinearDemand,
    Regime,
    analyze_costs,
    analyze_revenue_cost,
    break_even_price,
    competitive_demand_increase_grid,
    competitive_firm_canvas,
    competitive_firm_supply_grid,
    competitive_industry_supply_grid,
    competitive_market_supply_equilibrium_grid,
    competitive_revenue_grid,
    competitive_revenue_shift_grid,
    competitive_short_run_grid,
    cost_shift_canvas,
    firm_supply_canvas,
    industry_supply_canvas,
    market_and_firm_canvas,
    monopoly_revenue_grid,
    producer_surplus_canvas,
    revenue_cost_profit_canvas,
    shutdown_price,
    solve_competitive_firm,
)

COST = CubicCost(fixed_cost=30.0, linear=36.0, quadratic=-8.0, cubic=0.6)
ROOT = Path(__file__).parents[1]


def _ids(canvas: Canvas) -> set[str]:
    return {layer.id for layer in canvas.snapshot().layers}


def test_regimes_follow_the_price() -> None:
    assert solve_competitive_firm(COST, 18.0).regime is Regime.PROFIT
    assert solve_competitive_firm(COST, 11.0).regime is Regime.LOSS
    assert solve_competitive_firm(COST, 8.0).regime is Regime.SHUTDOWN
    assert solve_competitive_firm(COST, 8.0).output == 0.0
    assert shutdown_price(COST) < (break_even_price(COST) or 0.0)


def test_profit_is_revenue_minus_cost_and_price_equals_mc() -> None:
    outcome = solve_competitive_firm(COST, 18.0)
    assert outcome.profit == pytest.approx(outcome.total_revenue - outcome.total_cost)
    assert COST.marginal_cost(outcome.output) == pytest.approx(18.0)
    assert outcome.producer_surplus == pytest.approx(outcome.total_revenue - outcome.variable_cost)


def test_unit_tax_raises_marginal_cost_by_the_tax() -> None:
    taxed = COST.with_unit_tax(4.0)
    assert taxed.marginal_cost(5.0) == pytest.approx(COST.marginal_cost(5.0) + 4.0)


def test_industry_supply_sums_firms_and_rejects_empty() -> None:
    firms = (COST, CubicCost(30.0, 40.0, -8.0, 0.6))
    industry = IndustrySupply(firms)
    price = 20.0
    assert industry.quantity(price) == pytest.approx(
        sum(solve_competitive_firm(f, price).output for f in firms)
    )
    with pytest.raises(CompetitionError):
        IndustrySupply(())


def test_competition_canvases_build_with_stable_layer_ids() -> None:
    unit = analyze_costs(COST, output_range=(3.0, 8.6), samples=81)
    taxed = analyze_costs(COST.with_unit_tax(4.0), output_range=(3.0, 8.6), samples=81)
    outcome = solve_competitive_firm(COST, 18.0)
    assert "micro.competition.price" in _ids(competitive_firm_canvas(unit, outcome))
    assert any(
        "lost_profit" in name
        for name in _ids(competitive_firm_canvas(unit, outcome, lost_profit=(6.0, 8.2)))
    )
    assert firm_supply_canvas(unit, prices=(12.0, 18.0)).snapshot().layers
    assert "micro.competition.producer_surplus" in _ids(producer_surplus_canvas(unit, outcome))
    assert cost_shift_canvas(unit, taxed, 18.0, tax=4.0).snapshot().layers
    revenue = analyze_revenue_cost(COST, 18.0, output_range=(0.0, 8.6), samples=81)
    assert revenue_cost_profit_canvas(revenue).snapshot().layers
    industry = IndustrySupply((COST, CubicCost(30.0, 40.0, -8.0, 0.6)))
    assert industry_supply_canvas(industry, prices=(12.0, 18.0), price_max=24.0).snapshot().layers
    assert market_and_firm_canvas(LinearDemand(12.0, 0.5), 4.0, firm_output_max=8.6) is not None


def test_competitive_firm_type_grids_cover_profit_break_even_loss_and_shutdown() -> None:
    costs = (
        CubicCost(9.6, 15.6, -3.0, 0.3),
        CubicCost(21.6, 15.6, -3.0, 0.3),
        CubicCost(33.6, 15.6, -3.0, 0.3),
        CubicCost(24.0, 21.6, -3.0, 0.3),
    )
    grids = [
        competitive_short_run_grid(analyze_costs(cost, output_range=(2.0, 8.2)), 12.0)
        for cost in costs
    ]
    ids = [
        {layer.id for placement in grid.placements for layer in placement.canvas.snapshot().layers}
        for grid in grids
    ]
    assert "micro.competition.types.firm.profit" in ids[0]
    assert "micro.competition.types.firm.profit" not in ids[1]
    assert "micro.competition.types.firm.loss" in ids[2]
    assert "micro.competition.types.firm.operating_loss" in ids[3]
    assert competitive_demand_increase_grid(
        analyze_costs(costs[3], output_range=(2.0, 8.2)), (12.0, 16.0)
    ).links


def test_short_run_supply_derivation_grids_link_market_and_firm() -> None:
    analysis = analyze_costs(CubicCost(186.0, 40.0, -10.0, 1.0), output_range=(2.4, 8.2))
    grids = (
        competitive_firm_supply_grid(analysis, (10.0, 22.0, 32.0)),
        competitive_industry_supply_grid(analysis, 20, 22.0),
        competitive_market_supply_equilibrium_grid(analysis, 20, 22.0),
    )
    assert [len(grid.links) for grid in grids] == [3, 2, 1]
    assert all(len(grid.placements) == 2 for grid in grids)


def test_revenue_grids_link_total_average_and_marginal_revenue() -> None:
    monopoly = monopoly_revenue_grid(LinearDemand(10.0, 1.0))
    assert isinstance(monopoly, CanvasGrid)
    assert (monopoly.rows, monopoly.cols, len(monopoly.links)) == (2, 1, 4)
    monopoly_ids = {
        layer.id
        for placement in monopoly.placements
        for layer in placement.canvas.snapshot().layers
    }
    assert {
        "micro.revenue.monopoly.tr",
        "micro.revenue.monopoly.ar",
        "micro.revenue.monopoly.mr",
    } <= monopoly_ids

    base = competitive_revenue_grid(4.0)
    shifted = competitive_revenue_shift_grid(4.0, 6.0)
    base_ids = {
        layer.id for placement in base.placements for layer in placement.canvas.snapshot().layers
    }
    shifted_ids = {
        layer.id for placement in shifted.placements for layer in placement.canvas.snapshot().layers
    }
    assert "micro.revenue.competitive.tr" in base_ids
    assert {
        "micro.revenue.competitive.tr.after",
        "micro.revenue.competitive.unit.after",
        "micro.revenue.competitive.shift.tr",
        "micro.revenue.competitive.shift.unit",
    } <= shifted_ids


def test_example_writes_figures_from_arguments(tmp_path: Path) -> None:
    config = tmp_path / "econ-viz.toml"
    config.write_text('base = "manual"\n', encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "scripts" / "competition" / "competition.py"),
            "--output-dir",
            str(tmp_path / "out"),
            "--config",
            str(config),
            "--title",
            "Own title",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    names = {path.name for path in (tmp_path / "out").glob("*.svg")}
    assert {"firm_profit.svg", "firm_supply.svg", "producer_surplus.svg"} <= names
    assert "Own title" in (tmp_path / "out" / "firm_profit.svg").read_text(encoding="utf-8")


def test_guide_lying_on_a_solid_line_is_dropped_but_not_others() -> None:
    from mosaickit import PathLayer

    from micro_viz.visuals.common import curve, drop_covered_guides, guide

    price = curve(((0.0, 5.0), (10.0, 5.0)), layer_id="price", role="micro.curve.price")
    dashed = curve(((0.0, 3.0), (10.0, 3.0)), layer_id="afc", role="micro.curve.fixed")
    covered = guide((0.0, 5.0), (10.0, 5.0), layer_id="g.covered")
    inside = guide((0.0, 5.0), (4.0, 5.0), layer_id="g.inside")
    under_dashed = guide((0.0, 3.0), (4.0, 3.0), layer_id="g.dashed")
    drop = guide((4.0, 0.0), (4.0, 5.0), layer_id="g.drop")
    kept = drop_covered_guides([price, dashed, covered, inside, under_dashed, drop])
    ids = [layer.id for layer in kept if isinstance(layer, PathLayer)]
    assert ids == ["price", "afc", "g.dashed", "g.drop"]


def test_price_level_keeps_its_mark_without_a_dashed_line() -> None:
    cost = CubicCost(30.0, 36.0, -8.0, 0.6)
    canvas = competitive_firm_canvas(
        analyze_costs(cost, output_range=(3.0, 8.6)), solve_competitive_firm(cost, 8.0)
    )
    ids = {layer.id for layer in canvas.snapshot().layers}
    assert "micro.competition.mark.price" in ids
    assert "micro.competition.guide.price" not in ids


def test_industry_panels_link_the_price_across_every_panel() -> None:
    from micro_viz import industry_supply_panels

    industry = IndustrySupply((CubicCost(50.0, 24.0, -6.0, 0.6), CubicCost(50.0, 42.0, -9.0, 0.75)))
    grid = industry_supply_panels(industry, prices=(11.0, 17.0), price_max=20.0)
    assert len(grid.placements) == 3
    assert len(grid.links) == 2 * 2
