from __future__ import annotations

import re
import warnings
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest
from mosaickit import (
    Canvas,
    FillLayer,
    MarkerLayer,
    PathLayer,
    SpanBraceLayer,
    TextLayer,
)

from micro_viz import (
    Config,
    ProductionAnalysis,
    ShortRunProductionFunction,
    analyze_production,
    average_marginal_product_canvas,
    production_grid,
    shared_theme,
    total_product_canvas,
)


@pytest.fixture  # type: ignore[untyped-decorator]
def analysis() -> ProductionAnalysis:
    function = ShortRunProductionFunction(linear=6.0, quadratic=3.0, cubic=-0.5)
    return analyze_production(function, input_range=(0.0, 6.0), samples=61)


def _layers(canvas: Canvas) -> dict[str, object]:
    return {layer.id: layer for layer in canvas.snapshot().layers}


def _stroke_color(canvas: Canvas, layer: PathLayer) -> str:
    style = canvas.theme.resolve(layer.role, fallback_category=layer.fallback_category)
    assert style.stroke is not None and style.stroke.color is not None
    return cast(str, style.stroke.color.to_hex()).lower()


def test_total_product_canvas_has_curve_regions_guides_and_names(
    analysis: ProductionAnalysis,
) -> None:
    layers = _layers(total_product_canvas(analysis))

    assert isinstance(layers["micro.production.tp"], PathLayer)
    assert layers["micro.production.tp.label"].text == "TP"  # type: ignore[attr-defined]
    for name in ("increasing", "diminishing", "negative"):
        fill = layers[f"micro.production.region.{name}"]
        brace = layers[f"micro.production.region.{name}.brace"]
        assert isinstance(fill, FillLayer)
        assert fill.role.startswith("micro.region.")
        assert isinstance(brace, SpanBraceLayer) and brace.label
    for name in ("inflection", "average_max", "total_max"):
        assert isinstance(layers[f"micro.production.guide.{name}"], PathLayer)
        assert isinstance(layers[f"micro.production.point.{name}"], MarkerLayer)
        assert isinstance(layers[f"micro.production.mark.{name}"], TextLayer)


def test_guides_sit_on_the_exact_boundary_inputs(analysis: ProductionAnalysis) -> None:
    layers = _layers(total_product_canvas(analysis))
    for name, expected in (
        ("inflection", analysis.inflection_input),
        ("average_max", analysis.average_product_max_input),
        ("total_max", analysis.total_product_max_input),
    ):
        guide = layers[f"micro.production.guide.{name}"]
        assert isinstance(guide, PathLayer)
        assert all(point[0] == pytest.approx(expected) for point in guide.path)


def test_average_marginal_canvas_marks_ap_equals_mp_and_mp_zero(
    analysis: ProductionAnalysis,
) -> None:
    function = analysis.production_function
    layers = _layers(average_marginal_product_canvas(analysis))

    ap, mp = layers["micro.production.ap"], layers["micro.production.mp"]
    assert isinstance(ap, PathLayer) and isinstance(mp, PathLayer)
    assert ap.role == "micro.curve.average" and mp.role == "micro.curve.marginal"
    meet = layers["micro.production.point.average_max"]
    zero = layers["micro.production.point.total_max"]
    assert isinstance(meet, MarkerLayer) and isinstance(zero, MarkerLayer)
    x, y = meet.points[0]
    assert y == pytest.approx(function.marginal_product(x))
    assert y == pytest.approx(function.average_product(x))
    assert zero.points[0][1] == 0.0
    assert function.marginal_product(zero.points[0][0]) == pytest.approx(0.0, abs=1e-9)
    assert isinstance(layers["micro.production.annotation.ap_equals_mp"], object)
    assert isinstance(layers["micro.production.annotation.mp_zero"], TextLayer)


def test_titles_default_to_none_and_follow_the_argument(analysis: ProductionAnalysis) -> None:
    for builder in (total_product_canvas, average_marginal_product_canvas):
        assert builder(analysis).spec.title is None
        assert builder(analysis, title="Own title").spec.title == "Own title"


def test_axis_names_ranges_and_texts_are_arguments(analysis: ProductionAnalysis) -> None:
    canvas = total_product_canvas(
        analysis,
        x_label="K",
        y_label="Y",
        x_max=9.0,
        y_range=(0.0, 100.0),
        labels={"production.tp": "Output"},
        size=(4.0, 3.0),
        dpi=72,
    )
    assert (canvas.spec.x_label, canvas.spec.y_label) == ("K", "Y")
    assert canvas.spec.x_range == (0.0, 9.0)
    # the given range is the data range; the canvas adds the strip under the regions
    assert canvas.spec.y_range[1] == 100.0 and canvas.spec.y_range[0] < 0.0
    assert (canvas.spec.width, canvas.spec.height, canvas.spec.dpi) == (4.0, 3.0, 72)
    assert _layers(canvas)["micro.production.tp.label"].text == "Output"  # type: ignore[attr-defined]


