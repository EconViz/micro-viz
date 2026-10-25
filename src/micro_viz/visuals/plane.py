"""A small drawing kit over mosaickit for plane diagrams.

:class:`Plane` collects curves, guides, points, marks, regions and arrows of one diagram with
stable layer ids (``micro.<prefix>.<kind>.<n>``), so each figure module only states geometry.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import Canvas, CanvasGrid, PointLabelLayer

from micro_viz.theme import PlotTheme
from micro_viz.visuals.common import (
    FIGURE_DPI,
    FIGURE_SIZE,
    MARGIN,
    Point,
    Range,
    axis_mark,
    curve,
    curve_name,
    dot,
    guide,
    pad_range,
    region,
    region_name,
)
from micro_viz.visuals.competition import _finish, _start
from micro_viz.visuals.movement import parallel_arrow, rotation_arrow

PANEL = (6.0, 4.5)
"""Default size in inches of one panel of a multi-panel diagram."""


class Plane:
    """One plane diagram; call :meth:`finish` for the canvas."""

    def __init__(
        self,
        *,
        prefix: str,
        x_label: str,
        y_label: str,
        x_max: float,
        y_max: float,
        theme: PlotTheme | None = None,
        labels: Mapping[str, str] | None = None,
        title: str | None = None,
        margin: float = MARGIN,
        y_range: Range | None = None,
        size: tuple[float, float] = FIGURE_SIZE,
        dpi: int = FIGURE_DPI,
    ) -> None:
        self.prefix = prefix
        self.start = _start(
            theme=theme,
            labels=labels,
            x_symbol=x_label,
            x_label=x_label,
            y_label=y_label,
            y_text_id="competition.axis.price",
            x_max=x_max * (1 + margin),
            y_range=y_range or pad_range(0.0, y_max, margin),
            title=title,
            size=size,
            dpi=dpi,
        )
        self.x_max = x_max * (1 + margin)
        self._count: dict[str, int] = {}

    def t(self, key: str, **fields: object) -> str:
        """Built-in (or overridden) text ``key``."""
        return self.start.texts(key, **fields)

    def _id(self, kind: str) -> str:
        self._count[kind] = self._count.get(kind, 0) + 1
        return f"micro.{self.prefix}.{kind}.{self._count[kind]}"

    def line(
        self,
        points: Sequence[Point],
        name: str | None = None,
        *,
        role: str = "micro.curve.marginal",
        at: float = 1.0,
    ) -> None:
        """A curve through ``points`` named at the fraction ``at`` along it (1 = right end)."""
        ceiling = self.start.y_range[1]
        visible = [point for point in points if point[1] <= ceiling] or list(points)
        path = curve(visible, layer_id=self._id("curve"), role=role)
        self.start.layers.append(path)
        if name:
            self.start.layers.append(curve_name(path, name, at=at))

    def thin(self, points: Sequence[Point], name: str | None = None, *, at: float = 1.0) -> None:
        """A curve after a change: thin and solid."""
        self.line(points, name, role="micro.curve.after", at=at)

    def guide(self, a: Point, b: Point) -> None:
        self.start.layers.append(guide(a, b, layer_id=self._id("guide")))

    def dot(self, point: Point) -> None:
        self.start.layers.append(dot(point, layer_id=self._id("dot")))

    def xmark(self, x: float, text: str) -> None:
        self.start.layers.append(axis_mark("x", x, text, layer_id=self._id("xmark")))

    def ymark(self, y: float, text: str) -> None:
        self.start.layers.append(axis_mark("y", y, text, layer_id=self._id("ymark")))

    def point(
        self,
        x: float,
        y: float,
        *,
        xtext: str | None = None,
        ytext: str | None = None,
        name: str | None = None,
        marker: bool = True,
    ) -> None:
        """A dot with dashed guides to the axes and the given axis marks."""
        if xtext:
            self.guide((x, 0.0), (x, y))
            self.xmark(x, xtext)
        if ytext:
            self.guide((0.0, y), (x, y))
            self.ymark(y, ytext)
        if marker:
            self.dot((x, y))
        if name:
            self.start.layers.append(
                PointLabelLayer((x, y), name, id=self._id("name"), role="micro.point")
            )

    def area(
        self, polygon: Sequence[Point], name: str | None = None, *, shade: str = "mid"
    ) -> None:
        """A shaded region, optionally named inside it."""
        layer_id = self._id("area")
        self.start.layers.append(region(polygon, layer_id=layer_id, shade=shade))
        if name:
            self.start.layers.append(region_name(layer_id, name))

    def arrow(self, a: Point, b: Point, *, rotate: bool = False, label: str | None = None) -> None:
        """A solid movement arrow: straight for a shift, ``rotate`` for a slope change."""
        build = rotation_arrow if rotate else parallel_arrow
        layer = build(a, b, layer_id=self._id("arrow"))
        if label and not rotate:
            layer = parallel_arrow(a, b, layer_id=layer.id, label=label)
        self.start.layers.append(layer)

    def finish(self) -> Canvas:
        return _finish(self.start)


def linear(intercept: float, slope: float, x_max: float, x_min: float = 0.0) -> tuple[Point, Point]:
    """The segment ``y = intercept + slope x`` from ``x_min`` to ``x_max``."""
    return ((x_min, intercept + slope * x_min), (x_max, intercept + slope * x_max))


def sample(function, low: float, high: float, steps: int = 60) -> list[Point]:  # type: ignore[no-untyped-def]
    """Points ``(x, function(x))`` on an even grid from ``low`` to ``high``."""
    return [
        (low + (high - low) * i / steps, float(function(low + (high - low) * i / steps)))
        for i in range(steps + 1)
    ]


def row(cells: Sequence[Canvas]) -> CanvasGrid:
    """Panels side by side."""
    return CanvasGrid([list(cells)])


__all__ = ["PANEL", "Plane", "linear", "row", "sample"]
