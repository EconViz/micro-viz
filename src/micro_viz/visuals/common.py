"""Pieces every micro-viz figure is built from: canvas, texts, curves, guides and regions."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace

from mosaickit import (
    AxisMarkLayer,
    Canvas,
    CanvasSpec,
    FillLayer,
    Layer,
    MarkerLayer,
    PathLayer,
    PointLabelLayer,
    RegionLabelLayer,
    SpanBraceLayer,
)
from mosaickit.styles.nudge import Nudge

from micro_viz.config import default_theme
from micro_viz.label_groups import label_group
from micro_viz.theme import PlotTheme

Point = tuple[float, float]
Range = tuple[float, float]

FIGURE_SIZE = (6.0, 6.0)
"""Default physical size in inches of one panel: square, as in textbook diagrams."""
FIGURE_DPI = 150
"""Default resolution of raster output."""
MARGIN = 0.1
"""Default share of an axis left beyond the data, so curve names fit inside the plot."""
POINTS_PER_INCH = 72.0
PLOT_HEIGHT_SHARE = 0.77
"""Share of the canvas height the plot area takes (mosaickit uses Matplotlib's default
subplot margins); it converts points to data units for things drawn inside the plot."""
LABEL_LINE = 1.3
"""Height of a line of label text, in font sizes."""
BRACE_BASE_PT = 4.0
"""Points mosaickit leaves between a span brace's line and the brace itself."""
BRACE_DEPTH_PT = 8.0
"""Depth in points of a span brace (its ends to its tip)."""
BRACE_LABEL_PAD_PT = 8.0
"""Points kept under a brace tip for the padding around its label and some slack."""


class Texts:
    """Resolve figure text: a caller's override first, then the built-in table.

    ``overrides`` maps a text id (``"production.tp"``) to the caller's own text, which is
    used as given and never translated.
    """

    def __init__(self, theme: PlotTheme, overrides: Mapping[str, str] | None = None) -> None:
        self.theme = theme
        self.overrides = dict(overrides or {})

    def __call__(self, key: str, **fields: object) -> str:
        if key in self.overrides:
            return self.overrides[key]
        return self.theme.text(key, **fields)


def pad_range(low: float, high: float, margin: float = MARGIN) -> Range:
    """``(low, high)`` extended past the data by ``margin`` of the span, never across zero."""
    span = high - low
    if span <= 0:
        return (min(low, 0.0) - 0.5, max(high, 0.0) + 0.5)
    return (low - margin * span if low < 0 else low, high + margin * span)


@dataclass(frozen=True, slots=True)
class Frame:
    """The vertical layout of a figure with a strip of the plot kept under its regions.

    ``y_range`` is the range of the canvas, including the strip; ``natural_low`` is where
    the data (and the vertical axis) end; ``fill_low`` is the bottom edge of the shaded
    regions; ``brace_y`` is the line braces hang from, placed so the braces start ``brace_gap``
    points below that edge (``None`` without braces); ``unit`` is the data per point.
    """

    y_range: Range
    natural_low: float
    fill_low: float
    brace_y: float | None
    unit: float


def frame_for(
    natural: Range,
    size: tuple[float, float],
    *,
    mark_room: float = 0.0,
    brace_gap: float | None = None,
    label_size: float = 0.0,
    label_lines: int = 1,
) -> Frame:
    """Lay out ``natural`` with ``mark_room`` points under the axis and, if ``brace_gap`` is
    given, a strip for braces and their names (``label_lines`` lines of text) below the shaded
    regions.

    The strip is inside the plot, so the figure needs no extra margin under it: its height in
    points is the gap, a brace, its name and a pad, converted to data units with the plot
    height of the canvas.
    """
    low, high = natural
    brace_room = (
        0.0
        if brace_gap is None
        else brace_gap + BRACE_DEPTH_PT + BRACE_LABEL_PAD_PT + LABEL_LINE * label_size * label_lines
    )
    reserved = mark_room + brace_room
    plot_points = size[1] * POINTS_PER_INCH * PLOT_HEIGHT_SHARE
    unit = (high - low) / (plot_points - reserved)
    fill_low = low - mark_room * unit
    return Frame(
        y_range=(low - reserved * unit, high),
        natural_low=low,
        fill_low=fill_low,
        brace_y=None if brace_gap is None else fill_low - (brace_gap - BRACE_BASE_PT) * unit,
        unit=unit,
    )


def region_brace(start: float, end: float, y: float, text: str, *, layer_id: str) -> SpanBraceLayer:
    """A brace exactly spanning ``start`` to ``end`` at height ``y``, opening upward to the
    region above it, with its name below the tip."""
    return SpanBraceLayer((start, y), (end, y), text, side="below", id=layer_id, z_index=8)


