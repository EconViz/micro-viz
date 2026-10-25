"""Depict mosaickit layers as kinetickit nodes (public fields only).

The stage maps data coordinates to the plot area in points with y up, so a node's position is
a point of the figure. Every node's id derives from the layer's stable id, which is what lets
kinetickit match a layer between two frames and animate the change.
"""

from __future__ import annotations

import importlib
import math
import re
import warnings
from collections.abc import Iterable, Sequence
from dataclasses import replace
from functools import lru_cache
from pathlib import Path as FilePath
from typing import TYPE_CHECKING, Any

from mosaickit import (
    AxisMarkLayer,
    BraceLayer,
    Canvas,
    DashStyle,
    FillLayer,
    GroupLayer,
    Layer,
    MarkerLayer,
    PathLayer,
    PointLabelLayer,
    RegionLabelLayer,
    SpanBraceLayer,
    StyleBundle,
    TextLayer,
)
from mosaickit.rendering.matplotlib.text_layout import glyph_weight
from mosaickit.scene.text import TEXT_ANCHORS
from mosaickit.styles import ArrowPlacement
from mosaickit.themes import resolve

from micro_viz.animation.stage import POINTS_PER_INCH, Stage
from micro_viz.visuals.common import BRACE_BASE_PT, BRACE_DEPTH_PT

if TYPE_CHECKING:
    from kinetickit.scene import Node

Point = tuple[float, float]
GENERIC_SLOTS = ("sans", "serif", "mono")
FONT_FAMILIES = {"sans": "sans-serif", "serif": "serif", "mono": "monospace"}
"""Matplotlib family of each generic slot, used when no font file is configured."""
MARKER_SCALE = 0.55
"""Point2D size per point of marker diameter (kinetickit sizes a dot by half its extent)."""
ITALIC_CAPITAL_A = 0x1D434
ITALIC_SMALL_A = 0x1D44E
ITALIC_PLANCK = 0x210E  # the Unicode hole of Mathematical Italic small h
POINT_LABEL_OFFSET = (6.0, 6.0)
"""Offset in points of a point's name from the point: up and to the right."""
CURVE_NAME_OFFSET = (6.0, 0.0)
"""Offset in points of a curve's name from the curve's end: to the right."""
TITLE_RAISE = 14.0
"""Height in points of a figure title above the plot area."""


def _color(value: Any, alpha: float | None = None, palette: Any = None) -> Any:
    from kinetickit.interpolation import Color

    channels = (palette[value] if isinstance(value, str) else value).channels
    return Color(channels[0], channels[1], channels[2], channels[3] if alpha is None else alpha)


def _flatten(layers: Iterable[Layer], z: float = 0.0) -> Iterable[Layer]:
    for layer in layers:
        if not layer.visible:
            continue
        if isinstance(layer, GroupLayer):
            yield from _flatten(layer.children, z + layer.z_index)
        else:
            yield replace(layer, z_index=z + layer.z_index)


ARC_STEPS = 6
"""Straight pieces per quarter circle of a brace."""


def _arc(centre: Point, radius: float, start: float, end: float) -> list[Point]:
    return [
        (
            centre[0] + radius * math.cos(start + (end - start) * index / ARC_STEPS),
            centre[1] + radius * math.sin(start + (end - start) * index / ARC_STEPS),
        )
        for index in range(ARC_STEPS + 1)
    ]


def _brace_outline(low: float, high: float, top: float, radius: float) -> list[Any]:
    """A curly brace opening upward: the ends turn up and the middle points down."""
    from kinetickit.geometry.two_d import Vec2

    middle = (low + high) / 2
    half = _arc((low + radius, top), radius, math.pi, 1.5 * math.pi)
    half += _arc((middle - radius, top - 2 * radius), radius, 0.5 * math.pi, 0.0)
    mirrored = [(low + high - x, y) for x, y in reversed(half)]
    return [Vec2(x, y) for x, y in half + mirrored]


_COMMAND = re.compile(r"\\[A-Za-z]+|[A-Za-z]")


def _italic_letters(latex: str, coverage: frozenset[int]) -> str:
    """Set single letters in the Mathematical Italic alphabet where the font has it, as TeX does."""

    def replace_letter(match: re.Match[str]) -> str:
        value = match.group(0)
        if len(value) != 1:
            return value
        if value == "h":
            target = ITALIC_PLANCK
        elif value.isupper():
            target = ITALIC_CAPITAL_A + ord(value) - ord("A")
        else:
            target = ITALIC_SMALL_A + ord(value) - ord("a")
        return chr(target) if target in coverage else value

    return _COMMAND.sub(replace_letter, latex)


