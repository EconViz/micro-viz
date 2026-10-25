from __future__ import annotations

from pathlib import Path

import pytest
from mosaickit import Canvas

from micro_viz import (
    ShortRunProductionFunction,
    analyze_production,
    average_marginal_product_canvas,
    shared_theme,
    total_product_canvas,
)

pytest.importorskip("kinetickit")

from micro_viz.animation import Stage, animation_from_canvases, canvases_for, save_gif, save_svg  # noqa: E402

LINEAR_VALUES = (4.0, 6.0, 8.0)


def _frame(linear: float) -> Canvas:
    function = ShortRunProductionFunction(linear=linear, quadratic=3.0, cubic=-0.5)
    analysis = analyze_production(function, input_range=(0.0, 6.0), samples=41)
    return average_marginal_product_canvas(
        analysis, theme=shared_theme("manual"), y_range=(-25.0, 25.0), x_max=6.6
    )


def test_every_value_is_drawn_by_the_figures_own_builder() -> None:
    canvases = canvases_for(_frame, LINEAR_VALUES)
    assert len(canvases) == len(LINEAR_VALUES)
    ids = [{layer.id for layer in canvas.snapshot().layers} for canvas in canvases]
    assert ids[0] == ids[1] == ids[2]
    paths = [
        next(layer for layer in canvas.snapshot().layers if layer.id == "micro.production.mp").path
        for canvas in canvases
    ]
    assert paths[0] != paths[2]


def test_axes_that_change_between_values_are_rejected() -> None:
    def moving(value: float) -> Canvas:
        function = ShortRunProductionFunction(linear=value, quadratic=3.0, cubic=-0.5)
        return total_product_canvas(analyze_production(function, input_range=(0.0, 6.0)))

    with pytest.raises(ValueError, match="axis ranges"):
        canvases_for(moving, LINEAR_VALUES)
    with pytest.raises(ValueError, match="must not be empty"):
        canvases_for(_frame, [])


def test_the_animation_runs_one_step_between_consecutive_values() -> None:
    stage = Stage(seconds_per_step=2.0)
    animation, _ = animation_from_canvases(canvases_for(_frame, LINEAR_VALUES), stage=stage)
    assert animation.duration == pytest.approx(4.0)
    first = animation.sample(0.0).get("micro.production.mp").path.vertices()
    last = animation.sample(4.0).get("micro.production.mp").path.vertices()
    assert first != last


def test_animated_svg_keeps_layer_ids_and_animates(tmp_path: Path) -> None:
    target = save_svg(_frame, LINEAR_VALUES, tmp_path / "products.svg")
    svg = target.read_text(encoding="utf-8")
    for layer_id in (
        "micro.production.ap",
        "micro.production.mp",
        "micro.production.point.average_max",
        "micro.production.region.negative",
        "micro.production.mp.label",
    ):
        assert f'data-kk-id="{layer_id}' in svg
    assert "<animate" in svg
    assert "<image" not in svg


def test_gif_has_a_frame_per_interpolated_value(tmp_path: Path) -> None:
    from PIL import Image

    target = save_gif(_frame, (4.0, 8.0), tmp_path / "products.gif", frames_per_step=3, dpi=40)
    with Image.open(target) as image:
        assert image.n_frames == 4


