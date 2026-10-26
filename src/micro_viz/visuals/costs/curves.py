"""Total, unit and stacked cost-curve figures."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import Canvas, CanvasGrid, GridLink, Layer

from micro_viz.costs import CostAnalysis
from micro_viz.theme import PlotTheme
from micro_viz.visuals.axes import axes_layers
from micro_viz.visuals.common import (
    FIGURE_DPI,
    FIGURE_SIZE,
    MARGIN,
    Range,
    axis_mark,
    curve,
    curve_name,
    dot,
    drop_covered_guides,
    drop_line,
    guide,
    nudge_labels,
    pad_range,
    resolve_theme,
)
from micro_viz.visuals.costs._base import (
    _UNIT_STYLE,
    PANEL_SIZE,
    UNIT_CURVES,
    _curve_selection,
    _output_marks,
    _setup,
    _unit_points,
)


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
