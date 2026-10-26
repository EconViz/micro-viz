from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from micro_viz import (
    DifferentiatedDuopoly,
    Duopoly,
    OligopolyError,
    bertrand,
    collusive_total,
    competitive_total,
    cournot,
    price_reaction_canvas,
    reaction_curves_canvas,
    residual_demand_canvas,
    stackelberg,
)

ROOT = Path(__file__).parents[1]
DUOPOLY = Duopoly(30.0, 1.0, 6.0, 6.0)
ASYMMETRIC = Duopoly(30.0, 1.0, 4.0, 8.0)
DIFFERENTIATED = DifferentiatedDuopoly(12.0, 12.0, 2.0, 2.0, 1.0, 1.0, 2.0, 2.0)


def test_cournot_satisfies_both_best_responses() -> None:
    for duopoly in (DUOPOLY, ASYMMETRIC):
        result = cournot(duopoly)
        assert result.q1 == pytest.approx(duopoly.best_response_1(result.q2))
        assert result.q2 == pytest.approx(duopoly.best_response_2(result.q1))


def test_cournot_closed_form() -> None:
    result = cournot(DUOPOLY)
    assert result.q1 == pytest.approx((30.0 - 6.0) / 3.0)
    assert result.price == pytest.approx(30.0 - 16.0)


def test_stackelberg_leader_produces_twice_the_follower() -> None:
    result = stackelberg(DUOPOLY)
    assert result.q1 == pytest.approx(2 * result.q2)
    assert result.profit_1 > cournot(DUOPOLY).profit_1
    assert stackelberg(DUOPOLY, leader=2).q2 > stackelberg(DUOPOLY, leader=2).q1


def test_collusion_halves_competitive_output() -> None:
    assert collusive_total(DUOPOLY) == pytest.approx(competitive_total(DUOPOLY) / 2)
    cournot_total = sum((cournot(DUOPOLY).q1, cournot(DUOPOLY).q2))
    assert collusive_total(DUOPOLY) < cournot_total < competitive_total(DUOPOLY)


def test_bertrand_nash_and_collusive_prices() -> None:
    result = bertrand(DIFFERENTIATED)
    assert result.nash[0] == pytest.approx(DIFFERENTIATED.best_price_1(result.nash[1]))
    assert result.nash[1] == pytest.approx(DIFFERENTIATED.best_price_2(result.nash[0]))
    assert result.collusive[0] > result.nash[0]
    assert sum(result.collusive_profits) > sum(result.nash_profits)


def test_invalid_inputs() -> None:
    with pytest.raises(OligopolyError):
        Duopoly(30.0, 0.0, 6.0, 6.0)
    with pytest.raises(OligopolyError):
        Duopoly(30.0, 1.0, 31.0, 6.0)
    with pytest.raises(OligopolyError):
        stackelberg(DUOPOLY, leader=3)
    with pytest.raises(OligopolyError):
        DifferentiatedDuopoly(12.0, 12.0, 1.0, 1.0, 3.0, 3.0, 2.0, 2.0)


def test_canvases_follow_parameters() -> None:
    assert residual_demand_canvas(DUOPOLY, (0.0, 5.0), title="T").spec.title == "T"
    plain = reaction_curves_canvas(DUOPOLY).snapshot().layers
    full = reaction_curves_canvas(DUOPOLY, competitive=True, collusive=True, leader=1)
    assert len(full.snapshot().layers) > len(plain)
    assert price_reaction_canvas(DIFFERENTIATED, collusive=False) is not None


def test_example_runs(tmp_path: Path) -> None:
    config = tmp_path / "econ-viz.toml"
    config.write_text('base = "manual"\n', encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "scripts" / "oligopoly" / "oligopoly.py"),
            "--output-dir",
            str(tmp_path / "out"),
            "--config",
            str(config),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    assert (tmp_path / "out" / "cournot.svg").exists()