class Typography:
    """GlyphKit text assets in the canvas's configured fonts (DejaVu when none are set)."""

    def __init__(self, canvas: Canvas) -> None:
        self.fonts = canvas.config.fonts
        self.math_font = canvas.config.math_font
        self._engines: dict[str, Any] = {}
        self._coverage: frozenset[int] = frozenset()

    def _paths(self, slot: str) -> tuple[FilePath, ...]:
        configured = getattr(self.fonts, slot, None) if self.fonts is not None else None
        if configured:
            return tuple(configured)
        font_manager = importlib.import_module("matplotlib.font_manager")
        family = FONT_FAMILIES[slot]
        return tuple(
            dict.fromkeys(
                FilePath(
                    font_manager.findfont(font_manager.FontProperties(family=family, weight=w))
                )
                for w in ("normal", "bold")
            )
        )

    def _typography(self, slot: str) -> Any:
        if slot not in self._engines:
            from glyphkit import FontLibrary, FontSource
            from kinetickit.integrations.glyphkit import GlyphKitTypography

            sources = tuple(FontSource.path(path) for path in self._paths(slot))
            library = FontLibrary.from_sources(sources)
            families = tuple(dict.fromkeys(face.family for face in library.manifest().faces))
            self._engines[slot] = GlyphKitTypography(library, families=families, embed=False)
        return self._engines[slot]

    def _math(self) -> Any:
        if "math" not in self._engines and self.math_font is not None:
            from glyphkit import FontLibrary, FontSource
            from kinetickit.integrations.glyphkit import GlyphKitTypography

            library = FontLibrary.from_sources((FontSource.path(self.math_font.path),))
            families = tuple(dict.fromkeys(face.family for face in library.manifest().faces))
            self._engines["math"] = GlyphKitTypography(library, families=families, embed=False)
            face = next((item for item in library.faces if item.has_math), None)
            self._coverage = face.coverage if face is not None else frozenset()
        return self._engines.get("math")

    @lru_cache(maxsize=512)  # noqa: B019
    def asset(self, text: str, slot: str, size: float, weight: int, math: bool) -> Any:
        if math and self.math_font is not None:
            engine = self._math()
            latex = (
                _italic_letters(text.strip("$"), self._coverage)
                if self.math_font.italic
                else text.strip("$")
            )
            return engine.math(latex, size=size)
        plain = text.strip("$") if math else text
        return self._typography(slot).asset(plain, size=size, weight=weight)


class Depictor:
    """Turns the layers of one canvas into kinetickit nodes on a :class:`Stage`."""

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

    # -- layers -----------------------------------------------------------------------

    def depict(self, layer: Layer) -> list[Node]:
        """The nodes that draw ``layer``; a hidden layer's nodes are fully transparent.

        A layer kind without a depiction gives no nodes (and is reported by ``skipped``).
        """
        nodes = self._depict(layer)
        if layer.visible:
            return nodes
        return [replace(node, opacity=0.0) for node in nodes]

    def _depict(self, layer: Layer) -> list[Node]:
        if isinstance(layer, PathLayer):
            return self._path(layer)
        if isinstance(layer, FillLayer):
            return self._fill(layer)
        if isinstance(layer, MarkerLayer):
            return self._markers(layer)
        if isinstance(layer, AxisMarkLayer):
            return self._axis_mark(layer)
        if isinstance(layer, TextLayer):
            return self._text_layer(layer)
        if isinstance(layer, PointLabelLayer):
            return self._point_label(layer)
        if isinstance(layer, RegionLabelLayer):
            return self._region_label(layer)
        if isinstance(layer, BraceLayer):
            return self._brace(layer)
        if isinstance(layer, SpanBraceLayer):
            return self._span_brace(layer)
        self.skipped.append(f"{layer.id} ({type(layer).__name__})")
        return []

    def layers(self, canvas: Canvas | None = None) -> list[Layer]:
        """The drawable layers of ``canvas`` (default this canvas), lowest z first."""
        scene = (canvas or self.canvas).snapshot()
        return sorted(_flatten(scene.layers), key=lambda item: item.z_index)

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


def depict_all(depictor: Depictor, layers: Sequence[Layer]) -> list[Node]:
    """Every node of ``layers`` plus the title."""
    nodes: list[Node] = []
    for layer in layers:
        nodes.extend(depictor.depict(layer))
    return nodes


def warn_skipped(depictor: Depictor) -> None:
    """Warn once about layers that have no animated depiction."""
    if depictor.skipped:
        unique = ", ".join(sorted(set(depictor.skipped)))
        warnings.warn(f"animated SVG leaves out: {unique}", stacklevel=3)
