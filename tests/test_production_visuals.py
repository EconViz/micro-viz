from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest
from mosaickit import Canvas, FillLayer, PathLayer, TextLayer

from micro_viz import (
    ProductionAnalysis,
    ShortRunProductionFunction,
    analyze_production,
    average_marginal_product_canvas,
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


def test_total_product_canvas_has_semantic_curve_regions_and_label(
    analysis: ProductionAnalysis,
) -> None:
    canvas = total_product_canvas(analysis)
    layers = _layers(canvas)

    assert isinstance(layers["micro.production.tp"], PathLayer)
    assert isinstance(layers["micro.production.tp.label"], TextLayer)
    for name in ("increasing", "diminishing", "negative"):
        layer = layers[f"micro.production.region.{name}"]
        assert isinstance(layer, FillLayer)
        assert layer.role == f"micro.production.region.{name}"
    assert canvas.spec.x_label == "L"
    assert canvas.spec.y_label == "Q"


def test_average_marginal_canvas_has_distinct_ap_and_mp_curves(
    analysis: ProductionAnalysis,
) -> None:
    canvas = average_marginal_product_canvas(analysis)
    layers = _layers(canvas)

    average = layers["micro.production.ap"]
    marginal = layers["micro.production.mp"]
    assert isinstance(average, PathLayer)
    assert isinstance(marginal, PathLayer)
    assert average.role == "micro.production.average"
    assert marginal.role == "micro.production.marginal"
    assert isinstance(layers["micro.production.ap.label"], TextLayer)
    assert isinstance(layers["micro.production.mp.label"], TextLayer)


def test_titles_accept_custom_text_or_none(analysis: ProductionAnalysis) -> None:
    assert total_product_canvas(analysis, title="Short-run output").spec.title == "Short-run output"
    assert total_product_canvas(analysis, title=None).spec.title is None
    assert average_marginal_product_canvas(analysis, title="Products").spec.title == "Products"
    assert average_marginal_product_canvas(analysis, title=None).spec.title is None


def test_default_visuals_are_coloured_on_white(analysis: ProductionAnalysis) -> None:
    total = total_product_canvas(analysis)
    products = average_marginal_product_canvas(analysis)
    total_layers = _layers(total)
    product_layers = _layers(products)

    canvas_style = total.theme.resolve("canvas", fallback_category="fill")
    assert canvas_style.fill is not None and canvas_style.fill.color is not None
    assert canvas_style.fill.color.to_hex().lower() == "#ffffff"
    assert _stroke_color(total, total_layers["micro.production.tp"]) == "#377eb8"
    assert _stroke_color(products, product_layers["micro.production.ap"]) == "#4daf4a"
    assert _stroke_color(products, product_layers["micro.production.mp"]) == "#e41a1c"


def test_manual_visuals_are_black_and_white(analysis: ProductionAnalysis) -> None:
    theme = shared_theme("manual")
    total = total_product_canvas(analysis, theme=theme)
    products = average_marginal_product_canvas(analysis, theme=theme)
    total_layers = _layers(total)
    product_layers = _layers(products)

    assert _stroke_color(total, total_layers["micro.production.tp"]) == "#8c8c8c"
    assert _stroke_color(products, product_layers["micro.production.ap"]) == "#1a1a1a"
    assert _stroke_color(products, product_layers["micro.production.mp"]) == "#1a1a1a"


def test_both_production_canvases_render_to_svg(
    analysis: ProductionAnalysis, tmp_path: Path
) -> None:
    for name, canvas in (
        ("total-product", total_product_canvas(analysis)),
        ("average-marginal", average_marginal_product_canvas(analysis)),
    ):
        output = tmp_path / f"{name}.svg"
        canvas.save(output)
        svg = output.read_text(encoding="utf-8")
        assert output.stat().st_size > 0
        assert "micro.production" in svg
