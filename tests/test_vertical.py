from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from micro_viz import (
    LinearDemand,
    VerticalChain,
    VerticalError,
    double_marginalization_canvas,
    integrated_firm_canvas,
    transfer_price_outside_market_canvas,
    transfer_pricing,
)

ROOT = Path(__file__).parents[1]
CHAIN = VerticalChain(LinearDemand(40.0, 1.0), 2.0, 2.0, 0.5)


def test_stacked_upstream_sets_its_mr_equal_to_mc() -> None:
    result = CHAIN.stacked()
    assert CHAIN.upstream_marginal_revenue(result.quantity) == pytest.approx(
        CHAIN.upstream_marginal_cost(result.quantity)
    )
    assert result.transfer_price == pytest.approx(CHAIN.net_marginal_revenue(result.quantity))


def test_integrated_firm_sets_nmr_equal_to_mc() -> None:
    result = CHAIN.integrated()
    assert CHAIN.net_marginal_revenue(result.quantity) == pytest.approx(
        CHAIN.upstream_marginal_cost(result.quantity)
    )


def test_double_marginalization_cuts_output_and_raises_price() -> None:
    stacked, integrated = CHAIN.stacked(), CHAIN.integrated()
    assert stacked.quantity < integrated.quantity
    assert stacked.final_price > integrated.final_price
    assert integrated.profit > stacked.profit


def test_transfer_price_equals_market_price() -> None:
    result = transfer_pricing(CHAIN, 10.0)
    assert CHAIN.upstream_marginal_cost(result.upstream_quantity) == pytest.approx(10.0)
    assert CHAIN.net_marginal_revenue(result.downstream_quantity) == pytest.approx(10.0)
    assert result.transfer_price == 10.0
    assert result.outside_sales == pytest.approx(
        result.upstream_quantity - result.downstream_quantity
    )
    assert (
        transfer_pricing(CHAIN, 4.0).outside_sales < 0 < transfer_pricing(CHAIN, 14.0).outside_sales
    )


def test_invalid_inputs() -> None:
    with pytest.raises(VerticalError):
        VerticalChain(LinearDemand(40.0, 1.0), 30.0, 20.0)
    with pytest.raises(VerticalError):
        transfer_pricing(VerticalChain(LinearDemand(40.0, 1.0), 2.0, 2.0), 10.0)
    with pytest.raises(VerticalError):
        transfer_pricing(CHAIN, -1.0)


def test_canvases_follow_parameters() -> None:
    assert double_marginalization_canvas(CHAIN, title="T").spec.title == "T"
    assert integrated_firm_canvas(CHAIN) is not None
    kinked = transfer_price_outside_market_canvas(CHAIN, 10.0)
    flat = transfer_price_outside_market_canvas(CHAIN, 10.0, kinked=False)
    assert kinked.snapshot().layers != flat.snapshot().layers


def test_example_runs(tmp_path: Path) -> None:
    config = tmp_path / "econ-viz.toml"
    config.write_text('base = "manual"\n', encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "scripts" / "vertical" / "vertical.py"),
            "--output-dir",
            str(tmp_path / "out"),
            "--config",
            str(config),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    assert (tmp_path / "out" / "transfer_price.svg").exists()
