from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from micro_viz import (
    LearningAverageCost,
    LearningCurve,
    ProductionError,
    ProductionFrontier,
    ProductTransformation,
    ShortRunProductionFunction,
    TechnologyShift,
    learning_curve_canvas,
    product_transformation_canvas,
    production_frontier_canvas,
    scale_vs_learning_canvas,
    technology_shift_canvas,
)

ROOT = Path(__file__).parents[1]
PRODUCTION = ShortRunProductionFunction(2.0, 1.0, -0.06)


def test_learning_curve_falls_toward_floor() -> None:
    curve = LearningCurve(2.0, 10.0, 0.45)
    values = [curve.input_per_unit(n) for n in (1, 5, 20, 100)]
    assert values == sorted(values, reverse=True)
    assert all(value > 2.0 for value in values)
    assert curve.input_per_unit(1.0) == pytest.approx(12.0)
    assert curve.learning_index(1.0) == pytest.approx(1.0)
    with pytest.raises(ProductionError):
        curve.input_per_unit(0.0)


def test_learning_shifts_average_cost_down_at_every_output() -> None:
    cost = LearningAverageCost(10.0, 20.0, 0.02)
    for output in (5.0, 20.0, 35.0):
        assert cost.cost(output, 0.3) < cost.cost(output)
    assert cost.cost(20.0) == pytest.approx(10.0)
    with pytest.raises(ProductionError):
        cost.cost(10.0, 1.0)


def test_outward_bow_means_economies_of_scope() -> None:
    bowed = ProductTransformation(100.0, 100.0, 2.0)
    straight = ProductTransformation(100.0, 100.0, 1.0)
    inward = ProductTransformation(100.0, 100.0, 0.5)
    assert bowed.economies_of_scope and not straight.economies_of_scope
    assert bowed.output_2(50.0) > straight.output_2(50.0) > inward.output_2(50.0)
    assert straight.output_2(50.0) == pytest.approx(50.0)
    assert bowed.output_2(0.0) == pytest.approx(100.0)
    assert bowed.output_2(100.0) == pytest.approx(0.0)
    assert bowed.scope_degree(30.0, 30.0) > 0
    assert straight.scope_degree(30.0, 30.0) == pytest.approx(0.0)


def test_technology_shift_raises_total_product() -> None:
    shift = TechnologyShift(PRODUCTION, (1.0, 1.3, 1.6))
    for inputs in (2.0, 6.0, 10.0):
        assert (
            shift.total_product(0, inputs)
            < shift.total_product(1, inputs)
            < shift.total_product(2, inputs)
        )
    with pytest.raises(ProductionError):
        TechnologyShift(PRODUCTION, (1.3, 1.6))
    with pytest.raises(ProductionError):
        TechnologyShift(PRODUCTION, (1.0, 1.0))


def test_frontier_interior_points_are_below() -> None:
    frontier = ProductionFrontier(10.0, 0.5, ((3.0, 0.7), (8.0, 0.6)))
    for labor, output in frontier.points():
        assert output < frontier.output(labor)
        assert not frontier.efficient(labor, output)
    assert frontier.efficient(4.0, frontier.output(4.0))
    with pytest.raises(ProductionError):
        ProductionFrontier(10.0, 1.5)
    with pytest.raises(ProductionError):
        ProductionFrontier(10.0, 0.5, ((3.0, 1.2),))


def test_canvases_follow_parameters() -> None:
    assert learning_curve_canvas(LearningCurve(2.0, 10.0, 0.45), 50.0, title="T").spec.title == "T"
    cost = LearningAverageCost(10.0, 20.0, 0.02)
    assert scale_vs_learning_canvas(cost, 0.3, 10.0, 26.0) is not None
    plain = product_transformation_canvas(ProductTransformation(100.0, 100.0, 2.0), reference=False)
    full = product_transformation_canvas(ProductTransformation(100.0, 100.0, 2.0))
    assert len(full.snapshot().layers) > len(plain.snapshot().layers)
    assert technology_shift_canvas(TechnologyShift(PRODUCTION, (1.0, 1.3)), 12.0, 6.0) is not None
    frontier = ProductionFrontier(10.0, 0.5, ((3.0, 0.7),))
    assert production_frontier_canvas(frontier, 12.0, ("B",)) is not None


def test_example_runs(tmp_path: Path) -> None:
    config = tmp_path / "econ-viz.toml"
    config.write_text('base = "manual"\n', encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "scripts" / "production_extensions.py"),
            "--output-dir",
            str(tmp_path / "out"),
            "--config",
            str(config),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    assert (tmp_path / "out" / "production_frontier.svg").exists()
