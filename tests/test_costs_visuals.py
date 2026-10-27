from __future__ import annotations

from pathlib import Path

import pytest
from mosaickit import AxisMarkLayer, Canvas, CanvasGrid, MarkerLayer, PathLayer

from micro_viz import (
    Config,
    CostAnalysis,
    CostSegment,
    CubicCost,
    PiecewiseCost,
    ShortRunProductionFunction,
    analyze_costs,
    cost_curves_grid,
    cost_curves_panels,
    piecewise_cost_canvas,
    product_cost_derivation_grid,
    shared_theme,
    total_cost_canvas,
    unit_cost_canvas,
    variable_cost_derivation_grid,
)


@pytest.fixture  # type: ignore[untyped-decorator]
def cubic() -> CostAnalysis:
    cost = CubicCost(fixed_cost=50.0, linear=36.0, quadratic=-8.0, cubic=0.6)
    return analyze_costs(cost, output_range=(1.0, 11.0), samples=81)


@pytest.fixture  # type: ignore[untyped-decorator]
def stepped() -> CostAnalysis:
    cost = PiecewiseCost((CostSegment(6.0, 11.4), CostSegment(9.0, 13.0)))
    return analyze_costs(cost, output_range=(0.0, 9.0), samples=61)


def _layers(canvas: Canvas) -> dict[str, object]:
    return {layer.id: layer for layer in canvas.snapshot().layers}


def test_total_cost_canvas_draws_the_three_totals_and_the_tangent_ray(
    cubic: CostAnalysis,
) -> None:
    layers = _layers(total_cost_canvas(cubic))
    for name in ("tc", "vc", "fc"):
        assert isinstance(layers[f"micro.cost.{name}"], PathLayer)
        assert layers[f"micro.cost.{name}.label"].text == name.upper()  # type: ignore[attr-defined]
    tc, vc, fc = (layers[f"micro.cost.{name}"] for name in ("tc", "vc", "fc"))
    assert isinstance(tc, PathLayer) and isinstance(vc, PathLayer) and isinstance(fc, PathLayer)
    assert tc.path[0][0] == 0.0  # totals start at the axis
    for (_, total), (_, variable), (_, fixed) in zip(tc.path, vc.path, fc.path, strict=True):
        assert total == pytest.approx(variable + fixed)
    extremum = cubic.minimum_average_total_cost
    assert extremum is not None
    ray = layers["micro.cost.guide.ray"]
    assert isinstance(ray, PathLayer)
    (x0, y0), (x1, y1) = ray.path
    assert (x0, y0) == (0.0, 0.0)
    assert y1 / x1 == pytest.approx(extremum.value)  # the slope of the ray is the minimum ATC
    assert isinstance(layers["micro.cost.mark.min_atc.output"], AxisMarkLayer)


def test_total_cost_canvas_without_fixed_cost_or_ray_or_marks() -> None:
    cost = CubicCost(fixed_cost=0.0, linear=36.0, quadratic=-8.0, cubic=0.6)
    analysis = analyze_costs(cost, output_range=(1.0, 11.0))
    layers = _layers(total_cost_canvas(analysis, ray=False))
    assert "micro.cost.fc" not in layers and "micro.cost.guide.ray" not in layers
    marked = _layers(
        total_cost_canvas(
            analyze_costs(
                CubicCost(fixed_cost=5.0, linear=36.0, quadratic=-8.0, cubic=0.6),
                output_range=(1.0, 11.0),
            ),
            marks=False,
        )
    )
    assert "micro.cost.mark.min_atc.output" not in marked
    assert "micro.cost.guide.ray" in marked


def test_unit_cost_canvas_marks_the_minima_where_mc_crosses(cubic: CostAnalysis) -> None:
    layers = _layers(unit_cost_canvas(cubic))
    for name in ("mc", "atc", "avc", "afc"):
        assert isinstance(layers[f"micro.cost.{name}"], PathLayer)
    for name, extremum in (
        ("min_avc", cubic.minimum_average_variable_cost),
        ("min_atc", cubic.minimum_average_total_cost),
    ):
        assert extremum is not None
        point = layers[f"micro.cost.point.{name}"]
        assert isinstance(point, MarkerLayer)
        assert point.points[0] == pytest.approx((extremum.output, extremum.value))
        assert cubic.cost.marginal_cost(extremum.output) == pytest.approx(extremum.value)
        for suffix in ("output", "cost"):
            assert isinstance(layers[f"micro.cost.guide.{name}.{suffix}"], PathLayer)
            assert isinstance(layers[f"micro.cost.mark.{name}.{suffix}"], AxisMarkLayer)


def test_unit_cost_canvas_curve_subset_and_unknown_names(cubic: CostAnalysis) -> None:
    layers = _layers(unit_cost_canvas(cubic, curves=("mc", "avc")))
    assert "micro.cost.atc" not in layers and "micro.cost.afc" not in layers
    assert "micro.cost.point.min_avc" in layers and "micro.cost.point.min_atc" not in layers
    with pytest.raises(ValueError, match="unknown curves"):
        unit_cost_canvas(cubic, curves=("mc", "tc"))