def new_canvas(
    theme: PlotTheme,
    *,
    x_range: Range,
    y_range: Range,
    x_label: str,
    y_label: str,
    title: str | None,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """An empty canvas in ``theme`` with the coordinate ranges and the title."""
    spec = CanvasSpec(
        x_range=x_range,
        y_range=y_range,
        width=size[0],
        height=size[1],
        dpi=dpi,
        x_label=x_label,
        y_label=y_label,
        title=title,
    )
    return Canvas(spec, theme=theme.to_mosaickit(), config=theme.mosaickit_config())


def nudge_labels(layers: Iterable[Layer], nudges: Mapping[str, Nudge]) -> tuple[Layer, ...]:
    """``layers`` with each label moved by its group's default nudge from the settings."""
    result: list[Layer] = []
    for layer in layers:
        group = label_group(layer)
        nudge = nudges.get(group) if group is not None else None
        if nudge is not None:
            current: Nudge | None = getattr(layer, "nudge", None)
            if current is not None:
                nudge = Nudge(current.dx + nudge.dx, current.dy + nudge.dy)
            layer = replace(layer, nudge=nudge)
        result.append(layer)
    return tuple(result)


def resolve_theme(theme: PlotTheme | None) -> PlotTheme:
    """The theme given, else the active configuration's, else the built-in default."""
    return theme or default_theme()


def curve(
    points: Sequence[Point], *, layer_id: str, role: str, model: object | None = None
) -> PathLayer:
    """A main curve through ``points``."""
    return PathLayer(tuple(points), id=layer_id, role=role, model=model, z_index=2)


def curve_name(curve_layer: PathLayer, text: str, *, at: float = 1.0) -> PointLabelLayer:
    """The curve's name beside the point ``at`` of the way along it (1 is its right-most end).

    mosaickit places the text next to that point where it covers no line, marker or text; give
    curves that end close together different ``at`` values to name them apart.
    """
    ordered = sorted(curve_layer.path)
    anchor = ordered[min(len(ordered) - 1, max(0, round(at * (len(ordered) - 1))))]
    return PointLabelLayer(
        anchor, text, id=f"{curve_layer.id}.label", role=curve_layer.role, z_index=7
    )


def guide(start: Point, end: Point, *, layer_id: str) -> PathLayer:
    """A dashed guide line between two points."""
    return PathLayer((start, end), id=layer_id, role="micro.guide", z_index=3)


DASHED_CURVE_ROLES = frozenset({"micro.curve.fixed", "micro.curve.average.fixed"})
"""Curve roles drawn dashed: a guide on top of one of these is still drawn."""
COVER_TOLERANCE = 1e-9
"""Relative distance within which a guide counts as lying on a curve."""


def _on_segment(point: Point, a: Point, b: Point) -> bool:
    """Whether ``point`` lies on the straight segment from ``a`` to ``b``."""
    scale = max(1.0, *(abs(v) for v in (*a, *b)))
    cross = (b[0] - a[0]) * (point[1] - a[1]) - (b[1] - a[1]) * (point[0] - a[0])
    length = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
    if abs(cross) / length > COVER_TOLERANCE * scale:
        return False
    low_x, high_x = sorted((a[0], b[0]))
    low_y, high_y = sorted((a[1], b[1]))
    slack = COVER_TOLERANCE * scale
    return (
        low_x - slack <= point[0] <= high_x + slack and low_y - slack <= point[1] <= high_y + slack
    )


def drop_covered_guides(layers: Iterable[Layer]) -> list[Layer]:
    """``layers`` without the dashed guides that lie entirely on a solid straight curve piece.

    A dashed guide drawn along a solid line only adds noise (the price line carrying a dashed
    level guide, say); the axis mark that names the level is a separate layer and stays.
    """
    items = list(layers)
    solid = [
        layer.path
        for layer in items
        if isinstance(layer, PathLayer)
        and layer.role.startswith("micro.curve")
        and layer.role not in DASHED_CURVE_ROLES
    ]
    kept: list[Layer] = []
    for layer in items:
        if isinstance(layer, PathLayer) and layer.role == "micro.guide" and len(layer.path) == 2:
            a, b = layer.path
            if any(
                _on_segment(a, p, q) and _on_segment(b, p, q)
                for path in solid
                for p, q in zip(path, path[1:], strict=False)
            ):
                continue
        kept.append(layer)
    return kept


def drop_line(x: float, y: float, *, layer_id: str, floor: float = 0.0) -> PathLayer:
    """A dashed guide from the point ``(x, y)`` straight down (or up) to the axis at ``floor``."""
    return guide((x, floor), (x, y), layer_id=layer_id)


def axis_mark(axis: str, value: float, label: str, *, layer_id: str) -> AxisMarkLayer:
    """A math symbol (``L_1``) beside an axis at ``value``."""
    return AxisMarkLayer(axis, value, label, math=True, id=layer_id)


def dot(point: Point, *, layer_id: str) -> MarkerLayer:
    """A marked point."""
    return MarkerLayer((point,), id=layer_id, role="micro.point", z_index=6)


def region(
    polygon: Sequence[Point], *, layer_id: str, shade: str, model: object | None = None
) -> FillLayer:
    """A shaded region; ``shade`` is ``light``, ``mid`` or ``dark``."""
    return FillLayer(
        tuple(polygon), id=layer_id, role=f"micro.region.{shade}", model=model, z_index=-5
    )


def region_name(layer_id: str, text: str, short_text: str | None = None) -> RegionLabelLayer:
    """Name the filled region ``layer_id`` inside it, by its short name, or by a callout."""
    return RegionLabelLayer(
        layer_id,
        text,
        short_text=short_text,
        placement="auto",
        id=f"{layer_id}.label",
        role="micro.annotation",
        z_index=8,
    )


__all__ = [
    "FIGURE_DPI",
    "FIGURE_SIZE",
    "MARGIN",
    "BRACE_DEPTH_PT",
    "Frame",
    "Texts",
    "axis_mark",
    "curve",
    "curve_name",
    "dot",
    "drop_covered_guides",
    "drop_line",
    "frame_for",
    "guide",
    "new_canvas",
    "nudge_labels",
    "pad_range",
    "region",
    "region_brace",
    "region_name",
    "resolve_theme",
]
