"""Constants and geometry helpers shared by the depiction of layers."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import replace
from typing import Any

from mosaickit import (
    GroupLayer,
    Layer,
)

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