def test_unit_cost_canvas_output_marks_follow_the_output(cubic: CostAnalysis) -> None:
    low = _layers(unit_cost_canvas(cubic, output=3.0, x_max=12.0, y_range=(0.0, 100.0)))
    high = _layers(unit_cost_canvas(cubic, output=8.0, x_max=12.0, y_range=(0.0, 100.0)))
    for layers, q in ((low, 3.0), (high, 8.0)):
        dot = layers["micro.cost.point.output.mc"]
        assert isinstance(dot, MarkerLayer)
        assert dot.points[0] == pytest.approx((q, cubic.cost.marginal_cost(q)))
        assert isinstance(layers["micro.cost.guide.output"], PathLayer)


def test_grid_stacks_totals_over_unit_costs_with_a_link(cubic: CostAnalysis) -> None:
    grid = cost_curves_grid(cubic)
    assert isinstance(grid, CanvasGrid) and len(grid.placements) == 2
    upper, lower = (placement.canvas for placement in grid.placements)
    assert upper.spec.x_range == lower.spec.x_range
    (link,) = grid.links
    extremum = cubic.minimum_average_total_cost
    assert extremum is not None
    assert link.start == pytest.approx((extremum.output, cubic.cost.total_cost(extremum.output)))
    assert link.end == pytest.approx((extremum.output, extremum.value))
    assert "micro.cost.mark.min_atc.output" not in _layers(upper)


def test_variable_cost_derivation_uses_four_linked_panels() -> None:
    production = ShortRunProductionFunction(1.0, 2.0, -0.12)
    grid = variable_cost_derivation_grid(production, 4.0, (3.0, 5.0))
    assert (grid.rows, grid.cols, len(grid.placements)) == (2, 2, 4)
    assert len(grid.links) == 8
    ids = {
        layer.id for placement in grid.placements for layer in placement.canvas.snapshot().layers
    }
    assert {
        "micro.cost.derivation.labor_cost",
        "micro.cost.derivation.production",
        "micro.cost.derivation.output_cost",
        "micro.cost.derivation.diagonal",
    } <= ids


def test_product_cost_derivation_uses_four_linked_panels() -> None:
    production = ShortRunProductionFunction(1.0, 3.0, -0.3)
    grid = product_cost_derivation_grid(production, 4.0)
    assert (grid.rows, grid.cols, len(grid.placements)) == (2, 2, 4)
    assert len(grid.links) == 7
    ids = {
        layer.id for placement in grid.placements for layer in placement.canvas.snapshot().layers
    }
    assert {
        "micro.cost.product.mp",
        "micro.cost.product.ap",
        "micro.cost.product.tp",
        "micro.cost.product.smc",
        "micro.cost.product.avc",
        "micro.cost.product.diagonal",
    } <= ids


def test_piecewise_canvas_shows_steps_capacity_and_price_bands(stepped: CostAnalysis) -> None:
    layers = _layers(piecewise_cost_canvas(stepped, prices=(12.2, 14.0)))
    mc = layers["micro.cost.mc"]
    assert isinstance(mc, PathLayer)
    xs = [point[0] for point in mc.path]
    assert any(xs[index] == xs[index + 1] for index in range(len(xs) - 1))  # the vertical step
    assert isinstance(layers["micro.cost.avc"], PathLayer)
    capacity = layers["micro.cost.guide.capacity"]
    assert isinstance(capacity, PathLayer) and capacity.path[0][0] == 9.0
    first = layers["micro.cost.point.output.1"]
    second = layers["micro.cost.point.output.2"]
    assert isinstance(first, MarkerLayer) and isinstance(second, MarkerLayer)
    assert first.points[0] == (6.0, 12.2)  # between the steps: output stops at the jump
    assert second.points[0] == (9.0, 14.0)  # above the second step: full capacity
    assert "micro.cost.mark.output.1" in layers
    assert "micro.cost.mark.output.2" not in layers  # at capacity: the capacity mark is enough


def test_piecewise_canvas_price_below_the_first_step_has_no_output(stepped: CostAnalysis) -> None:
    layers = _layers(piecewise_cost_canvas(stepped, prices=(5.0,)))
    assert "micro.cost.point.output.1" not in layers
    assert "micro.cost.guide.price.1" in layers


def test_piecewise_canvas_needs_a_piecewise_cost(cubic: CostAnalysis) -> None:
    with pytest.raises(TypeError, match="PiecewiseCost"):
        piecewise_cost_canvas(cubic)


