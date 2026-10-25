"""mosaickit visual builders for short-run production analysis."""

from __future__ import annotations

from collections.abc import Mapping

from mosaickit import BraceLayer, Canvas, Layer, PointLabelLayer, TextLayer

from micro_viz.production import MarginalReturns, ProductionAnalysis
from micro_viz.theme import PlotTheme
from micro_viz.visuals.axes import axes_layers
from micro_viz.visuals.common import (
    FIGURE_DPI,
    FIGURE_SIZE,
    MARGIN,
    Point,
    Range,
    Texts,
    axis_mark,
    curve,
    curve_name,
    dot,
    drop_line,
    guide,
    new_canvas,
    nudge_labels,
    pad_range,
    region,
    resolve_theme,
)

_SHADES = {
    MarginalReturns.INCREASING: "light",
    MarginalReturns.DIMINISHING: "mid",
    MarginalReturns.NEGATIVE: "dark",
}
ANNOTATION_OFFSET_PT = (8.0, 6.0)
"""Offset in points of the MP = 0 annotation from its point, up and to the right."""
MARK_GAP_PT = 4.0
"""Gap in points between the x axis and a mark written under it."""


def _region_layers(
    result: ProductionAnalysis, y_range: Range, texts: Texts
) -> tuple[Layer, ...]:
    low, high = y_range
    layers: list[Layer] = []
    for item in result.regions:
        kind = item.kind.value
        layer_id = f"micro.production.region.{kind}"
        layers.append(
            region(
                (
                    (item.start_input, low),
                    (item.end_input, low),
                    (item.end_input, high),
                    (item.start_input, high),
                ),
                layer_id=layer_id,
                shade=_SHADES[item.kind],
                model=item,
            )
        )
        layers.append(
            BraceLayer(
                "x",
                item.start_input,
                item.end_input,
                texts(f"production.region.{kind}"),
                side="outside",
                id=f"{layer_id}.brace",
            )
        )
    return tuple(layers)


def _key_inputs(result: ProductionAnalysis) -> tuple[tuple[str, str, float], ...]:
    """The three boundary inputs as (id, text id of its mark, value)."""
    return (
        ("inflection", "production.mark.inflection", result.inflection_input),
        ("average_max", "production.mark.average_max", result.average_product_max_input),
        ("total_max", "production.mark.total_max", result.total_product_max_input),
    )


def _mark(
    value: float, text: str, *, layer_id: str, axis_at_bottom: bool, left_of: bool = False
) -> Layer:
    """A math mark for an input, under the horizontal axis wherever the axis crosses."""
    if axis_at_bottom:
        return axis_mark("x", value, text, layer_id=layer_id)
    return TextLayer(
        (value, 0.0),
        text,
        id=layer_id,
        role="axes",
        anchor="top-right" if left_of else "top",
        offset=(-MARK_GAP_PT / 2 if left_of else 0.0, -MARK_GAP_PT),
        math=True,
        z_index=8,
    )


def _setup(
    result: ProductionAnalysis,
    *,
    theme: PlotTheme | None,
    labels: Mapping[str, str] | None,
    x_label: str | None,
    y_label: str | None,
    x_max: float | None,
    y_range: Range,
    title: str | None,
    size: tuple[float, float],
    dpi: int,
    y_text_id: str | None,
) -> tuple[Canvas, PlotTheme, Texts, Range, tuple[Layer, ...]]:
    selected = resolve_theme(theme)
    texts = Texts(selected, labels)
    function = result.production_function
    x_axis: Range = (0.0, x_max if x_max is not None else result.input_range[1] * (1 + MARGIN))
    horizontal = x_label if x_label is not None else function.input_symbol
    if y_label is not None:
        vertical = y_label
    elif y_text_id is not None:
        vertical = texts(y_text_id)
    else:
        vertical = function.output_symbol
    canvas = new_canvas(
        selected,
        x_range=x_axis,
        y_range=y_range,
        x_label=horizontal,
        y_label=vertical,
        title=title,
        size=size,
        dpi=dpi,
    )
    base = axes_layers(x_axis, y_range, x_label=horizontal, y_label=vertical)
    return canvas, selected, texts, x_axis, base


