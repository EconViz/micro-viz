from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from micro_viz import (
    CubicCost,
    LinearDemand,
    Monopolist,
    MonopolyError,
    MultiplantMonopoly,
    analyze_costs,
    elasticity,
    lerner_markup_canvas,
    marginal_revenue,
    monopoly_canvas,
    monopoly_demand_shift_canvas,
    monopoly_dwl_canvas,
    monopoly_tax_canvas,
    monopoly_totals_canvas,
    monopoly_totals_grid,
    multiplant_canvas,
)

COST = CubicCost(20.0, 6.0, -1.5, 0.15)
DEMAND = LinearDemand(30.0, 2.0)
ROOT = Path(__file__).parents[1]


def test_mr_equals_mc_at_the_optimum() -> None:
    outcome = Monopolist(DEMAND, COST).solve()
    assert marginal_revenue(DEMAND, outcome.quantity) == pytest.approx(
        COST.marginal_cost(outcome.quantity), abs=1e-6
    )
    assert outcome.price == pytest.approx(DEMAND.price(outcome.quantity))


def test_lerner_index_is_the_inverse_elasticity() -> None:
    outcome = Monopolist(DEMAND, COST).solve()
    assert outcome.lerner_index == pytest.approx(1 / abs(elasticity(DEMAND, outcome.quantity)))
    assert outcome.lerner_index == pytest.approx(1 / abs(outcome.elasticity))


def test_deadweight_loss_matches_the_triangle_when_mc_is_linear() -> None:
    flat = CubicCost(0.0, 4.0, 0.0, 1e-9)
    outcome = Monopolist(DEMAND, flat).solve()
    triangle = (
        0.5
        * (outcome.competitive_quantity - outcome.quantity)
        * (outcome.price - outcome.competitive_price)
    )
    assert outcome.deadweight_loss == pytest.approx(triangle, rel=1e-3)
    assert outcome.transfer == pytest.approx(
        (outcome.price - outcome.competitive_price) * outcome.quantity
    )


def test_monopoly_restricts_output_below_competition() -> None:
    outcome = Monopolist(DEMAND, COST).solve()
    assert outcome.quantity < outcome.competitive_quantity
    assert outcome.price > outcome.competitive_price


def test_unit_tax_raises_price_by_less_than_tax_for_linear_demand() -> None:
    flat = CubicCost(0.0, 4.0, 0.0, 1e-9)
    before = Monopolist(DEMAND, flat).solve()
    after = Monopolist(DEMAND, flat.with_unit_tax(2.0)).solve()
    assert after.price - before.price == pytest.approx(1.0, abs=1e-3)


def test_multiplant_equalises_marginal_costs_with_mr() -> None:
    plants = (CubicCost(10.0, 4.0, -1.0, 0.12), CubicCost(10.0, 8.0, -1.5, 0.15))
    firm = MultiplantMonopoly(LinearDemand(30.0, 0.8), plants)
    outcome = firm.solve()
    for plant, quantity in zip(plants, outcome.plant_outputs, strict=True):
        assert plant.marginal_cost(quantity) == pytest.approx(outcome.marginal_cost, abs=1e-6)
    assert marginal_revenue(firm.demand, outcome.quantity) == pytest.approx(
        outcome.marginal_cost, abs=1e-6
    )
    with pytest.raises(MonopolyError):
        MultiplantMonopoly(firm.demand, plants[:1])


def test_builders_return_canvases_with_stable_ids() -> None:
    unit = analyze_costs(COST, output_range=(2.0, 10.0), samples=81)
    firm = Monopolist(DEMAND, COST)
    outcome = firm.solve()
    taxed_cost = COST.with_unit_tax(4.0)
    taxed = analyze_costs(taxed_cost, output_range=(2.0, 10.0), samples=81)
    ids = {layer.id for layer in monopoly_canvas(outcome, unit, profit=True).snapshot().layers}
    assert {"micro.monopoly.demand", "micro.monopoly.mr", "micro.monopoly.profit"} <= ids
    assert monopoly_dwl_canvas(outcome, unit).snapshot().layers
    assert monopoly_tax_canvas(outcome, Monopolist(DEMAND, taxed_cost).solve(), unit, taxed)
    shifted = firm.with_demand(LinearDemand(36.0, 2.0)).solve()
    assert monopoly_demand_shift_canvas(outcome, shifted, unit).snapshot().layers
    rotated = firm.with_demand(LinearDemand(30.0, 1.5)).solve()
    assert monopoly_demand_shift_canvas(outcome, rotated, unit, rotate=True).snapshot().layers
    assert monopoly_totals_canvas(outcome, output_range=(2.0, 10.0)).snapshot().layers
    assert monopoly_totals_grid(outcome, unit) is not None
    assert lerner_markup_canvas((outcome, outcome), (unit, unit)) is not None
    plants = (CubicCost(10.0, 4.0, -1.0, 0.12), CubicCost(10.0, 8.0, -1.5, 0.15))
    multi = MultiplantMonopoly(LinearDemand(30.0, 0.8), plants)
    assert multiplant_canvas(multi, multi.solve()) is not None


def test_example_writes_figures_and_title(tmp_path: Path) -> None:
    config = tmp_path / "econ-viz.toml"
    config.write_text('base = "manual"\n', encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "scripts" / "monopoly.py"),
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
    assert {"monopoly.svg", "monopoly_dwl.svg", "multiplant.svg"} <= names
    assert "Own title" in (tmp_path / "out" / "monopoly.svg").read_text(encoding="utf-8")


def test_animation_example_saves_animated_svgs(tmp_path: Path) -> None:
    pytest.importorskip("kinetickit")
    config = tmp_path / "econ-viz.toml"
    config.write_text('base = "manual"\n', encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "scripts" / "animate_monopoly.py"),
            "--output-dir",
            str(tmp_path / "out"),
            "--config",
            str(config),
            "--steps",
            "2",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    svg = (tmp_path / "out" / "monopoly_demand_shift_animated.svg").read_text(encoding="utf-8")
    assert "<animate" in svg
