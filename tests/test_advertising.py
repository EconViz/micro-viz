from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from micro_viz import (
    AdvertisingDecision,
    AdvertisingError,
    LinearDemand,
    advertising_effect_canvas,
)

ROOT = Path(__file__).parents[1]
BASE = LinearDemand(30.0, 1.0)
BETTER = LinearDemand(36.0, 1.0)


def test_optimum_where_mr_equals_mc() -> None:
    decision = AdvertisingDecision(BASE, BETTER, 4.0, 40.0, 60.0)
    before, after = decision.before(), decision.after()
    assert before.quantity == pytest.approx(13.0)
    assert before.price == pytest.approx(17.0)
    assert after.quantity == pytest.approx(16.0)
    assert after.price == pytest.approx(20.0)


def test_profit_is_the_rectangle_between_price_and_average_cost() -> None:
    decision = AdvertisingDecision(BASE, BETTER, 4.0, 40.0, 60.0)
    for outcome in (decision.before(), decision.after()):
        assert outcome.profit == pytest.approx(
            (outcome.price - outcome.average_cost) * outcome.quantity
        )


def test_average_cost_rises_after_advertising() -> None:
    decision = AdvertisingDecision(BASE, BETTER, 4.0, 40.0, 60.0)
    for quantity in (5.0, 13.0, 30.0):
        assert decision.average_cost(quantity, True) > decision.average_cost(quantity)


def test_advertising_can_fail_to_pay() -> None:
    assert AdvertisingDecision(BASE, BETTER, 4.0, 40.0, 60.0).worthwhile
    assert not AdvertisingDecision(BASE, BETTER, 4.0, 40.0, 500.0).worthwhile


def test_invalid_inputs() -> None:
    with pytest.raises(AdvertisingError):
        AdvertisingDecision(BETTER, BASE, 4.0, 40.0, 60.0)
    with pytest.raises(AdvertisingError):
        AdvertisingDecision(BASE, BETTER, -1.0, 40.0, 60.0)
    with pytest.raises(AdvertisingError):
        AdvertisingDecision(BASE, BETTER, 4.0, 40.0, 60.0).average_cost(0.0)


def test_canvas_follows_parameters() -> None:
    decision = AdvertisingDecision(BASE, BETTER, 4.0, 40.0, 60.0)
    assert advertising_effect_canvas(decision, title="T").spec.title == "T"
    loss = AdvertisingDecision(BASE, BETTER, 4.0, 200.0, 60.0)
    assert advertising_effect_canvas(loss) is not None


def test_example_runs(tmp_path: Path) -> None:
    config = tmp_path / "econ-viz.toml"
    config.write_text('base = "manual"\n', encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "scripts" / "advertising.py"),
            "--output-dir",
            str(tmp_path / "out"),
            "--config",
            str(config),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    assert (tmp_path / "out" / "advertising.svg").exists()
