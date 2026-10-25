"""Pieces every micro-viz figure is built from: canvas, texts, curves, guides and regions."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import replace

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


def curve_name(curve_layer: PathLayer, text: str) -> PointLabelLayer:
    """The curve's name beside its right-most end; mosaickit keeps it clear of everything else."""
    end = max(curve_layer.path, key=lambda point: (point[0], point[1]))
    return PointLabelLayer(
        end, text, id=f"{curve_layer.id}.label", role=curve_layer.role, z_index=7
    )


def guide(start: Point, end: Point, *, layer_id: str) -> PathLayer:
    """A dashed guide line between two points."""
    return PathLayer((start, end), id=layer_id, role="micro.guide", z_index=3)


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
    "Texts",
    "axis_mark",
    "curve",
    "curve_name",
    "dot",
    "drop_line",
    "guide",
    "new_canvas",
    "nudge_labels",
    "pad_range",
    "region",
    "region_name",
    "resolve_theme",
]
