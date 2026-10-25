from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from micro_viz import (
    CobbDouglas,
    FixedProportions,
    IsoquantError,
    PerfectSubstitutes,
    cost_minimization_canvas,
    cost_minimizing_bundle,
    cost_of,
    expansion_path,
    expansion_path_canvas,
    fixed_capital_canvas,
    input_price_change_canvas,
    isocost_segment,
    technical_change_canvas,
)

ROOT = Path(__file__).parents[1]
BOUNDS = (14.0, 14.0)
TECH = CobbDouglas(0.5, 0.5)


def test_tangency_equates_mrts_to_the_price_ratio_and_hits_the_output() -> None:
    bundle = cost_minimizing_bundle(TECH, 6.0, 1.0, 2.0)
    assert TECH.output(bundle.labor, bundle.capital) == pytest.approx(6.0)
    assert TECH.mrts(bundle.labor, bundle.capital) == pytest.approx(1.0 / 2.0)
    assert bundle.cost == pytest.approx(cost_of(bundle.labor, bundle.capital, 1.0, 2.0))


def test_no_other_bundle_on_the_isoquant_is_cheaper() -> None:
    best = cost_minimizing_bundle(TECH, 6.0, 1.0, 2.0)
    for labor, capital in TECH.isoquant(6.0, BOUNDS):
        assert cost_of(labor, capital, 1.0, 2.0) >= best.cost - 1e-9


def test_dearer_labor_means_less_labor_more_capital() -> None:
    before = cost_minimizing_bundle(TECH, 6.0, 1.0, 1.0)
    after = cost_minimizing_bundle(TECH, 6.0, 2.0, 1.0)
    assert after.labor < before.labor and after.capital > before.capital


def test_corner_solutions_and_expansion_path_cost() -> None:
    assert cost_minimizing_bundle(PerfectSubstitutes(1.0, 1.0), 4.0, 1.0, 2.0).capital == 0.0
    corner = cost_minimizing_bundle(FixedProportions(1.0, 1.0), 4.0, 1.0, 1.0)
    assert (corner.labor, corner.capital) == (4.0, 4.0)
    path = expansion_path(TECH, (2.0, 4.0), 1.0, 1.0)
    assert path[1].cost == pytest.approx(2 * path[0].cost)  # constant returns: cost is linear
    with pytest.raises(IsoquantError):
        cost_minimizing_bundle(TECH, 6.0, 0.0, 1.0)
    with pytest.raises(IsoquantError):
        isocost_segment(1000.0, 1.0, 1.0, (1.0, 1.0))


def test_builders_and_example(tmp_path: Path) -> None:
    better = CobbDouglas(0.5, 0.5, 1.3)
    assert cost_minimization_canvas(TECH, 6.0, 1.0, 1.0, BOUNDS, title="T").spec.title == "T"
    assert input_price_change_canvas(TECH, 6.0, 1.0, 1.0, 2.0, BOUNDS, along=True)
    assert technical_change_canvas(TECH, better, 6.0, 1.0, 1.0, BOUNDS)
    assert expansion_path_canvas(TECH, (4.0, 6.0, 8.0), 1.0, 1.0, BOUNDS) is not None
    assert fixed_capital_canvas(TECH, (4.0, 6.0), 4.0, 1.0, 1.0, BOUNDS)
    config = tmp_path / "econ-viz.toml"
    config.write_text('base = "manual"\n', encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "scripts" / "cost_minimization.py"),
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
    assert "Own title" in (tmp_path / "out" / "cost_minimization.svg").read_text(encoding="utf-8")