def total_product_canvas(
    result: ProductionAnalysis,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    x_label: str | None = None,
    y_label: str | None = None,
    x_max: float | None = None,
    y_range: Range | None = None,
    margin: float = MARGIN,
    regions: bool = True,
    guides: bool = True,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """A TP diagram: the curve, its three marginal-return regions and the boundary guides.

    ``regions`` shades and names the increasing, diminishing and negative marginal-return
    regions; ``guides`` marks the inflection (MP maximum), the AP maximum (the ray from the
    origin is tangent to TP there) and the TP maximum with dashed drop lines and axis marks.
    ``title=None`` draws no title; ``labels`` replaces built-in texts by id.
    """
    function = result.production_function
    points: tuple[Point, ...] = tuple(
        (point.variable_input, point.total_product) for point in result.points
    )
    vertical: Range = y_range or pad_range(0.0, max(value for _, value in points), margin)
    canvas, selected, texts, _, base = _setup(
        result,
        theme=theme,
        labels=labels,
        x_label=x_label,
        y_label=y_label,
        x_max=x_max if x_max is not None else result.input_range[1] * (1 + margin),
        y_range=vertical,
        title=title,
        size=size,
        dpi=dpi,
        y_text_id=None,
    )
    layers: list[Layer] = list(base)
    if regions:
        layers.extend(_region_layers(result, vertical, texts))
    tp = curve(points, layer_id="micro.production.tp", role="micro.curve.total", model=result)
    layers.extend((tp, curve_name(tp, texts("production.tp"))))
    if guides:
        symbol = function.input_symbol
        for name, key, value in _key_inputs(result):
            level = function.total_product(value)
            layers.append(drop_line(value, level, layer_id=f"micro.production.guide.{name}"))
            layers.append(dot((value, level), layer_id=f"micro.production.point.{name}"))
            layers.append(
                axis_mark("x", value, texts(key, input=symbol), layer_id=f"micro.production.mark.{name}")
            )
        average_point = (result.average_product_max_input, function.total_product(result.average_product_max_input))
        layers.append(guide((0.0, 0.0), average_point, layer_id="micro.production.guide.ray"))
    canvas.extend(nudge_labels(layers, selected.label_nudges))
    return canvas


def average_marginal_product_canvas(
    result: ProductionAnalysis,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    x_label: str | None = None,
    y_label: str | None = None,
    x_max: float | None = None,
    y_range: Range | None = None,
    margin: float = MARGIN,
    regions: bool = True,
    guides: bool = True,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """An AP/MP diagram with the marginal-return regions and the AP = MP and MP = 0 points.

    AP and MP meet where AP peaks; MP crosses zero where TP peaks. ``guides`` draws dashed
    drop lines from the MP maximum, the AP = MP point and the MP = 0 point to the axis.
    """
    function = result.production_function
    average: tuple[Point, ...] = tuple(
        (point.variable_input, point.average_product)
        for point in result.points
        if point.average_product is not None
    )
    marginal: tuple[Point, ...] = tuple(
        (point.variable_input, point.marginal_product) for point in result.points
    )
    values = [value for _, value in (*average, *marginal)]
    vertical: Range = y_range or pad_range(min(0.0, *values), max(values), margin)
    canvas, selected, texts, _, base = _setup(
        result,
        theme=theme,
        labels=labels,
        x_label=x_label,
        y_label=y_label,
        x_max=x_max if x_max is not None else result.input_range[1] * (1 + margin),
        y_range=vertical,
        title=title,
        size=size,
        dpi=dpi,
        y_text_id="production.product",
    )
    layers: list[Layer] = list(base)
    if regions:
        layers.extend(_region_layers(result, vertical, texts))
    ap = curve(average, layer_id="micro.production.ap", role="micro.curve.average", model=result)
    mp = curve(marginal, layer_id="micro.production.mp", role="micro.curve.marginal", model=result)
    layers.extend((ap, curve_name(ap, texts("production.ap")), mp, curve_name(mp, texts("production.mp"))))
    if guides:
        symbol = function.input_symbol
        at_bottom = vertical[0] >= 0.0
        peak = result.inflection_input
        meet = result.average_product_max_input
        zero = result.total_product_max_input
        points = {
            "inflection": (peak, function.marginal_product(peak)),
            "average_max": (meet, function.marginal_product(meet)),
            "total_max": (zero, 0.0),
        }
        keys = {name: key for name, key, _ in _key_inputs(result)}
        for name, point in points.items():
            if point[1] != 0.0:
                layers.append(drop_line(point[0], point[1], layer_id=f"micro.production.guide.{name}"))
            layers.append(dot(point, layer_id=f"micro.production.point.{name}"))
            layers.append(
                _mark(
                    point[0],
                    texts(keys[name], input=symbol),
                    layer_id=f"micro.production.mark.{name}",
                    axis_at_bottom=at_bottom,
                    left_of=name == "total_max",
                )
            )
        layers.append(
            PointLabelLayer(
                points["average_max"],
                texts("production.annotation.ap_equals_mp"),
                id="micro.production.annotation.ap_equals_mp",
                role="micro.point",
                z_index=7,
            )
        )
        layers.append(
            TextLayer(
                points["total_max"],
                texts("production.annotation.mp_zero"),
                id="micro.production.annotation.mp_zero",
                role="micro.annotation",
                anchor="bottom-left",
                offset=ANNOTATION_OFFSET_PT,
                z_index=7,
            )
        )
    canvas.extend(nudge_labels(layers, selected.label_nudges))
    return canvas


__all__ = ["average_marginal_product_canvas", "total_product_canvas"]
