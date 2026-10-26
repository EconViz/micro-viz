from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from micro_viz import (
    DominantFirm,
    KinkedDemand,
    OligopolyError,
    cartel_elasticity_canvas,
    dominant_firm_canvas,
    kinked_demand_canvas,
)

ROOT = Path(__file__).parents[1]
KINK = KinkedDemand(10.0, 20.0, 0.5, 1.5)
FIRM = DominantFirm(40.0, 1.0, 6.0, 1.5, 4.0, 0.2)


def test_kinked_demand_has_marginal_revenue_gap() -> None:
    low, high = KINK.gap
    assert (low, high) == pytest.approx((5.0, 15.0))
    assert KINK.marginal_revenue(10.0 - 1e-9) == pytest.approx(high)
    assert KINK.marginal_revenue(10.0 + 1e-9) == pytest.approx(low, abs=1e-6)
    assert KINK.demand(10.0) == pytest.approx(20.0)


def test_cost_shifts_inside_the_gap_leave_price_unchanged() -> None:
    assert KINK.keeps_price(6.0) and KINK.keeps_price(12.0)
    assert not KINK.keeps_price(16.0)


def test_kinked_demand_validation() -> None:
    with pytest.raises(OligopolyError):
        KinkedDemand(10.0, 20.0, 2.0, 0.5)
    with pytest.raises(OligopolyError):
        KinkedDemand(10.0, 20.0, 0.5, 3.0)


def test_dominant_firm_equates_mr_and_mc_on_residual_demand() -> None:
    result = FIRM.solve()
    assert result.marginal_revenue == pytest.approx(
        FIRM.cost_intercept + FIRM.cost_slope * result.dominant_quantity
    )
    assert FIRM.inverse_residual(result.dominant_quantity) == pytest.approx(result.price)
    assert result.fringe_quantity == pytest.approx(FIRM.fringe_supply(result.price))
    assert result.total_quantity == pytest.approx(result.dominant_quantity + result.fringe_quantity)


def test_elastic_demand_leaves_little_market_power() -> None:
    inelastic = DominantFirm(30.0, 0.6, 6.0, 1.0, 4.0, 0.2).solve()
    elastic = DominantFirm(60.0, 2.5, 6.0, 1.0, 4.0, 0.2).solve()

    margin_inelastic = (inelastic.price - 4.0) / inelastic.price
    margin_elastic = (elastic.price - 4.0) / elastic.price
    assert margin_elastic < margin_inelastic


def test_dominant_firm_validation() -> None:
    with pytest.raises(OligopolyError):
        DominantFirm(40.0, 1.0, 50.0, 1.5, 4.0)
    with pytest.raises(OligopolyError):
        DominantFirm(40.0, 1.0, 6.0, 0.0, 4.0)


def test_canvases_follow_parameters() -> None:
    assert kinked_demand_canvas(KINK, (8.0,), title="T").spec.title == "T"
    plain = kinked_demand_canvas(KINK, (8.0,)).snapshot().layers
    more = kinked_demand_canvas(KINK, (8.0, 12.0)).snapshot().layers
    assert len(more) > len(plain)
    assert dominant_firm_canvas(FIRM, cartel=True) is not None
    assert cartel_elasticity_canvas(FIRM, FIRM) is not None


def test_example_runs(tmp_path: Path) -> None:
    config = tmp_path / "econ-viz.toml"
    config.write_text('base = "manual"\n', encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "scripts" / "oligopoly" / "dominant_firm.py"),
            "--output-dir",
            str(tmp_path / "out"),
            "--config",
            str(config),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    assert (tmp_path / "out" / "kinked_demand.svg").exists()
