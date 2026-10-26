"""Depiction of braces and the figure title."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mosaickit import (
    BraceLayer,
    SpanBraceLayer,
)
from mosaickit.rendering.matplotlib.text_layout import glyph_weight
from mosaickit.themes import resolve

from micro_viz.animation.depict._labels import _Labels
from micro_viz.animation.depict._support import TITLE_RAISE, _brace_outline
from micro_viz.visuals.common import BRACE_BASE_PT, BRACE_DEPTH_PT

if TYPE_CHECKING:
    from kinetickit.scene import Node


class _Braces(_Labels):
    """Depiction of braces and the figure title."""

    # -- braces -----------------------------------------------------------------------

    def _brace(self, layer: BraceLayer) -> list[Node]:
        from kinetickit.geometry.two_d import Path2D, Vec2
        from kinetickit.scene import PathNode2D

        if layer.axis != "x":
            self.skipped.append(f"{layer.id} (BraceLayer on the y axis)")
            return []
        left = self.world((layer.start, self.y_range[0])).x
        right = self.world((layer.end, self.y_range[0])).x
        low, high = min(left, right), max(left, right)
        top = -self.stage.brace_depth
        radius = self.stage.brace_height / 2
        middle = (low + high) / 2
        outline = _brace_outline(low, high, top, radius)
        depth = 2 * radius
        style = self.style(layer).stroke
        width = float(style.width) if style and style.width is not None else 1.0
        nodes: list[Node] = [
            PathNode2D(
                id=layer.id,
                path=Path2D.polyline(outline),
                color=self.color(style.color) if style and style.color else None,
                width=width,
                z=layer.z_index,
            )
        ]
        if layer.label:
            nodes.extend(
                self._text_node(
                    f"{layer.id}.label",
                    layer.label,
                    layer,
                    Vec2(middle, top - depth),
                    "top",
                    (0.0, -self.stage.gutter / 2),
                    math_text=layer.math,
                )
            )
        return nodes

    def _span_brace(self, layer: SpanBraceLayer) -> list[Node]:
        from kinetickit.geometry.two_d import Path2D, Vec2
        from kinetickit.scene import PathNode2D

        (x0, y0), (x1, y1) = layer.start, layer.end
        if y0 != y1:
            self.skipped.append(f"{layer.id} (SpanBraceLayer on a vertical span)")
            return []
        left, right = self.world((x0, y0)), self.world((x1, y1))
        low, high = min(left.x, right.x), max(left.x, right.x)
        below = layer.side == "below"
        direction = -1.0 if below else 1.0
        base = left.y + direction * BRACE_BASE_PT
        radius = BRACE_DEPTH_PT / 2
        outline = _brace_outline(low, high, base, radius)
        if not below:
            outline = [Vec2(point.x, 2 * base - point.y) for point in outline]
        style = self.style(layer).stroke
        width = float(style.width) if style and style.width is not None else 1.0
        nodes: list[Node] = [
            PathNode2D(
                id=layer.id,
                path=Path2D.polyline(outline),
                color=self.color(style.color) if style and style.color else None,
                width=width,
                z=layer.z_index,
            )
        ]
        if layer.label:
            tip = base + direction * BRACE_DEPTH_PT
            nodes.extend(
                self._text_node(
                    f"{layer.id}.label",
                    layer.label,
                    layer,
                    Vec2((low + high) / 2, tip),
                    "top" if below else "bottom",
                    (0.0, direction * self.stage.gutter / 2),
                    math_text=layer.math,
                )
            )
        return nodes

    # -- figure -----------------------------------------------------------------------

    def title(self) -> list[Node]:
        """The figure title above the plot area, if the canvas has one."""
        from kinetickit.geometry.two_d import Vec2
        from kinetickit.scene import Text2D

        title = self.canvas.spec.title
        if not title:
            return []
        style = resolve(self.canvas.theme, "title", fallback_category="text").text
        size = float(style.size) if style and style.size else self.stage.title_size
        slot = style.font if style and style.font else "sans"
        asset = self.typography.asset(
            title, slot, size, glyph_weight(style.weight if style else None), False
        )
        probe = Text2D(id="title", asset=asset, position=Vec2(0.0, 0.0)).bounds()
        if probe is None:
            return []
        center = (probe.min.x + probe.max.x) / 2
        return [
            Text2D(
                id="micro.title",
                asset=asset,
                position=Vec2(self.width / 2 - center, self.height + TITLE_RAISE - probe.min.y),
                color=self.color(style.color) if style and style.color else None,
            )
        ]