def _mixed_canvas(title: str | None = None) -> Canvas:
    from mosaickit import (
        AxisMarkLayer,
        BraceLayer,
        CanvasSpec,
        FillLayer,
        GroupLayer,
        LegendLayer,
        MarkerLayer,
        PathLayer,
        PointLabelLayer,
        RegionLabelLayer,
        TextLayer,
    )

    spec = CanvasSpec(x_range=(0.0, 10.0), y_range=(0.0, 10.0), title=title)
    theme = shared_theme("manual")
    canvas = Canvas(spec, theme=theme.to_mosaickit(), config=theme.mosaickit_config())
    canvas.extend(
        (
            FillLayer(((1, 1), (4, 1), (4, 4), (1, 4)), id="region", role="micro.region.mid"),
            RegionLabelLayer("region", "Region", short_text="R", id="region.label"),
            PathLayer(((0, 0), (10, 10)), id="line", role="micro.curve.total"),
            PointLabelLayer((10, 10), "End", id="line.label", role="micro.curve.total"),
            PointLabelLayer((5, 5), "Here", id="here", role="micro.point"),
            MarkerLayer(((5, 5),), id="dot", role="micro.point"),
            TextLayer((2, 8), "Text", id="text", role="micro.annotation", anchor="left"),
            TextLayer((8, 2), "x_1", id="math", role="axes", math=True),
            AxisMarkLayer("x", 3.0, "L_1", math=True, id="mark.x"),
            AxisMarkLayer("y", 3.0, "p_1", math=True, id="mark.y"),
            BraceLayer("x", 1.0, 4.0, "Span", side="outside", id="brace"),
            BraceLayer("y", 1.0, 4.0, "Rise", id="brace.y"),
            GroupLayer((PathLayer(((0, 5), (10, 5)), id="grouped"),), id="group"),
            LegendLayer(id="legend"),
        )
    )
    return canvas


def test_every_layer_kind_has_a_depiction_or_is_reported_once() -> None:
    from micro_viz.animation.depict import Depictor

    canvas = _mixed_canvas(title="Title")
    depictor = Depictor(canvas, Stage())
    nodes = [node for layer in depictor.layers() for node in depictor.depict(layer)]
    ids = {node.id for node in nodes}
    assert {"region", "line", "line.label", "dot.0", "text", "mark.x", "brace", "grouped"} <= ids
    assert {"region.label", "here", "math", "mark.y", "brace.label"} <= ids
    assert depictor.skipped == ["brace.y (BraceLayer on the y axis)", "legend (LegendLayer)"]
    assert "line.arrow.end" not in ids


def test_title_becomes_a_text_node_in_the_animation() -> None:
    animation, _ = animation_from_canvases([_mixed_canvas("Title"), _mixed_canvas("Title")])
    assert animation.sample(0.0).get("micro.title") is not None


def test_math_letters_are_set_in_the_math_italic_alphabet() -> None:
    from micro_viz.animation.depict import ITALIC_CAPITAL_A, ITALIC_SMALL_A, _italic_letters

    coverage = frozenset({ITALIC_CAPITAL_A + 11, ITALIC_SMALL_A + 15})
    assert (
        _italic_letters("L_p", coverage)
        == f"{chr(ITALIC_CAPITAL_A + 11)}_{chr(ITALIC_SMALL_A + 15)}"
    )
    assert _italic_letters(r"\alpha_q", coverage) == r"\alpha_q"
    assert _italic_letters("L", frozenset()) == "L"


def test_animation_uses_the_configured_fonts_when_present() -> None:
    from micro_viz import Config
    from micro_viz.animation.depict import Typography

    theme = Config.from_dict({"base": "manual"}).theme
    canvas = Canvas(config=theme.mosaickit_config())
    asset = Typography(canvas).asset("Word", "serif", 11.0, 400, False)
    assert asset.width > 0
    math_asset = Typography(canvas).asset("L_1", "serif", 11.0, 400, True)
    assert math_asset.width > 0


def test_layers_missing_from_some_frames_fade_in_instead_of_failing() -> None:
    from micro_viz import CostSegment, PiecewiseCost, analyze_costs, piecewise_cost_canvas

    analysis = analyze_costs(
        PiecewiseCost((CostSegment(6.0, 11.4), CostSegment(9.0, 13.0))), output_range=(0.0, 9.0)
    )

    def frame(price: float) -> Canvas:
        return piecewise_cost_canvas(
            analysis, prices=(price,), x_max=10.0, y_range=(0.0, 16.0), theme=shared_theme("manual")
        )

    # a price below the first step has no output point; the higher prices do
    canvases = canvases_for(frame, (5.0, 12.0, 14.0))
    ids = [{layer.id for layer in canvas.snapshot().layers} for canvas in canvases]
    assert "micro.cost.point.output.1" not in ids[0] and "micro.cost.point.output.1" in ids[1]
    animation, _ = animation_from_canvases(canvases)
    dot = "micro.cost.point.output.1.0"
    assert animation.sample(0.0).get(dot).opacity == 0.0
    assert animation.sample(animation.duration).get(dot).opacity == 1.0
