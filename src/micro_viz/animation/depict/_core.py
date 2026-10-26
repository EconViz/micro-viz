"""Coordinates, styles and layer lookup of the depictor."""

from __future__ import annotations

from typing import Any

from mosaickit import (
    Canvas,
    DashStyle,
    Layer,
    StyleBundle,
)
from mosaickit.themes import resolve

from micro_viz.animation.depict._support import Point, _color, _flatten
from micro_viz.animation.depict.typography import Typography
from micro_viz.animation.stage import POINTS_PER_INCH, Stage


class _Core:
    """Coordinates, styles and layer lookup shared by the depiction classes."""

    def __init__(self, canvas: Canvas, stage: Stage) -> None:
        spec = canvas.spec
        self.canvas = canvas
        self.stage = stage
        self.width = spec.width * POINTS_PER_INCH - stage.left - stage.right
        self.height = spec.height * POINTS_PER_INCH - stage.top - stage.bottom
        self.x_range = spec.x_range
        self.y_range = spec.y_range
        self.typography = Typography(canvas)
        self.skipped: list[str] = []

    def color(self, value: Any, alpha: float | None = None) -> Any:
        """A kinetickit colour for a mosaickit colour or palette name."""
        return _color(value, alpha, self.canvas.config.palette)

    # -- coordinates ------------------------------------------------------------------

    def world(self, point: Point) -> Any:
        from kinetickit.geometry.two_d import Vec2

        x0, x1 = self.x_range
        y0, y1 = self.y_range
        return Vec2(
            (point[0] - x0) / (x1 - x0) * self.width,
            (point[1] - y0) / (y1 - y0) * self.height,
        )

    # -- styles -----------------------------------------------------------------------

    def style(self, layer: Layer) -> StyleBundle:
        theme_style = resolve(
            self.canvas.theme,
            layer.role,
            fallback_category=layer.fallback_category,
            overrides=(self.canvas.config.role_overrides, self.canvas.role_overrides),
        )
        explicit = StyleBundle(
            **{slot: getattr(layer, name) for slot, name in layer.style_slots.items()}
        )
        return explicit.merged_over(theme_style)

    def _dash(self, dash: DashStyle | None, width: float) -> tuple[float, ...]:
        if dash == DashStyle.DASHED:
            on, off = self.stage.dash_scale
            return (on * width, off * width)
        if dash == DashStyle.DOTTED:
            on, off = self.stage.dot_scale
            return (on * width, off * width)
        if dash == DashStyle.DASHDOT:
            on, off = self.stage.dash_scale
            return (on * width, off * width, width, off * width)
        return ()

    def layers(self, canvas: Canvas | None = None) -> list[Layer]:
        """The drawable layers of ``canvas`` (default this canvas), lowest z first."""
        scene = (canvas or self.canvas).snapshot()
        return sorted(_flatten(scene.layers), key=lambda item: item.z_index)