def test_piecewise_canvas_axis_starting_above_zero_is_broken(stepped: CostAnalysis) -> None:
    layers = _layers(piecewise_cost_canvas(stepped, y_range=(10.0, 15.0)))
    assert "axes.y.break.0" in layers and "axes.y.break.1" in layers
    assert "axes.origin.label" not in layers
    unbroken = _layers(piecewise_cost_canvas(stepped))
    assert "axes.y.break.0" not in unbroken and "axes.origin.label" in unbroken


def test_titles_texts_and_language_are_arguments(
    cubic: CostAnalysis, stepped: CostAnalysis
) -> None:
    builders = (total_cost_canvas, unit_cost_canvas)
    for builder in builders:
        assert builder(cubic).spec.title is None
        assert builder(cubic, title="Own title").spec.title == "Own title"
    assert piecewise_cost_canvas(stepped, title="Own").spec.title == "Own"
    canvas = unit_cost_canvas(cubic, labels={"cost.mc": "Marginal"}, x_label="Q", y_label="$")
    assert _layers(canvas)["micro.cost.mc.label"].text == "Marginal"  # type: ignore[attr-defined]
    assert (canvas.spec.x_label, canvas.spec.y_label) == ("Q", "$")
    theme = Config.from_dict({"base": "manual", "micro": {"language": "zh-TW"}}).theme
    assert theme.language == "zh-TW"
    assert unit_cost_canvas(cubic, theme=theme).spec.y_label == "C"


def test_output_symbol_comes_from_the_cost_model() -> None:
    cost = CubicCost(fixed_cost=5.0, linear=36.0, quadratic=-8.0, cubic=0.6, output_symbol="x")
    analysis = analyze_costs(cost, output_range=(1.0, 11.0))
    canvas = unit_cost_canvas(analysis)
    assert canvas.spec.x_label == "x"
    mark = _layers(canvas)["micro.cost.mark.min_atc.output"]
    assert mark.label == "x_2"  # type: ignore[attr-defined]


def test_output_follows_the_cost_function() -> None:
    first = analyze_costs(CubicCost(10.0, 36.0, -8.0, 0.6), output_range=(1.0, 11.0))
    second = analyze_costs(CubicCost(80.0, 30.0, -6.0, 0.5), output_range=(1.0, 11.0))
    one = _layers(unit_cost_canvas(first))["micro.cost.atc"]
    two = _layers(unit_cost_canvas(second))["micro.cost.atc"]
    assert one.path != two.path  # type: ignore[attr-defined]


def test_group_nudges_move_the_curve_names(cubic: CostAnalysis) -> None:
    theme = Config.from_dict({"micro": {"label": {"curve": {"top": "3pt"}}}}).theme
    moved = _layers(unit_cost_canvas(cubic, theme=theme))
    plain = _layers(unit_cost_canvas(cubic))
    assert plain["micro.cost.mc.label"].nudge is None  # type: ignore[attr-defined]
    assert moved["micro.cost.mc.label"].nudge.dy == pytest.approx(3.0)  # type: ignore[attr-defined]


def test_manual_theme_uses_the_shared_greys(cubic: CostAnalysis) -> None:
    theme = shared_theme("manual")
    canvas = unit_cost_canvas(cubic, theme=theme)
    colors = {}
    for name, role in (
        ("mc", "micro.curve.marginal"),
        ("atc", "micro.curve.average"),
        ("avc", "micro.curve.average.variable"),
    ):
        style = canvas.theme.resolve(role, fallback_category="path")
        assert style.stroke is not None and style.stroke.color is not None
        colors[name] = style.stroke.color.to_hex().lower()
    assert colors == {"mc": "#1a1a1a", "atc": "#8c8c8c", "avc": "#6e6e6e"}


def test_all_cost_figures_render_to_svg(
    cubic: CostAnalysis, stepped: CostAnalysis, tmp_path: Path
) -> None:
    figures = {
        "total": total_cost_canvas(cubic),
        "unit": unit_cost_canvas(cubic),
        "grid": cost_curves_grid(cubic),
        "step": piecewise_cost_canvas(stepped, prices=(12.2,)),
    }
    for name, figure in figures.items():
        target = tmp_path / f"{name}.svg"
        figure.save(target)
        assert target.stat().st_size > 0
    assert "micro.cost" in (tmp_path / "total.svg").read_text(encoding="utf-8")


def test_panels_stand_alone_with_the_grid_axes(cubic: CostAnalysis) -> None:
    upper, lower = cost_curves_panels(cubic)
    grid_upper, grid_lower = (p.canvas for p in cost_curves_grid(cubic).placements)
    assert upper.spec.x_range == grid_upper.spec.x_range
    assert lower.spec.y_range == grid_lower.spec.y_range
    assert "micro.cost.mark.min_atc.output" not in _layers(upper)


def test_avc_is_named_at_its_right_end(cubic: CostAnalysis) -> None:
    layers = _layers(unit_cost_canvas(cubic))
    label = layers["micro.cost.avc.label"]
    assert getattr(label, "at", 1.0) == 1.0
