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


def test_fair_insurance_gives_full_cover_and_unfair_partial() -> None:
    from micro_viz import StateClaims, state_claims_canvas

    claims = StateClaims(100.0, 40.0, 0.25, 0.5)
    c1, c2 = claims.choice(0.25)
    assert c1 == pytest.approx(c2)
    assert claims.coverage(0.25) == pytest.approx(45.0)
    u1, u2 = claims.choice(0.3)
    assert u2 < u1
    assert 0 < claims.coverage(0.3) < 45.0
    # the choice lies on the budget line and the indifference curve is tangent there
    assert claims.budget_c2(u1, 0.3) == pytest.approx(u2)
    level = claims.utility(u1, u2)
    assert claims.indifference_c2(u1, level) == pytest.approx(u2)
    assert state_claims_canvas(claims, (0.25, 0.3), title="T").spec.title == "T"
    with pytest.raises(UncertaintyError):
        StateClaims(100.0, 40.0, 0.25, 1.5)


def test_stochastic_dominance_checks() -> None:
    from micro_viz import (
        UniformLottery,
        cdf_crossing,
        first_order_dominates,
        second_order_dominates,
        stochastic_dominance_canvas,
    )

    a, b, c = UniformLottery(30.0, 90.0), UniformLottery(10.0, 70.0), UniformLottery(40.0, 60.0)
    assert first_order_dominates(a, b) and not first_order_dominates(b, a)
    assert cdf_crossing(a, b) is None
    assert not first_order_dominates(c, b) and not first_order_dominates(b, c)
    assert c.mean == pytest.approx(50.0) and b.mean == pytest.approx(40.0)
    wide, narrow = UniformLottery(20.0, 80.0), UniformLottery(40.0, 60.0)
    assert second_order_dominates(narrow, wide) and not second_order_dominates(wide, narrow)
    assert not first_order_dominates(narrow, wide)
    assert cdf_crossing(narrow, wide) == pytest.approx(50.0)
    assert stochastic_dominance_canvas(narrow, wide, "second") is not None
    assert stochastic_dominance_canvas(a, b, "first") is not None
    with pytest.raises(UncertaintyError):
        stochastic_dominance_canvas(a, b, "third")


def test_two_asset_frontier() -> None:
    from micro_viz import TwoAssetFrontier, mean_variance_frontier_canvas

    frontier = TwoAssetFrontier(8.0, 10.0, 14.0, 24.0, 0.2)
    sd, mean = frontier.minimum_variance()
    assert sd < min(10.0, 24.0)
    for step in range(-5, 16):
        assert frontier.portfolio(step / 10)[0] >= sd - 1e-9
    assert frontier.portfolio(1.0) == pytest.approx((10.0, 8.0))
    assert 8.0 < mean < 14.0
    assert mean_variance_frontier_canvas(frontier) is not None
    with pytest.raises(UncertaintyError):
        TwoAssetFrontier(8.0, 10.0, 14.0, 24.0, 1.0)


def test_state_claims_labels_find_free_places(tmp_path: Path) -> None:
    import warnings

    from mosaickit.errors import LayoutWarning

    from micro_viz import StateClaims, shared_theme, state_claims_canvas

    claims = StateClaims(100.0, 40.0, 0.5, 0.3)
    theme = shared_theme("manual")
    for rates in ((0.5,), (0.5, 0.6)):
        canvas = state_claims_canvas(claims, rates, theme=theme)
        with warnings.catch_warnings():
            warnings.simplefilter("error", LayoutWarning)
            canvas.save(tmp_path / f"claims{len(rates)}.svg")
