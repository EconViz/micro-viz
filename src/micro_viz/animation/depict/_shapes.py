"""Depiction of paths, fills and markers."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from mosaickit import (
    FillLayer,
    MarkerLayer,
    PathLayer,
)
from mosaickit.styles import ArrowPlacement

from micro_viz.animation.depict._core import _Core
from micro_viz.animation.depict._support import MARKER_SCALE, Point

if TYPE_CHECKING:
    from kinetickit.scene import Node


class _Shapes(_Core):
    """Depiction of paths, fills and markers."""

    def _path(self, layer: PathLayer) -> list[Node]:
        from kinetickit.geometry.two_d import Path2D
        from kinetickit.scene import PathNode2D

        style = self.style(layer).stroke
        width = float(style.width) if style and style.width is not None else 1.0
        opacity = style.opacity if style and style.opacity is not None else 1.0
        points = [self.world(point) for point in self._thin(layer.path)]
        nodes: list[Node] = [
            PathNode2D(
                id=layer.id,
                path=Path2D.polyline(points),
                color=self.color(style.color, opacity) if style and style.color else None,
                width=width,
                dash=self._dash(style.dash if style else None, width),
                cap="butt" if style and style.arrow else "round",
                z=layer.z_index,
            )
        ]
        if style is not None and style.arrow and len(points) >= 2:
            if layer.arrow_placement in (ArrowPlacement.END, ArrowPlacement.BOTH):
                nodes.append(self._arrow(layer, points[-1], points[-2], style, "end"))
            if layer.arrow_placement in (ArrowPlacement.START, ArrowPlacement.BOTH):
                nodes.append(self._arrow(layer, points[0], points[1], style, "start"))
        return nodes

    def _thin(self, path: Sequence[Point]) -> Sequence[Point]:
        limit = self.stage.max_path_points
        if len(path) <= limit:
            return path
        last = len(path) - 1
        return [path[round(index * last / (limit - 1))] for index in range(limit)]

    def _arrow(self, layer: PathLayer, tip: Any, before: Any, style: Any, tag: str) -> Node:
        from kinetickit.geometry.two_d import Path2D, Vec2
        from kinetickit.scene import Shape2D

        dx, dy = tip.x - before.x, tip.y - before.y
        norm = math.hypot(dx, dy) or 1.0
        ux, uy = dx / norm, dy / norm
        length, half = self.stage.arrow_length, self.stage.arrow_half_width
        base = Vec2(tip.x - ux * length, tip.y - uy * length)
        left = Vec2(base.x - uy * half, base.y + ux * half)
        right = Vec2(base.x + uy * half, base.y - ux * half)
        return Shape2D(
            id=f"{layer.id}.arrow.{tag}",
            path=Path2D.polygon([tip, left, right]),
            fill=self.color(style.color),
            z=layer.z_index,
        )

    def _fill(self, layer: FillLayer) -> list[Node]:
        from kinetickit.geometry.two_d import Path2D
        from kinetickit.scene import Shape2D

        style = self.style(layer)
        fill = style.fill
        if fill is None or fill.color is None:
            return []
        opacity = fill.opacity if fill.opacity is not None else 1.0
        stroke = style.stroke
        visible_edge = stroke is not None and stroke.width and stroke.color is not None
        return [
            Shape2D(
                id=layer.id,
                path=Path2D.polygon([self.world(point) for point in layer.boundary]),
                fill=self.color(fill.color),
                opacity=opacity,
                stroke=self.color(stroke.color) if visible_edge else None,
                stroke_width=float(stroke.width) if visible_edge else 0.0,
                z=layer.z_index,
            )
        ]

    def _markers(self, layer: MarkerLayer) -> list[Node]:
        from kinetickit.scene import Point2D

        marker = self.style(layer).marker
        if marker is None or marker.color is None:
            return []
        diameter = (
            math.sqrt(float(marker.size)) if marker.size is not None else self.stage.dot_diameter
        )
        return [
            Point2D(
                id=f"{layer.id}.{index}",
                position=self.world(point),
                size=diameter * MARKER_SCALE,
                color=self.color(marker.color),
                z=layer.z_index,
            )
            for index, point in enumerate(layer.points)
        ]