def test_output_follows_the_production_function() -> None:
    first = analyze_production(ShortRunProductionFunction(6, 3, -0.5), input_range=(0, 6))
    second = analyze_production(ShortRunProductionFunction(2, 4, -0.4), input_range=(0, 8))
    one = total_product_canvas(first).snapshot().layers
    two = total_product_canvas(second).snapshot().layers
    assert one != two
    tp_one = next(layer for layer in one if layer.id == "micro.production.tp")
    tp_two = next(layer for layer in two if layer.id == "micro.production.tp")
    assert tp_one.path != tp_two.path


def test_no_regions_or_guides_removes_those_layers(analysis: ProductionAnalysis) -> None:
    layers = _layers(total_product_canvas(analysis, regions=False, guides=False))
    assert not [name for name in layers if ".region." in name or ".guide." in name]


def test_language_changes_every_built_in_text(analysis: ProductionAnalysis) -> None:
    theme = Config.from_dict({"base": "manual", "micro": {"language": "zh-TW"}}).theme
    layers = _layers(average_marginal_product_canvas(analysis, theme=theme))
    brace = layers["micro.production.region.increasing.brace"]
    assert isinstance(brace, SpanBraceLayer) and brace.label == "報酬遞增"
    assert average_marginal_product_canvas(analysis, theme=theme).spec.y_label == "產量"


def test_group_nudges_move_curve_names(analysis: ProductionAnalysis) -> None:
    plain = _layers(total_product_canvas(analysis))["micro.production.tp.label"]
    theme = Config.from_dict({"micro": {"label": {"curve": {"top": "5pt"}}}}).theme
    moved = _layers(total_product_canvas(analysis, theme=theme))["micro.production.tp.label"]
    assert plain.nudge is None  # type: ignore[attr-defined]
    assert moved.nudge.dy == pytest.approx(5.0)  # type: ignore[attr-defined]


def test_default_visuals_are_coloured_on_white(analysis: ProductionAnalysis) -> None:
    total = total_product_canvas(analysis)
    products = average_marginal_product_canvas(analysis)
    canvas_style = total.theme.resolve("canvas", fallback_category="fill")
    assert canvas_style.fill is not None and canvas_style.fill.color is not None
    assert canvas_style.fill.color.to_hex().lower() == "#ffffff"
    assert _stroke_color(total, _layers(total)["micro.production.tp"]) == "#4daf4a"
    assert _stroke_color(products, _layers(products)["micro.production.ap"]) == "#377eb8"
    assert _stroke_color(products, _layers(products)["micro.production.mp"]) == "#e41a1c"


def test_manual_visuals_are_black_and_white(analysis: ProductionAnalysis) -> None:
    theme = shared_theme("manual")
    products = average_marginal_product_canvas(analysis, theme=theme)
    layers = _layers(products)
    assert _stroke_color(products, layers["micro.production.ap"]) == "#8c8c8c"
    assert _stroke_color(products, layers["micro.production.mp"]) == "#1a1a1a"
    for name in ("light", "mid", "dark"):
        style = products.theme.resolve(f"micro.region.{name}", fallback_category="region")
        assert style.fill is not None and style.fill.opacity == theme.region_opacity


def test_both_production_canvases_render_to_svg(
    analysis: ProductionAnalysis, tmp_path: Path
) -> None:
    for name, canvas in (
        ("total-product", total_product_canvas(analysis)),
        ("average-marginal", average_marginal_product_canvas(analysis)),
    ):
        output = tmp_path / f"{name}.svg"
        canvas.save(output)
        assert output.stat().st_size > 0
        assert "micro.production" in output.read_text(encoding="utf-8")


