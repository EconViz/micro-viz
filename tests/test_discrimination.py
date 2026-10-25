from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from micro_viz import (
    CostSegment,
    CubicCost,
    DiscriminationError,
    LinearDemand,
    Monopolist,
    PiecewiseCost,
    block_pricing,
    block_pricing_canvas,
    first_degree,
    first_degree_canvas,
    marginal_revenue,
    single_price_canvas,
    third_degree,
    third_degree_canvas,
)

ROOT = Path(__file__).parents[1]
DEMAND = LinearDemand(30.0, 1.0)
FLAT = PiecewiseCost((CostSegment(100.0, 6.0),))


def test_perfect_discrimination_sells_where_demand_meets_mc_and_beats_one_price() -> None:
    result = first_degree(DEMAND, FLAT)
    assert result.quantity == pytest.approx(24.0)
    assert result.profit == pytest.approx(0.5 * 24.0 * 24.0)  # the triangle
    assert result.profit > Monopolist(DEMAND, FLAT).solve().profit
    assert result.extra_profit == pytest.approx(result.profit - result.single_price.profit)


def test_blocks_approach_perfect_discrimination_as_they_multiply() -> None:
    profits = [block_pricing(DEMAND, FLAT, n).profit for n in (1, 3, 12, 60)]
    assert profits == sorted(profits)
    assert profits[-1] == pytest.approx(first_degree(DEMAND, FLAT).profit, rel=0.03)
    with pytest.raises(DiscriminationError):
        block_pricing(DEMAND, FLAT, 0)


def test_third_degree_equalises_marginal_revenue_with_mc() -> None:
    result = third_degree((DEMAND, LinearDemand(20.0, 1.0)), FLAT)
    for market in result.markets:
        assert marginal_revenue(market.demand, market.quantity) == pytest.approx(6.0, abs=1e-6)
    assert result.markets[0].price > result.markets[1].price
    assert result.quantity == pytest.approx(sum(m.quantity for m in result.markets))


def test_a_small_market_is_not_served_when_mc_rises() -> None:
    result = third_degree((DEMAND, LinearDemand(10.0, 1.0)), CubicCost(0.0, 6.0, 0.0, 0.3))
    assert [m.served for m in result.markets] == [True, False]
    with pytest.raises(DiscriminationError):
        third_degree((DEMAND,), FLAT)


def test_builders_and_example(tmp_path: Path) -> None:
    assert single_price_canvas(DEMAND, FLAT, groups=True, title="T").spec.title == "T"
    assert first_degree_canvas(first_degree(DEMAND, FLAT)).snapshot().layers
    assert block_pricing_canvas(block_pricing(DEMAND, FLAT, 4), average_cost=True)
    assert third_degree_canvas(third_degree((DEMAND, LinearDemand(20.0, 1.0)), FLAT)) is not None
    config = tmp_path / "econ-viz.toml"
    config.write_text('base = "manual"\n', encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "scripts" / "price_discrimination.py"),
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
    assert "Own title" in (tmp_path / "out" / "single_price.svg").read_text(encoding="utf-8")
