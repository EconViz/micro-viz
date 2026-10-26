"""mosaickit visual builders for short-run cost curves."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import Canvas, CanvasGrid, GridLink, Layer

from micro_viz.costs import CostAnalysis, PiecewiseCost
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
    drop_covered_guides,
    drop_line,
    guide,
    new_canvas,
    nudge_labels,
    pad_range,
    resolve_theme,
)

PANEL_SIZE = (6.0, 4.5)
"""Default size in inches of each panel of a stacked figure."""
UNIT_CURVES = ("mc", "atc", "avc", "afc")
"""The per-unit curves :func:`unit_cost_canvas` can draw, in drawing order."""
_UNIT_STYLE = {
    "mc": ("micro.curve.marginal", "cost.mc", 1.0),
    "atc": ("micro.curve.average", "cost.atc", 1.0),
    "avc": ("micro.curve.average.variable", "cost.avc", 1.0),
    "afc": ("micro.curve.average.fixed", "cost.afc", 1.0),
}
"""Role, text id and the share of the curve at which its name is written, per unit curve."""


def _unit_points(analysis: CostAnalysis, name: str) -> tuple[Point, ...]:
    if name == "mc":
        return analysis.marginal_cost_path
    attribute = {
        "atc": "average_total_cost",
        "avc": "average_variable_cost",
        "afc": "average_fixed_cost",
    }[name]
    return tuple(
        (point.output, value)
        for point in analysis.points
        if (value := getattr(point, attribute)) is not None
    )


def _setup(
    analysis: CostAnalysis,
    *,
    theme: PlotTheme | None,
    labels: Mapping[str, str] | None,
    x_label: str | None,
    y_label: str | None,
    y_text_id: str,
    x_max: float | None,
    y_range: Range,
    title: str | None,
    size: tuple[float, float],
    dpi: int,
    margin: float,
) -> tuple[Canvas, PlotTheme, Texts, Range, str, str]:
    selected = resolve_theme(theme)
    texts = Texts(selected, labels)
    symbol = analysis.cost.output_symbol
    x_axis: Range = (0.0, x_max if x_max is not None else analysis.output_range[1] * (1 + margin))
    horizontal = x_label if x_label is not None else symbol
    vertical = y_label if y_label is not None else texts(y_text_id)
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
    return canvas, selected, texts, x_axis, horizontal, vertical


def total_cost_canvas(
    analysis: CostAnalysis,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    x_label: str | None = None,
    y_label: str | None = None,
    x_max: float | None = None,
    y_range: Range | None = None,
    margin: float = MARGIN,
    ray: bool = True,
    marks: bool = True,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """TC, VC and FC against output.

    ``ray`` draws the dashed line from the origin to TC at the lowest average total cost: its
    slope is the minimum ATC, and TC is tangent to it there (cubic cost functions only);
    ``marks=False`` leaves out its output mark (for a panel stacked above a unit-cost panel).
    """
    cost = analysis.cost
    # Totals are defined at zero output, so they start at the axis whatever the unit-cost range.
    count = len(analysis.points)
    last = analysis.output_range[1]
    outputs = [last * index / (count - 1) for index in range(count)]
    total = tuple((q, cost.total_cost(q)) for q in outputs)
    variable = tuple((q, cost.variable_cost(q)) for q in outputs)
    fixed = tuple((q, cost.fixed_cost) for q in outputs)
    vertical = y_range or pad_range(0.0, max(value for _, value in total), margin)
    canvas, selected, texts, x_axis, horizontal, vertical_label = _setup(
        analysis,
        theme=theme,
        labels=labels,
        x_label=x_label,
        y_label=y_label,
        y_text_id="cost.axis.total",
        x_max=x_max,
        y_range=vertical,
        title=title,
        size=size,
        dpi=dpi,
        margin=margin,
    )
    layers: list[Layer] = list(
        axes_layers(x_axis, vertical, x_label=horizontal, y_label=vertical_label)
    )
    for name, points, role, key in (
        ("tc", total, "micro.curve.total", "cost.tc"),
        ("vc", variable, "micro.curve.variable", "cost.vc"),
        ("fc", fixed, "micro.curve.fixed", "cost.fc"),
    ):
        if name == "fc" and cost.fixed_cost == 0:
            continue
        path = curve(points, layer_id=f"micro.cost.{name}", role=role, model=analysis)
        layers.extend((path, curve_name(path, texts(key))))
    extremum = analysis.minimum_average_total_cost
    if ray and extremum is not None:
        level = cost.total_cost(extremum.output)
        symbol = cost.output_symbol
        layers.append(guide((0.0, 0.0), (extremum.output, level), layer_id="micro.cost.guide.ray"))
        layers.append(drop_line(extremum.output, level, layer_id="micro.cost.guide.min_atc"))
        layers.append(dot((extremum.output, level), layer_id="micro.cost.point.min_atc"))
        if marks:
            layers.append(
                axis_mark(
                    "x",
                    extremum.output,
                    texts("cost.mark.min_atc.output", output=symbol),
                    layer_id="micro.cost.mark.min_atc.output",
                )
            )
    canvas.extend(nudge_labels(drop_covered_guides(layers), selected.label_nudges))
    return canvas


def _curve_selection(curves: Sequence[str]) -> tuple[str, ...]:
    unknown = [name for name in curves if name not in UNIT_CURVES]
    if unknown:
        raise ValueError(f"unknown curves {unknown}; choose from {', '.join(UNIT_CURVES)}")
    return tuple(name for name in UNIT_CURVES if name in curves)


def unit_cost_canvas(
    analysis: CostAnalysis,
    *,
    curves: Sequence[str] = UNIT_CURVES,
    minima: bool = True,
    output: float | None = None,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    x_label: str | None = None,
    y_label: str | None = None,
    x_max: float | None = None,
    y_range: Range | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """MC, ATC, AVC and AFC against output (choose a subset with ``curves``).

    ``minima`` marks the lowest AVC and ATC (where MC crosses them) with dashed guides to both
    axes, for cubic cost functions. ``output`` marks the unit costs at one output with dots and
    a dashed drop line, so the figure can be swept as output grows.
    """
    chosen = _curve_selection(curves)
    series = {name: _unit_points(analysis, name) for name in chosen}
    top = max(value for points in series.values() for _, value in points)
    vertical = y_range or pad_range(0.0, top, margin)
    canvas, selected, texts, x_axis, horizontal, vertical_label = _setup(
        analysis,
        theme=theme,
        labels=labels,
        x_label=x_label,
        y_label=y_label,
        y_text_id="cost.axis.unit",
        x_max=x_max,
        y_range=vertical,
        title=title,
        size=size,
        dpi=dpi,
        margin=margin,
    )
    cost = analysis.cost
    symbol = cost.output_symbol
    layers: list[Layer] = list(
        axes_layers(x_axis, vertical, x_label=horizontal, y_label=vertical_label)
    )
    for name in chosen:
        role, key, along = _UNIT_STYLE[name]
        path = curve(series[name], layer_id=f"micro.cost.{name}", role=role, model=analysis)
        layers.extend((path, curve_name(path, texts(key), at=along)))
    if minima:
        for name, extremum, shown in (
            ("min_avc", analysis.minimum_average_variable_cost, "avc"),
            ("min_atc", analysis.minimum_average_total_cost, "atc"),
        ):
            if extremum is None or shown not in chosen:
                continue
            point = (extremum.output, extremum.value)
            layers.append(drop_line(point[0], point[1], layer_id=f"micro.cost.guide.{name}.output"))
            layers.append(guide((0.0, point[1]), point, layer_id=f"micro.cost.guide.{name}.cost"))
            layers.append(dot(point, layer_id=f"micro.cost.point.{name}"))
            layers.append(
                axis_mark(
                    "x",
                    point[0],
                    texts(f"cost.mark.{name}.output", output=symbol),
                    layer_id=f"micro.cost.mark.{name}.output",
                )
            )
            layers.append(
                axis_mark(
                    "y",
                    point[1],
                    texts(f"cost.mark.{name}.cost"),
                    layer_id=f"micro.cost.mark.{name}.cost",
                )
            )
    if output is not None:
        layers.extend(_output_marks(analysis, chosen, output, texts, symbol))
    canvas.extend(nudge_labels(drop_covered_guides(layers), selected.label_nudges))
    return canvas


def _unit_value(cost_name: str, analysis: CostAnalysis, output: float) -> float | None:
    cost = analysis.cost
    if cost_name == "mc":
        return cost.marginal_cost(output)
    if cost_name == "atc":
        return cost.average_total_cost(output)
    if cost_name == "avc":
        return cost.average_variable_cost(output)
    return cost.average_fixed_cost(output)


def _output_marks(
    analysis: CostAnalysis,
    chosen: Sequence[str],
    output: float,
    texts: Texts,
    symbol: str,
) -> list[Layer]:
    layers: list[Layer] = []
    values = {name: _unit_value(name, analysis, output) for name in chosen}
    shown = [value for value in values.values() if value is not None]
    if shown:
        layers.append(drop_line(output, max(shown), layer_id="micro.cost.guide.output"))
    for name, value in values.items():
        if value is not None:
            layers.append(dot((output, value), layer_id=f"micro.cost.point.output.{name}"))
    layers.append(
        axis_mark(
            "x", output, texts("cost.mark.output", output=symbol), layer_id="micro.cost.mark.output"
        )
    )
    return layers


def cost_curves_panels(
    analysis: CostAnalysis,
    *,
    titles: tuple[str | None, str | None] = (None, None),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    x_max: float | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL_SIZE,
    dpi: int = FIGURE_DPI,
) -> tuple[Canvas, Canvas]:
    """The two panels of :func:`cost_curves_grid` as separate canvases: total cost, then unit
    costs, on the same output axis. Each stands alone as a figure."""
    selected = resolve_theme(theme)
    horizontal = x_max if x_max is not None else analysis.output_range[1] * (1 + margin)
    common = {
        "theme": selected,
        "labels": labels,
        "x_max": horizontal,
        "margin": margin,
        "size": size,
        "dpi": dpi,
    }
    upper = total_cost_canvas(analysis, title=titles[0], marks=False, **common)  # type: ignore[arg-type]
    lower = unit_cost_canvas(analysis, title=titles[1], **common)  # type: ignore[arg-type]
    return upper, lower


def cost_curves_grid(
    analysis: CostAnalysis,
    *,
    titles: tuple[str | None, str | None] = (None, None),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    x_max: float | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL_SIZE,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """The total-cost panel above the per-unit panel, sharing the output axis.

    A dashed link joins the tangency point of the total-cost panel (the lowest ATC) to the
    lowest-ATC point of the unit-cost panel.
    """
    upper, lower = cost_curves_panels(
        analysis,
        titles=titles,
        theme=theme,
        labels=labels,
        x_max=x_max,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    links: list[GridLink] = []
    extremum = analysis.minimum_average_total_cost
    if extremum is not None:
        level = analysis.cost.total_cost(extremum.output)
        links.append(
            GridLink(
                0,
                (extremum.output, level),
                1,
                (extremum.output, extremum.value),
                role="micro.guide",
            )
        )
    return CanvasGrid([[upper], [lower]], links=links)


def piecewise_cost_canvas(
    analysis: CostAnalysis,
    *,
    prices: Sequence[float] = (),
    average: bool = True,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    x_label: str | None = None,
    y_label: str | None = None,
    x_max: float | None = None,
    y_range: Range | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Stepped or kinked marginal cost with its capacity and price bands.

    MC is drawn with its jumps; ``average`` adds AVC. A dashed vertical line marks the capacity.
    Each price in ``prices`` is a dashed horizontal line with a dot at the output the firm
    chooses at that price (where the price meets MC, or the last output before a jump that
    lies above it) and axis marks for the price and the output.
    """
    cost = analysis.cost
    if not isinstance(cost, PiecewiseCost):
        raise TypeError("piecewise_cost_canvas needs a PiecewiseCost")
    series = {}
    if average:
        series["avc"] = _unit_points(analysis, "avc")
    series["mc"] = _unit_points(analysis, "mc")  # drawn last: MC lies over AVC where they meet
    top = max(max(value for _, value in points) for points in series.values())
    top = max([top, *prices])
    low = min(min(value for _, value in points) for points in series.values())
    vertical = y_range or pad_range(min(0.0, low) if low < 0 else 0.0, top, margin)
    canvas, selected, texts, x_axis, horizontal, vertical_label = _setup(
        analysis,
        theme=theme,
        labels=labels,
        x_label=x_label,
        y_label=y_label,
        y_text_id="cost.axis.unit",
        x_max=x_max,
        y_range=vertical,
        title=title,
        size=size,
        dpi=dpi,
        margin=margin,
    )
    symbol = cost.output_symbol
    layers: list[Layer] = list(
        axes_layers(x_axis, vertical, x_label=horizontal, y_label=vertical_label)
    )
    for name, points in series.items():
        role, key, along = _UNIT_STYLE[name]
        path = curve(points, layer_id=f"micro.cost.{name}", role=role, model=analysis)
        layers.extend((path, curve_name(path, texts(key), at=along)))
    floor = vertical[0]
    layers.append(
        drop_line(cost.capacity, vertical[1], layer_id="micro.cost.guide.capacity", floor=floor)
    )
    layers.append(
        axis_mark(
            "x",
            cost.capacity,
            texts("cost.mark.capacity", output=symbol),
            layer_id="micro.cost.mark.capacity",
        )
    )
    for index, price in enumerate(prices, start=1):
        quantity = cost.output_at_price(price)
        layers.append(
            guide((0.0, price), (x_axis[1], price), layer_id=f"micro.cost.guide.price.{index}")
        )
        layers.append(
            axis_mark(
                "y",
                price,
                texts("cost.mark.price", index=index),
                layer_id=f"micro.cost.mark.price.{index}",
            )
        )
        if quantity > 0:
            layers.append(
                drop_line(quantity, price, layer_id=f"micro.cost.guide.output.{index}", floor=floor)
            )
            layers.append(dot((quantity, price), layer_id=f"micro.cost.point.output.{index}"))
        if 0 < quantity < cost.capacity:
            layers.append(
                axis_mark(
                    "x",
                    quantity,
                    texts("cost.mark.price_output", output=symbol, index=index),
                    layer_id=f"micro.cost.mark.output.{index}",
                )
            )
    canvas.extend(nudge_labels(drop_covered_guides(layers), selected.label_nudges))
    return canvas


__all__ = [
    "UNIT_CURVES",
    "cost_curves_grid",
    "piecewise_cost_canvas",
    "total_cost_canvas",
    "unit_cost_canvas",
]
