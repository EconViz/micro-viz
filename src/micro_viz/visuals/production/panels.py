"""mosaickit visual builders for short-run production analysis."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import replace

from mosaickit import Canvas, Layer, PointLabelLayer, TextLayer
from mosaickit.styles import Fill

from micro_viz.production import MarginalReturns, ProductionAnalysis
from micro_viz.theme import LABEL_SIZE, PlotTheme
from micro_viz.visuals.axes import axes_layers
from micro_viz.visuals.common import (
    FIGURE_DPI,
    FIGURE_SIZE,
    LABEL_LINE,
    MARGIN,
    Frame,
    Point,
    Range,
    Texts,
    curve,
    curve_name,
    dot,
    drop_covered_guides,
    drop_line,
    frame_for,
    guide,
    new_canvas,
    nudge_labels,
    pad_range,
    region,
    region_brace,
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


def _region_polygon(
    start: float, end: float, low: float, high: float, top: Callable[[float], float] | None
) -> tuple[Point, ...]:
    """A region from ``low`` up to ``high``, or up to ``top(x)`` when the shade stops at the
    curve (capped at ``high``)."""
    if top is None:
        return ((start, low), (end, low), (end, high), (start, high))
    steps = 24
    xs = [start + (end - start) * i / steps for i in range(steps + 1)]
    upper = tuple((x, min(max(top(x), low), high)) for x in xs)
    return ((start, low), (end, low), *reversed(upper))


def _region_layers(
    result: ProductionAnalysis,
    frame: Frame,
    high: float,
    texts: Texts,
    *,
    theme: PlotTheme,
    top: Callable[[float], float],
    colors: Mapping[str, str] | None,
) -> tuple[Layer, ...]:
    """The regions from ``frame.fill_low`` up to ``high`` (or the curve ``top``), each with its
    brace and name. ``theme.region_fill`` switches the shade off; ``colors`` maps a region kind
    to its own colour."""
    layers: list[Layer] = []
    for item in result.regions:
        kind = item.kind.value
        layer_id = f"micro.production.region.{kind}"
        if theme.region_fill:
            shaded = region(
                _region_polygon(
                    item.start_input,
                    item.end_input,
                    frame.fill_low,
                    high,
                    top if theme.region_extent == "curve" else None,
                ),
                layer_id=layer_id,
                shade=_SHADES[item.kind],
                model=item,
            )
            if colors and kind in colors:
                shaded = replace(
                    shaded, fill=Fill(color=colors[kind], opacity=theme.region_opacity)
                )
            layers.append(shaded)
        if frame.brace_y is not None:
            layers.append(
                region_brace(
                    item.start_input,
                    item.end_input,
                    frame.brace_y,
                    texts(f"production.region.{kind}"),
                    layer_id=f"{layer_id}.brace",
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


def _mark(value: float, text: str, *, layer_id: str, left_of: bool = False) -> Layer:
    """A math mark for an input, written under the horizontal axis."""
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


def _layout(
    theme: PlotTheme,
    natural: Range,
    size: tuple[float, float],
    *,
    marks: bool,
    braces: bool,
    texts: Texts,
) -> Frame:
    label_size = LABEL_SIZE * theme.label_scale
    lines = max(texts(f"production.region.{kind.value}").count("\n") + 1 for kind in _SHADES)
    return frame_for(
        natural,
        size,
        mark_room=MARK_GAP_PT + LABEL_LINE * label_size if marks else 0.0,
        brace_gap=theme.brace_gap if braces else None,
        label_size=label_size,
        label_lines=lines,
    )


def _setup(
    result: ProductionAnalysis,
    *,
    theme: PlotTheme,
    texts: Texts,
    x_label: str | None,
    y_label: str | None,
    x_axis: Range,
    frame: Frame,
    high: float,
    title: str | None,
    size: tuple[float, float],
    dpi: int,
    y_text_id: str | None,
) -> tuple[Canvas, list[Layer]]:
    function = result.production_function
    horizontal = x_label if x_label is not None else function.input_symbol
    if y_label is not None:
        vertical = y_label
    elif y_text_id is not None:
        vertical = texts(y_text_id)
    else:
        vertical = function.output_symbol
    y_range = (frame.y_range[0], high)
    canvas = new_canvas(
        theme,
        x_range=x_axis,
        y_range=y_range,
        x_label=horizontal,
        y_label=vertical,
        title=title,
        size=size,
        dpi=dpi,
    )
    base = axes_layers(
        x_axis,
        y_range,
        x_label=horizontal,
        y_label=vertical,
        y_axis_start=frame.natural_low,
    )
    return canvas, list(base)


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
    region_colors: Mapping[str, str] | None = None,
    guides: bool = True,
    marks: bool = True,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """A TP diagram: the curve, its three marginal-return regions and the boundary guides.

    ``regions`` shades and names the increasing, diminishing and negative marginal-return
    regions with braces under them, ``theme.brace_gap`` points below the shaded area;
    ``guides`` marks the inflection (MP maximum), the AP maximum (the ray from the origin is
    tangent to TP there) and the TP maximum with dashed drop lines. ``marks`` writes their
    input names under the axis; it can be switched off when this canvas is an upper panel.
    ``region_colors`` maps a region kind (``increasing``, ``diminishing``, ``negative``) to its
    own colour; whether regions are shaded and whether the shade stops at the curve are the
    theme's ``region_fill`` and ``region_extent`` (``[micro.region]``).
    ``title=None`` draws no title; ``labels`` replaces built-in texts by id.
    """
    selected = resolve_theme(theme)
    texts = Texts(selected, labels)
    function = result.production_function
    points: tuple[Point, ...] = tuple(
        (point.variable_input, point.total_product) for point in result.points
    )
    natural: Range = y_range or pad_range(0.0, max(value for _, value in points), margin)
    frame = _layout(
        selected,
        natural,
        size,
        marks=(guides and marks) or regions,
        braces=regions,
        texts=texts,
    )
    x_axis: Range = (0.0, x_max if x_max is not None else result.input_range[1] * (1 + margin))
    canvas, layers = _setup(
        result,
        theme=selected,
        texts=texts,
        x_label=x_label,
        y_label=y_label,
        x_axis=x_axis,
        frame=frame,
        high=natural[1],
        title=title,
        size=size,
        dpi=dpi,
        y_text_id=None,
    )
    if regions:
        layers.extend(
            _region_layers(
                result,
                frame,
                natural[1],
                texts,
                theme=selected,
                top=function.total_product,
                colors=region_colors,
            )
        )
    tp = curve(points, layer_id="micro.production.tp", role="micro.curve.total", model=result)
    layers.extend((tp, curve_name(tp, texts("production.tp"))))
    if guides:
        symbol = function.input_symbol
        for name, key, value in _key_inputs(result):
            level = function.total_product(value)
            layers.append(drop_line(value, level, layer_id=f"micro.production.guide.{name}"))
            layers.append(dot((value, level), layer_id=f"micro.production.point.{name}"))
            if marks:
                layers.append(
                    _mark(
                        value,
                        texts(key, input=symbol),
                        layer_id=f"micro.production.mark.{name}",
                    )
                )
        average_point = (
            result.average_product_max_input,
            function.total_product(result.average_product_max_input),
        )
        layers.append(guide((0.0, 0.0), average_point, layer_id="micro.production.guide.ray"))
    canvas.extend(nudge_labels(drop_covered_guides(layers), selected.label_nudges))
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
    region_colors: Mapping[str, str] | None = None,
    guides: bool = True,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """An AP/MP diagram with the marginal-return regions and the AP = MP and MP = 0 points.

    AP and MP meet where AP peaks; MP crosses zero where TP peaks. ``guides`` draws dashed
    drop lines from the MP maximum, the AP = MP point and the MP = 0 point to the axis.
    The region braces sit ``theme.brace_gap`` points under the shaded area.
    """
    selected = resolve_theme(theme)
    texts = Texts(selected, labels)
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
    natural: Range = y_range or pad_range(min(0.0, *values), max(values), margin)
    frame = _layout(selected, natural, size, marks=False, braces=regions, texts=texts)
    x_axis: Range = (0.0, x_max if x_max is not None else result.input_range[1] * (1 + margin))
    canvas, layers = _setup(
        result,
        theme=selected,
        texts=texts,
        x_label=x_label,
        y_label=y_label,
        x_axis=x_axis,
        frame=frame,
        high=natural[1],
        title=title,
        size=size,
        dpi=dpi,
        y_text_id="production.product",
    )

    def upper(x: float) -> float:
        average_product = function.average_product(x)
        average_value = average_product if average_product is not None else 0.0
        return float(max(average_value, function.marginal_product(x)))

    if regions:
        layers.extend(
            _region_layers(
                result,
                frame,
                natural[1],
                texts,
                theme=selected,
                top=upper,
                colors=region_colors,
            )
        )
    ap = curve(average, layer_id="micro.production.ap", role="micro.curve.average", model=result)
    mp = curve(marginal, layer_id="micro.production.mp", role="micro.curve.marginal", model=result)
    layers.extend(
        (ap, curve_name(ap, texts("production.ap")), mp, curve_name(mp, texts("production.mp")))
    )
    if guides:
        symbol = function.input_symbol
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
                layers.append(
                    drop_line(point[0], point[1], layer_id=f"micro.production.guide.{name}")
                )
            layers.append(dot(point, layer_id=f"micro.production.point.{name}"))
            layers.append(
                _mark(
                    point[0],
                    texts(keys[name], input=symbol),
                    layer_id=f"micro.production.mark.{name}",
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
    canvas.extend(nudge_labels(drop_covered_guides(layers), selected.label_nudges))
    return canvas


__all__ = ["average_marginal_product_canvas", "total_product_canvas"]
