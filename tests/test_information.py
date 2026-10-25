from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from micro_viz import (
    BonusSchedule,
    EfficiencyWage,
    InformationError,
    LemonsMarket,
    LinearDemand,
    MoralHazard,
    Signaling,
    bonus_schedule_canvas,
    efficiency_wage_canvas,
    lemons_market_canvas,
    moral_hazard_canvas,
    signaling_canvas,
)

ROOT = Path(__file__).parents[1]
LEMONS = LemonsMarket(LinearDemand(40.0, 1.0), LinearDemand(20.0, 1.0), 24.0, 6.0, 0.5)
SIGNAL = Signaling(20.0, 2.0, 1.0)
HAZARD = MoralHazard(LinearDemand(30.0, 1.0), 12.0, 0.6)
BONUS = BonusSchedule(0.5, 0.1, 1.2)
EFFICIENCY = EfficiencyWage(40.0, 1.0, 4.0, 0.5, 10.0, 0.9)


def test_mixed_demand_is_the_share_weighted_average() -> None:
    mixed = LEMONS.mixed_demand(0.25)
    assert mixed.intercept == pytest.approx(0.25 * 40.0 + 0.75 * 20.0)
    assert LEMONS.mixed_demand(1.0).intercept == pytest.approx(40.0)


def test_low_share_drives_high_quality_out() -> None:
    assert LEMONS.high_quality_sells(0.8)
    assert not LEMONS.high_quality_sells(0.1)
    share = LEMONS.critical_share
    assert LEMONS.mixed_demand(share).intercept == pytest.approx(24.0)


def test_separating_signal_lies_between_the_ceilings() -> None:
    assert SIGNAL.low_ceiling == pytest.approx(10.0)
    assert SIGNAL.high_ceiling == pytest.approx(20.0)
    assert SIGNAL.separating(SIGNAL.separating_signal)
    assert not SIGNAL.separating(5.0)
    assert not SIGNAL.separating(25.0)


def test_insurance_causes_overuse() -> None:
    outcome = HAZARD.solve()
    assert outcome.insured_quantity > outcome.efficient_quantity
    assert outcome.efficient_quantity == pytest.approx(18.0)
    assert outcome.insured_quantity == pytest.approx(25.2)
    assert outcome.deadweight_loss == pytest.approx(0.5 * 7.2 * 7.2)


def test_truthful_report_maximises_the_bonus() -> None:
    for actual in (30.0, 60.0):
        best = BONUS.bonus(BONUS.best_report(actual), actual)
        for report in (0.0, 0.5 * actual, 0.9 * actual, 1.1 * actual, 2 * actual):
            assert BONUS.bonus(report, actual) <= best + 1e-9


def test_no_shirking_wage_creates_unemployment() -> None:
    out = EFFICIENCY.solve()
    assert out.wage > out.competitive_wage
    assert out.employment < out.competitive_employment
    assert out.unemployment > 0
    assert out.wage == pytest.approx(10.0 + 0.9 * out.employment)


def test_invalid_inputs() -> None:
    with pytest.raises(InformationError):
        LemonsMarket(LinearDemand(20.0, 1.0), LinearDemand(40.0, 1.0), 24.0, 6.0, 0.5)
    with pytest.raises(InformationError):
        Signaling(20.0, 1.0, 2.0)
    with pytest.raises(InformationError):
        MoralHazard(LinearDemand(30.0, 1.0), 12.0, 1.0)
    with pytest.raises(InformationError):
        BonusSchedule(0.5, 0.6, 1.2)


def test_canvases_follow_parameters() -> None:
    assert lemons_market_canvas(LEMONS, (0.8, 0.3)) is not None
    assert signaling_canvas(SIGNAL, 15.0) is not None
    assert moral_hazard_canvas(HAZARD, title="T").spec.title == "T"
    assert bonus_schedule_canvas(BONUS, (30.0, 60.0), 100.0) is not None
    assert efficiency_wage_canvas(EFFICIENCY) is not None


def test_example_runs(tmp_path: Path) -> None:
    config = tmp_path / "econ-viz.toml"
    config.write_text('base = "manual"\n', encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "scripts" / "information.py"),
            "--output-dir",
            str(tmp_path / "out"),
            "--config",
            str(config),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    assert (tmp_path / "out" / "efficiency_wage.svg").exists()
