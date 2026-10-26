from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from micro_viz import (
    CompetitionError,
    CostSegment,
    CubicCost,
    LinearDemand,
    Monopolist,
    PiecewiseCost,
    analyze_costs,
    natural_monopoly_canvas,
    natural_monopoly_pricing,
    price_ceiling_canvas,
    price_ceiling_outcome,
)

COST = CubicCost(20.0, 6.0, -1.5, 0.15)
DEMAND = LinearDemand(30.0, 2.0)
NATURAL = PiecewiseCost((CostSegment(40.0, 4.0),), fixed_cost=120.0)
ROOT = Path(__file__).parents[1]


def test_a_binding_ceiling_lowers_price_and_may_raise_output() -> None:
    firm = Monopolist(DEMAND, COST)
    free = firm.solve()
    capped = price_ceiling_outcome(firm, 12.0)
    assert capped.price == pytest.approx(12.0)
    assert capped.price < free.price
    assert capped.quantity > free.quantity
    assert capped.marginal_revenue(0.0) == 12.0
    assert capped.marginal_revenue(capped.ceiling_quantity + 1) < 12.0


def test_a_ceiling_above_the_monopoly_price_does_not_bind() -> None:
    firm = Monopolist(DEMAND, COST)
    free = firm.solve()
    capped = price_ceiling_outcome(firm, free.price + 3.0)
    assert capped.quantity == pytest.approx(free.quantity, abs=0.01)
    with pytest.raises(CompetitionError):
        price_ceiling_outcome(firm, 0.0)


def test_natural_monopoly_prices_are_ordered() -> None:
    pricing = natural_monopoly_pricing(Monopolist(LinearDemand(30.0, 1.0), NATURAL))
    assert pricing.marginal_cost.price == pytest.approx(4.0, abs=0.05)
    assert pricing.marginal_cost.profit < 0
    assert pricing.average_cost.profit == pytest.approx(0.0, abs=0.5)
    assert pricing.unregulated.price > pricing.average_cost.price > pricing.marginal_cost.price
    assert (
        pricing.unregulated.quantity
        < pricing.average_cost.quantity
        < pricing.marginal_cost.quantity
    )


def test_builders_and_example(tmp_path: Path) -> None:
    unit = analyze_costs(COST, output_range=(2.0, 10.0), samples=81)
    capped = price_ceiling_outcome(Monopolist(DEMAND, COST), 12.0)
    ids = {layer.id for layer in price_ceiling_canvas(capped, unit, title="T").snapshot().layers}
    assert "micro.regulation.ceiling" in ids
    demand = LinearDemand(30.0, 1.0)
    natural = analyze_costs(NATURAL, output_range=(2.0, 30.0), samples=81)
    pricing = natural_monopoly_pricing(Monopolist(demand, NATURAL))
    assert natural_monopoly_canvas(pricing, natural).snapshot().layers
    config = tmp_path / "econ-viz.toml"
    config.write_text('base = "manual"\n', encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "scripts" / "regulation" / "regulation.py"),
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
    assert "Own title" in (tmp_path / "out" / "price_ceiling.svg").read_text(encoding="utf-8")


def test_loss_is_the_gap_between_atc_and_price_at_the_regulated_output() -> None:
    from mosaickit import FillLayer, TextLayer

    firm = Monopolist(LinearDemand(30.0, 1.0), NATURAL)
    pricing = natural_monopoly_pricing(firm)
    analysis = analyze_costs(NATURAL, output_range=(2.0, 30.0), samples=81)
    layers = {x.id: x for x in natural_monopoly_canvas(pricing, analysis).snapshot().layers}
    fill = layers["micro.regulation.loss"]
    assert isinstance(fill, FillLayer)
    q = pricing.marginal_cost.quantity
    atc = NATURAL.average_total_cost(q)
    ys = sorted({y for _, y in fill.boundary})
    xs = sorted({x for x, _ in fill.boundary})
    assert ys == pytest.approx([pricing.marginal_cost.price, atc])
    assert xs == pytest.approx([0.0, q])
    label = layers["micro.regulation.loss.label"]
    assert isinstance(label, TextLayer)
    assert 0 < label.position[0] < q and ys[0] < label.position[1] < ys[1]
