from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from micro_viz import (
    Gamble,
    IncomeUtility,
    MeanVarianceInvestor,
    RiskReturnLine,
    UncertaintyError,
    risk_attitude_canvas,
    risk_premium_canvas,
    risk_return_choice_canvas,
    utility_of_income_canvas,
)

ROOT = Path(__file__).parents[1]
GAMBLE = Gamble(10.0, 30.0, 0.5)
CONCAVE = IncomeUtility(0.5)
CONVEX = IncomeUtility(2.0)
LINEAR = IncomeUtility(1.0)
LINE = RiskReturnLine(5.0, 0.6)


def test_attitude_follows_curvature() -> None:
    assert (CONCAVE.attitude, CONVEX.attitude, LINEAR.attitude) == ("averse", "loving", "neutral")


def test_expected_utility_lies_on_the_chord() -> None:
    for utility in (CONCAVE, CONVEX, LINEAR):
        low, high = GAMBLE.chord(utility)
        expected_income = GAMBLE.expected_income
        height = low[1] + (high[1] - low[1]) * (expected_income - low[0]) / (high[0] - low[0])
        assert GAMBLE.expected_utility(utility) == pytest.approx(height)


def test_risk_premium_signs() -> None:
    assert GAMBLE.expected_income == pytest.approx(20.0)
    assert GAMBLE.risk_premium(CONCAVE) > 0
    assert GAMBLE.risk_premium(CONVEX) < 0
    assert GAMBLE.risk_premium(LINEAR) == pytest.approx(0.0)
    equivalent = GAMBLE.certainty_equivalent(CONCAVE)
    assert CONCAVE.utility(equivalent) == pytest.approx(GAMBLE.expected_utility(CONCAVE))
    assert equivalent < GAMBLE.expected_income


def test_more_risk_aversion_means_steeper_indifference_curves() -> None:
    steep, flat = MeanVarianceInvestor(0.08), MeanVarianceInvestor(0.02)
    assert steep.slope(10.0) > flat.slope(10.0)
    assert steep.indifference_mean(5.0, 10.0) > flat.indifference_mean(5.0, 10.0)
    assert steep.utility(steep.indifference_mean(5.0, 10.0), 10.0) == pytest.approx(5.0)


def test_tangency_matches_the_slope_of_the_line() -> None:
    investor = MeanVarianceInvestor(0.08)
    sd, mean = LINE.choice(investor)
    assert investor.slope(sd) == pytest.approx(LINE.price_of_risk)
    assert mean == pytest.approx(LINE.mean(sd))
    flat = MeanVarianceInvestor(0.02)
    assert LINE.choice(flat)[0] > sd
    assert LINE.borrows(flat, 12.0) and not LINE.borrows(investor, 12.0)


def test_invalid_inputs() -> None:
    with pytest.raises(UncertaintyError):
        IncomeUtility(0.0)
    with pytest.raises(UncertaintyError):
        Gamble(30.0, 10.0)
    with pytest.raises(UncertaintyError):
        Gamble(10.0, 30.0, 1.0)
    with pytest.raises(UncertaintyError):
        MeanVarianceInvestor(-1.0)
    with pytest.raises(UncertaintyError):
        CONCAVE.utility(-1.0)


def test_canvases_follow_parameters() -> None:
    assert utility_of_income_canvas(GAMBLE, (CONCAVE, CONVEX, LINEAR)) is not None
    assert risk_premium_canvas(GAMBLE, CONCAVE, title="T").spec.title == "T"
    investors = (MeanVarianceInvestor(0.08), MeanVarianceInvestor(0.02))
    assert risk_attitude_canvas(investors, 5.0, 30.0) is not None
    plain = risk_return_choice_canvas(LINE, investors[:1], 5.0, 30.0).snapshot().layers
    more = risk_return_choice_canvas(LINE, investors, 5.0, 30.0, 12.0).snapshot().layers
    assert len(more) > len(plain)


def test_example_runs(tmp_path: Path) -> None:
    config = tmp_path / "econ-viz.toml"
    config.write_text('base = "manual"\n', encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "scripts" / "uncertainty.py"),
            "--output-dir",
            str(tmp_path / "out"),
            "--config",
            str(config),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    assert (tmp_path / "out" / "risk_premium.svg").exists()
