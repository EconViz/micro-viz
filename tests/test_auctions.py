from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from micro_viz import (
    Auction,
    AuctionError,
    Signaling,
    bid_functions_canvas,
    revenue_equivalence_canvas,
)

ROOT = Path(__file__).parents[1]


def test_bid_functions() -> None:
    auction = Auction(4, 100.0)
    assert auction.second_price_bid(60.0) == 60.0
    assert auction.first_price_bid(60.0) == pytest.approx(45.0)
    assert auction.shading(60.0) == pytest.approx(15.0)
    assert Auction(10, 100.0).shading(60.0) < auction.shading(60.0)


def test_revenue_equivalence() -> None:
    for bidders in (2, 3, 6, 10):
        auction = Auction(bidders, 100.0)
        closed = (bidders - 1) / (bidders + 1) * 100.0
        assert auction.expected_revenue == pytest.approx(closed)
        assert auction.expected_revenue_numeric(True) == pytest.approx(closed, rel=1e-3)
        assert auction.expected_revenue_numeric(False) == pytest.approx(closed, rel=1e-3)
        assert auction.expected_profit(70.0, True) == pytest.approx(
            auction.expected_profit(70.0, False)
        )


def test_more_bidders_raise_revenue() -> None:
    assert Auction(3).expected_revenue < Auction(6).expected_revenue < 1.0


def test_pooling_and_separating_signals() -> None:
    signaling = Signaling(20.0, 2.0, 1.0)
    assert signaling.pooling(5.0) and not signaling.pooling(15.0)
    assert signaling.separating(15.0) and not signaling.separating(5.0)


def test_invalid_inputs() -> None:
    with pytest.raises(AuctionError):
        Auction(1)
    with pytest.raises(AuctionError):
        Auction(3, 0.0)
    with pytest.raises(AuctionError):
        Auction(3).first_price_bid(2.0)


def test_canvases_follow_parameters() -> None:
    assert bid_functions_canvas((Auction(3),), title="T").spec.title == "T"
    assert revenue_equivalence_canvas((2, 3, 4)) is not None


def test_example_runs(tmp_path: Path) -> None:
    config = tmp_path / "econ-viz.toml"
    config.write_text('base = "manual"\n', encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "scripts" / "auctions" / "auctions.py"),
            "--output-dir",
            str(tmp_path / "out"),
            "--config",
            str(config),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    assert (tmp_path / "out" / "revenue_equivalence.svg").exists()
