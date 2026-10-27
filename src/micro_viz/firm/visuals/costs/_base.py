"""Shared unit-curve styles and helpers of the cost figures."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import Canvas, Layer

from micro_viz.core.theme import PlotTheme
from micro_viz.firm.costs import Cost, CostAnalysis, CostFunction, analyze_costs
from micro_viz.visuals.common import (
    Point,
    Range,
    Texts,
    axis_mark,
    dot,
    drop_line,
    new_canvas,
    resolve_theme,
)

CostSource = CostAnalysis | CostFunction | str
"""What a cost figure accepts: an analysis, a cost function or a formula (``"TC = 50 + 3Q"``)."""
SAMPLES = 201
"""Default number of sampled outputs when a figure analyses a cost function itself."""
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


def resolve_analysis(
    source: CostSource, output: tuple[float, float] | None, samples: int = SAMPLES
) -> CostAnalysis:
    """The analysis a figure draws: ``source`` itself, or the cost function (or formula) in
    ``source`` analysed over ``output``."""
    if isinstance(source, CostAnalysis):
        return source
    if output is None:
        raise TypeError("pass output=(low, high), the range of output the figure covers")
    cost = Cost(source) if isinstance(source, str) else source
    return analyze_costs(cost, output_range=output, samples=samples)


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


def _curve_selection(curves: Sequence[str]) -> tuple[str, ...]:
    unknown = [name for name in curves if name not in UNIT_CURVES]
    if unknown:
        raise ValueError(f"unknown curves {unknown}; choose from {', '.join(UNIT_CURVES)}")
    return tuple(name for name in UNIT_CURVES if name in curves)


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
