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
    Returns,
    isoquant_map_canvas,
    mrts_steps_canvas,
    returns_to_scale_grid,
)

ROOT = Path(__file__).parents[1]
BOUNDS = (12.0, 12.0)


def test_cobb_douglas_isoquant_holds_output_and_mrts_falls() -> None:
    tech = CobbDouglas(0.5, 0.5)
    points = tech.isoquant(6.0, BOUNDS)
    assert all(tech.output(x, y) == pytest.approx(6.0) for x, y in points)
    slopes = [tech.mrts(x, y) for x, y in points]
    assert all(a > b for a, b in zip(slopes, slopes[1:], strict=False))  # type: ignore[operator]


def test_mrts_is_the_marginal_product_ratio() -> None:
    tech = CobbDouglas(0.4, 0.6, scale=2.0)
    labor, capital, eps = 3.0, 5.0, 1e-6
    mp_l = (tech.output(labor + eps, capital) - tech.output(labor, capital)) / eps
    mp_k = (tech.output(labor, capital + eps) - tech.output(labor, capital)) / eps
    assert tech.mrts(labor, capital) == pytest.approx(mp_l / mp_k, rel=1e-4)


def test_substitutes_have_constant_mrts_and_complements_kink_on_a_ray() -> None:
    substitutes = PerfectSubstitutes(2.0, 1.0)
    assert substitutes.mrts(1.0, 1.0) == substitutes.mrts(5.0, 2.0) == 2.0
    complements = FixedProportions(1.0, 2.0)
    labor, capital = complements.corner(4.0)
    assert capital == pytest.approx(complements.ray_slope * labor)
    assert complements.output(labor, capital) == pytest.approx(4.0)
    assert complements.mrts(labor, capital) is None


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    ("shares", "expected"),
    [
        ((0.4, 0.4), Returns.DECREASING),
        ((0.5, 0.5), Returns.CONSTANT),
        ((0.7, 0.6), Returns.INCREASING),
    ],
)
def test_returns_to_scale_follow_the_exponents(
    shares: tuple[float, float], expected: Returns
) -> None:
    assert CobbDouglas(*shares).returns_to_scale() is expected


def test_isoquants_along_a_ray_are_closer_under_increasing_returns() -> None:
    constant, increasing = CobbDouglas(0.5, 0.5), CobbDouglas(0.65, 0.65)
    gaps = []
    for tech in (constant, increasing):
        first, second = (tech.scale_for(q, 1.0, 1.0) for q in (2.0, 4.0))
        gaps.append(second - first)
    assert gaps[1] < gaps[0]


def test_invalid_technology_is_rejected() -> None:
    with pytest.raises(IsoquantError):
        CobbDouglas(0.0, 0.5)


def test_builders_follow_inputs() -> None:
    tech = CobbDouglas()
    canvas = isoquant_map_canvas(tech, (4.0, 6.0), BOUNDS, title="T")
    assert canvas.spec.title == "T"
    ids = {layer.id for layer in canvas.snapshot().layers}
    assert {"micro.isoquant.q.1", "micro.isoquant.q.2"} <= ids
    steps = mrts_steps_canvas(tech, 6.0, (2.0, 4.0, 8.0), BOUNDS)
    assert "micro.isoquant.chord.2" in {layer.id for layer in steps.snapshot().layers}
    with pytest.raises(ValueError):
        mrts_steps_canvas(PerfectSubstitutes(), 6.0, (9.0,), BOUNDS)
    assert returns_to_scale_grid((tech, tech), ((2.0, 4.0), (2.0, 4.0)), BOUNDS, (1.0, 1.0))


def test_example_writes_figures(tmp_path: Path) -> None:
    config = tmp_path / "econ-viz.toml"
    config.write_text('base = "manual"\n', encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "scripts" / "isoquants.py"),
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
    assert "Own title" in (tmp_path / "out" / "isoquant_map.svg").read_text(encoding="utf-8")
