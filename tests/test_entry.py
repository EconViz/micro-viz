from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from micro_viz import (
    CubicCost,
    IndustryEntry,
    LinearDemand,
    LongRunError,
    PlantFamily,
    analyze_costs,
    break_even_price,
    constant_cost_canvas,
    entry_canvas,
    increasing_cost_canvas,
    long_run_firm_canvas,
    rent_canvas,
)

ROOT = Path(__file__).parents[1]
COST = CubicCost(50.0, 24.0, -6.0, 0.6)
DEMAND = LinearDemand(40.0, 0.04)
INDUSTRY = IndustryEntry(DEMAND, COST)
VIEW = analyze_costs(COST, output_range=(2.0, 12.0), samples=81)


def test_few_firms_earn_profit_and_entry_drives_it_to_zero() -> None:
    start = INDUSTRY.equilibrium(50.0)
    assert start.profit > 0 and start.price > INDUSTRY.long_run_price
    firms = INDUSTRY.long_run_firms()
    assert firms > 50.0
    end = INDUSTRY.equilibrium(firms)
    assert end.profit == pytest.approx(0.0, abs=1e-6)
    assert end.price == pytest.approx(break_even_price(COST))


def test_market_clears_at_the_equilibrium() -> None:
    point = INDUSTRY.equilibrium(80.0)
    assert INDUSTRY.supply(80.0, point.price) == pytest.approx(DEMAND.quantity(point.price))
    assert point.quantity == pytest.approx(80.0 * point.firm_output)


def test_demand_increase_keeps_the_long_run_price_for_constant_cost() -> None:
    higher = LinearDemand(46.0, 0.04)
    assert IndustryEntry(higher, COST).long_run_price == INDUSTRY.long_run_price
    assert INDUSTRY.long_run_firms(higher) > INDUSTRY.long_run_firms()


def test_builders_and_example(tmp_path: Path) -> None:
    higher = LinearDemand(46.0, 0.04)
    advantaged = CubicCost(20.0, 24.0, -6.0, 0.6)
    other = analyze_costs(advantaged, output_range=(2.0, 12.0), samples=81)
    assert entry_canvas(INDUSTRY, 50.0, VIEW) is not None
    assert rent_canvas(INDUSTRY, advantaged, VIEW, other) is not None
    assert constant_cost_canvas(INDUSTRY, higher, VIEW) is not None
    assert increasing_cost_canvas(INDUSTRY, higher, 0.02, VIEW) is not None
    with pytest.raises(LongRunError):
        increasing_cost_canvas(INDUSTRY, higher, 0.0, VIEW)
    family = PlantFamily(10.0, 4.0, 1.0, 0.6)
    assert long_run_firm_canvas(family, 7.0, 18.0, title="T").spec.title == "T"
    config = tmp_path / "econ-viz.toml"
    config.write_text('base = "manual"\n', encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "scripts" / "long_run_competition.py"),
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
    assert "Own title" in (tmp_path / "out" / "long_run_firm.svg").read_text(encoding="utf-8")
