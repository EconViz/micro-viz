from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from micro_viz import (
    CubicCost,
    LinearDemand,
    Monopolist,
    analyze_costs,
    excess_capacity_grid,
    long_run_demand,
    monopolistic_competition_grid,
    monopolistic_long_run_canvas,
    solve_monopolistic_competition,
)

COST = CubicCost(20.0, 6.0, -1.5, 0.15)
DEMAND = LinearDemand(30.0, 2.0)
ROOT = Path(__file__).parents[1]


def test_long_run_demand_is_tangent_to_average_total_cost() -> None:
    outcome = solve_monopolistic_competition(DEMAND, COST)
    q = outcome.long_run.quantity
    assert outcome.long_run.profit == pytest.approx(0.0, abs=1e-6)
    assert outcome.long_run.price == pytest.approx(COST.total_cost(q) / q, abs=1e-6)
    slope_of_atc = (COST.marginal_cost(q) - COST.total_cost(q) / q) / q
    assert slope_of_atc == pytest.approx(-DEMAND.slope, abs=1e-4)


def test_mr_equals_mc_in_the_long_run_and_price_exceeds_mc() -> None:
    outcome = solve_monopolistic_competition(DEMAND, COST)
    q = outcome.long_run.quantity
    assert outcome.long_run_demand.intercept - 2 * DEMAND.slope * q == pytest.approx(
        COST.marginal_cost(q), abs=1e-6
    )
    assert outcome.long_run.price > outcome.long_run.marginal_cost


def test_excess_capacity_is_output_at_minimum_atc_less_long_run_output() -> None:
    outcome = solve_monopolistic_competition(DEMAND, COST)
    assert outcome.minimum_atc_output == COST.minimum_average_total_cost_output
    assert outcome.excess_capacity == pytest.approx(
        outcome.minimum_atc_output - outcome.long_run.quantity
    )
    assert outcome.excess_capacity > 0
    assert outcome.short_run.profit > 0


def test_a_firm_with_a_loss_cannot_enter() -> None:
    from micro_viz import CompetitionError

    with pytest.raises(CompetitionError):
        long_run_demand(LinearDemand(8.0, 2.0), COST)
    assert Monopolist(LinearDemand(8.0, 2.0), COST).solve().profit < 0


def test_builders_return_figures() -> None:
    outcome = solve_monopolistic_competition(DEMAND, COST)
    unit = analyze_costs(COST, output_range=(2.0, 10.0), samples=81)
    assert monopolistic_competition_grid(outcome, unit) is not None
    assert excess_capacity_grid(outcome, unit) is not None
    canvas = monopolistic_long_run_canvas(outcome, unit, excess_capacity=True, title="T")
    assert canvas.spec.title == "T"
    assert any(layer.id.endswith("brace.excess") for layer in canvas.snapshot().layers)


@pytest.mark.parametrize("script", ["monopolistic_competition", "animate_monopolistic"])  # type: ignore[untyped-decorator]
def test_examples_run(tmp_path: Path, script: str) -> None:
    if script.startswith("animate"):
        pytest.importorskip("kinetickit")
    config = tmp_path / "econ-viz.toml"
    config.write_text('base = "manual"\n', encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "scripts" / f"{script}.py"),
            "--output-dir",
            str(tmp_path / "out"),
            "--config",
            str(config),
            "--steps",
            "2",
        ]
        if script.startswith("animate")
        else [
            sys.executable,
            str(ROOT / "examples" / "scripts" / f"{script}.py"),
            "--output-dir",
            str(tmp_path / "out"),
            "--config",
            str(config),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    assert list((tmp_path / "out").glob("*.svg"))
