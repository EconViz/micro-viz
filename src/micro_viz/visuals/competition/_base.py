"""Shared start, finish and curve helpers of the competition figures."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from mosaickit import Canvas, Layer

from micro_viz.costs import CostAnalysis
from micro_viz.theme import PlotTheme
from micro_viz.visuals.axes import axes_layers
from micro_viz.visuals.common import (
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
    resolve_theme,
)
from micro_viz.visuals.costs import _UNIT_STYLE, _unit_points

PANEL_SIZE = (6.0, 4.5)
"""Default size in inches of each panel of a multi-panel figure."""
SAMPLES = 61
"""Default points of a curve built from the model (supply and shift curves)."""


@dataclass(slots=True)
class _Start:
    canvas: Canvas
    theme: PlotTheme
    texts: Texts
    x_axis: Range
    y_range: Range
    layers: list[Layer]


def _start(
    *,
    theme: PlotTheme | None,
    labels: Mapping[str, str] | None,
    x_symbol: str,
    x_label: str | None,
    y_label: str | None,
    y_text_id: str,
    x_max: float,
    y_range: Range,
    title: str | None,
    size: tuple[float, float],
    dpi: int,
) -> _Start:
    selected = resolve_theme(theme)
    texts = Texts(selected, labels)
    x_axis: Range = (0.0, x_max)
    horizontal = x_label if x_label is not None else x_symbol
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
    layers = list(axes_layers(x_axis, y_range, x_label=horizontal, y_label=vertical))
    return _Start(canvas, selected, texts, x_axis, y_range, layers)


def _finish(start: _Start) -> Canvas:
    layers = drop_covered_guides(start.layers)
    start.canvas.extend(nudge_labels(layers, start.theme.label_nudges))
    return start.canvas


def _unit_curves(
    start: _Start, analysis: CostAnalysis, names: Sequence[str], *, prefix: str = "micro.cost"
) -> None:
    for name in names:
        role, key, along = _UNIT_STYLE[name]
        path = curve(
            _unit_points(analysis, name),
            layer_id=f"{prefix}.{name}",
            role=role,
            model=analysis,
        )
        start.layers.extend((path, curve_name(path, start.texts(key), at=along)))


def _price_line(start: _Start, price: float, *, key: str, layer_id: str) -> None:
    path = curve(
        ((0.0, price), (start.x_axis[1], price)),
        layer_id=layer_id,
        role="micro.curve.price",
    )
    start.layers.extend((path, curve_name(path, start.texts(key))))


def _top(analysis: CostAnalysis, names: Sequence[str], *extra: float) -> float:
    values = [value for name in names for _, value in _unit_points(analysis, name)]
    return max([*values, *extra])


def _x_max(analysis: CostAnalysis, x_max: float | None, margin: float) -> float:
    return x_max if x_max is not None else analysis.output_range[1] * (1 + margin)


def _output_marks(
    start: _Start,
    symbol: str,
    output: float,
    level: float,
    *,
    mark_id: str,
    key: str = "competition.mark.output",
    **fields: object,
) -> None:
    start.layers.append(drop_line(output, level, layer_id=f"micro.competition.guide.{mark_id}"))
    start.layers.append(dot((output, level), layer_id=f"micro.competition.point.{mark_id}"))
    start.layers.append(
        axis_mark(
            "x",
            output,
            start.texts(key, output=symbol, **fields),
            layer_id=f"micro.competition.mark.{mark_id}",
        )
    )


def _level_mark(
    start: _Start, level: float, key: str, *, mark_id: str, dotted: bool = True, **fields: object
) -> None:
    if dotted:
        start.layers.append(
            guide(
                (0.0, level),
                (start.x_axis[1], level),
                layer_id=f"micro.competition.guide.{mark_id}",
            )
        )
    start.layers.append(
        axis_mark(
            "y",
            level,
            start.texts(key, **fields),
            layer_id=f"micro.competition.mark.{mark_id}",
        )
    )


def _rectangle(left: float, right: float, low: float, high: float) -> tuple[Point, ...]:
    return ((left, low), (right, low), (right, high), (left, high))


def _between(upper: Sequence[Point], lower: Sequence[Point]) -> tuple[Point, ...]:
    """A polygon bounded above by ``upper`` (left to right) and below by ``lower``."""
    return (*upper, *reversed(lower))


def _slice(points: Sequence[Point], low: float, high: float) -> list[Point]:
    return [point for point in points if low <= point[0] <= high]


def _lower_crossing(function: Callable[[float], float], level: float, high: float) -> float:
    """The smallest output in ``0..high`` where ``function`` is at most ``level`` (bisection)."""
    if function(0.0) <= level:
        return 0.0
    low, up = 0.0, high
    for _ in range(60):
        middle = (low + up) / 2
        if function(middle) > level:
            low = middle
        else:
            up = middle
    return up


def _mc_between(analysis: CostAnalysis, low: float, high: float, samples: int = 41) -> list[Point]:
    cost = analysis.cost
    return [
        (q, cost.marginal_cost(q))
        for q in (low + (high - low) * index / (samples - 1) for index in range(samples))
    ]
