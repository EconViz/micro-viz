"""Depiction of text, point labels, region labels and axis marks."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mosaickit import (
    AxisMarkLayer,
    FillLayer,
    Layer,
    PointLabelLayer,
    RegionLabelLayer,
    TextLayer,
)
from mosaickit.rendering.matplotlib.text_layout import glyph_weight
from mosaickit.scene.text import TEXT_ANCHORS

from micro_viz.animation.depict._shapes import _Shapes
from micro_viz.animation.depict._support import CURVE_NAME_OFFSET, POINT_LABEL_OFFSET, Point

if TYPE_CHECKING:
    from kinetickit.scene import Node


class _Labels(_Shapes):
    """Depiction of text, point labels, region labels and axis marks."""

    # -- text -------------------------------------------------------------------------

    def _text_node(
        self,
        node_id: str,
        text: str,
        layer: Layer,
        at: Any,
        anchor: str,
        offset: Point,
        *,
        math_text: bool,
    ) -> list[Node]:
        from kinetickit.geometry.two_d import Vec2
        from kinetickit.scene import Text2D

        style = self.style(layer).text
        size = float(style.size) if style and style.size else self.stage.text_size
        slot = style.font if style and style.font else "sans"
        weight = glyph_weight(style.weight if style else None)
        asset = self.typography.asset(text, slot, size, weight, math_text)
        probe = Text2D(id=node_id, asset=asset, position=Vec2(0.0, 0.0))
        box = probe.bounds()
        if box is None:
            return []
        horizontal, vertical = TEXT_ANCHORS[anchor]
        ax = {"left": box.min.x, "center": (box.min.x + box.max.x) / 2, "right": box.max.x}[
            horizontal
        ]
        ay = {"bottom": box.min.y, "center": (box.min.y + box.max.y) / 2, "top": box.max.y}[
            vertical
        ]
        position = Vec2(at.x + offset[0] - ax, at.y + offset[1] - ay)
        color = self.color(style.color) if style and style.color else None
        node = Text2D(id=node_id, asset=asset, position=position, color=color, z=layer.z_index)
        return [node]

    def _text_layer(self, layer: TextLayer) -> list[Node]:
        total = layer.total_offset
        return self._text_node(
            layer.id,
            layer.text,
            layer,
            self.world(layer.position),
            layer.anchor,
            (total[0], total[1]),
            math_text=layer.math,
        )

    def _point_label(self, layer: PointLabelLayer) -> list[Node]:
        nudge = layer.nudge
        extra = (nudge.dx, nudge.dy) if nudge is not None else (0.0, 0.0)
        is_curve = layer.role.startswith("micro.curve")
        base = CURVE_NAME_OFFSET if is_curve else POINT_LABEL_OFFSET
        return self._text_node(
            layer.id,
            layer.text,
            layer,
            self.world(layer.point),
            "left" if is_curve else "bottom-left",
            (base[0] + extra[0], base[1] + extra[1]),
            math_text=False,
        )

    def _region_label(self, layer: RegionLabelLayer) -> list[Node]:
        polygon = layer.region
        if isinstance(polygon, str):
            fills = {item.id: item for item in self.layers() if isinstance(item, FillLayer)}
            polygon = fills[polygon].boundary if polygon in fills else ()
        if not polygon:
            return []
        xs, ys = zip(*polygon, strict=True)
        center = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
        return self._text_node(
            layer.id,
            layer.short_text or layer.text,
            layer,
            self.world(center),
            "center",
            (0.0, 0.0),
            math_text=False,
        )

    def _axis_mark(self, layer: AxisMarkLayer) -> list[Node]:
        from kinetickit.geometry.two_d import Vec2

        gap = self.stage.gutter
        if layer.axis == "x":
            at = self.world((layer.value, self.y_range[0]))
            return self._text_node(
                layer.id, layer.label, layer, at, "top", (0.0, -gap), math_text=layer.math
            )
        at = self.world((self.x_range[0], layer.value))
        return self._text_node(
            layer.id,
            layer.label,
            layer,
            Vec2(at.x, at.y),
            "right",
            (-gap, 0.0),
            math_text=layer.math,
        )