def test_production_grid_aligns_the_three_corresponding_inputs(
    analysis: ProductionAnalysis, tmp_path: Path
) -> None:
    grid = production_grid(analysis, theme=shared_theme("manual"))

    assert (grid.rows, grid.cols) == (2, 1)
    assert len(grid.links) == 3
    upper_layers = _layers(grid.placements[0].canvas)
    lower_layers = _layers(grid.placements[1].canvas)
    assert not [layer_id for layer_id in upper_layers if ".mark." in layer_id]
    assert all(
        f"micro.production.mark.{name}" in lower_layers
        for name in ("inflection", "average_max", "total_max")
    )
    expected = (
        analysis.inflection_input,
        analysis.average_product_max_input,
        analysis.total_product_max_input,
    )
    for link, variable_input in zip(grid.links, expected, strict=True):
        assert link.start_cell == 0 and link.end_cell == 1
        assert link.start[0] == pytest.approx(variable_input)
        assert link.end[0] == pytest.approx(variable_input)

    output = tmp_path / "production-panels.svg"
    grid.save(output)
    svg = output.read_text(encoding="utf-8")
    assert "micro.production.tp" in svg
    assert "micro.production.ap" in svg
    assert "micro.production.mp" in svg


def _first_numbers(svg: str, element_id: str) -> list[tuple[float, float]]:
    start = svg.index(f'id="{element_id}"')
    path = re.search(r' d="([^"]+)"', svg[start:])
    assert path is not None
    return [(float(x), float(y)) for x, y in re.findall(r"(-?[\d.]+) (-?[\d.]+)", path.group(1))]


@pytest.mark.parametrize("gap", [4.0, 9.0, 0.0])  # type: ignore[untyped-decorator]
@pytest.mark.parametrize("figure", ["total", "products"])  # type: ignore[untyped-decorator]
def test_braces_hug_their_regions_by_the_theme_gap(
    analysis: ProductionAnalysis, tmp_path: Path, gap: float, figure: str
) -> None:
    theme = replace(shared_theme("manual"), brace_gap=gap)
    builder = total_product_canvas if figure == "total" else average_marginal_product_canvas
    target = tmp_path / "figure.svg"
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # no label may be left without a free place
        builder(analysis, theme=theme).save(target)
    svg = target.read_text(encoding="utf-8")
    for kind in ("increasing", "diminishing", "negative"):
        region = _first_numbers(svg, f"micro.production.region.{kind}")
        brace = _first_numbers(svg, f"micro.production.region.{kind}.brace")
        bottom = max(y for _, y in region)
        assert min(y for _, y in brace) - bottom == pytest.approx(gap, abs=0.01)
        assert min(x for x, _ in brace) == pytest.approx(min(x for x, _ in region), abs=0.01)
        assert max(x for x, _ in brace) == pytest.approx(max(x for x, _ in region), abs=0.01)


def test_brace_gap_is_a_setting_not_a_literal() -> None:
    theme = Config.from_dict({"micro": {"brace": {"gap": 7}}}).theme
    assert theme.brace_gap == 7
    with pytest.raises(ValueError):
        Config.from_dict({"micro": {"brace": {"gap": -1}}})


def test_region_fill_is_optional_per_theme(analysis: ProductionAnalysis) -> None:
    base = shared_theme("manual")
    shaded = _layers(total_product_canvas(analysis, theme=base))
    bare = _layers(total_product_canvas(analysis, theme=replace(base, region_fill=False)))
    assert any(".region." in key and not key.endswith("brace") for key in shaded)
    assert not [key for key, layer in bare.items() if isinstance(layer, FillLayer)]
    assert [key for key in bare if key.endswith(".brace")]


def test_region_shade_can_stop_at_the_curve(analysis: ProductionAnalysis) -> None:
    base = shared_theme("manual")
    top = _layers(total_product_canvas(analysis, theme=base))
    under = _layers(total_product_canvas(analysis, theme=replace(base, region_extent="curve")))
    key = "micro.production.region.increasing"
    assert isinstance(top[key], FillLayer) and isinstance(under[key], FillLayer)
    height = max(y for _, y in top[key].boundary)  # type: ignore[attr-defined]
    assert max(y for _, y in under[key].boundary) < height  # type: ignore[attr-defined]


def test_each_region_takes_its_own_colour(analysis: ProductionAnalysis) -> None:
    layers = _layers(
        total_product_canvas(
            analysis,
            theme=shared_theme("manual"),
            region_colors={"increasing": "#336699", "negative": "#993333"},
        )
    )
    fills = {
        kind: layers[f"micro.production.region.{kind}"].fill  # type: ignore[attr-defined]
        for kind in ("increasing", "diminishing", "negative")
    }
    assert fills["increasing"] is not None and fills["negative"] is not None
    assert fills["diminishing"] is None
    assert fills["increasing"] != fills["negative"]


def test_region_extent_is_validated() -> None:
    with pytest.raises(ValueError, match="region_extent"):
        replace(shared_theme("manual"), region_extent="side")
