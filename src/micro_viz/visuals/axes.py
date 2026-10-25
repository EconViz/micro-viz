"""Axes, axis titles and the origin, drawn like every EconViz manual figure."""

from __future__ import annotations

from mosaickit import ArrowPlacement, ArrowStyle, Layer, PathLayer, Stroke, TextLayer

TITLE_GAP_PT = 6.0
"""Gap in points between an arrow tip and its axis title."""

ORIGIN_OFFSET_PT = (-7.0, -7.0)
"""Offset in points of the origin label from the crossing of the axes."""

BREAK_SHARE = 0.04
"""Where an axis break sits, as a share of the axis length from the origin."""
BREAK_HALF_WIDTH = 0.012
"""Half the width of an axis break, as a share of the other axis' length."""
BREAK_SLOPE = 0.5
"""Rise of an axis-break stroke per unit of its half width, in share of the axis length."""


def is_symbol(label: str) -> bool:
    """Single letters (``p``, ``Q``) and ``$...$`` titles are set as math; words stay upright."""
    is_math = len(label) > 1 and label.startswith("$") and label.endswith("$")
    return is_math or (len(label) == 1 and label.isalpha())


def axis_title_layers(
    x_max: float,
    y_max: float,
    *,
    x_label: str,
    y_label: str,
    origin: tuple[float, float] = (0.0, 0.0),
) -> tuple[TextLayer, ...]:
    """Axis titles past the arrow tips: y above its arrow, x to the right of its arrow."""
    layers: list[TextLayer] = []
    if y_label:
        layers.append(
            TextLayer(
                (origin[0], float(y_max)),
                y_label,
                id="axes.y.label",
                role="axes",
                offset=(0, TITLE_GAP_PT),
                anchor="bottom",
                math=is_symbol(y_label),
            )
        )
    if x_label:
        symbol = is_symbol(x_label)
        # A symbol sits right of the tip; a word would run off the figure there, so it
        # ends at the tip, under the arrow.
        layers.append(
            TextLayer(
                (float(x_max), origin[1]),
                x_label,
                id="axes.x.label",
                role="axes",
                offset=(TITLE_GAP_PT, 0) if symbol else (0, -TITLE_GAP_PT),
                anchor="left" if symbol else "top-right",
                math=symbol,
            )
        )
    return tuple(layers)


def _axis(
    layer_id: str, start: tuple[float, float], end: tuple[float, float], arrow: bool
) -> Layer:
    return PathLayer(
        (start, end),
        id=layer_id,
        role="axes",
        stroke=Stroke(arrow=ArrowStyle.TRIANGLE) if arrow else None,
        arrow_placement=ArrowPlacement.END,
        clip=False,
    )


def axes_layers(
    x_range: tuple[float, float],
    y_range: tuple[float, float],
    *,
    x_label: str,
    y_label: str,
    arrows: bool = True,
    origin_label: str | None = "0",
    origin: tuple[float, float] | None = None,
) -> tuple[Layer, ...]:
    """Both axes with arrows, their titles and (unless ``None``) the origin label.

    The axes cross at ``origin``, by default at the lower-left corner when the ranges start
    at zero or below, and at zero otherwise. A crossing that is not at zero (a range that
    starts above zero) is marked with an axis break and carries no origin label.
    """
    x0, x1 = x_range
    y0, y1 = y_range
    cross = origin if origin is not None else (max(x0, min(0.0, x1)), max(y0, min(0.0, y1)))
    layers: list[Layer] = [
        _axis("axes.x", (x0, cross[1]), (x1, cross[1]), arrows),
        _axis("axes.y", (cross[0], y0), (cross[0], y1), arrows),
    ]
    layers.extend(axis_title_layers(x1, y1, x_label=x_label, y_label=y_label, origin=cross))
    broken_y = y0 > 0.0
    broken_x = x0 > 0.0
    if broken_y:
        layers.extend(_axis_break("y", cross, x_range, y_range))
    if broken_x:
        layers.extend(_axis_break("x", cross, x_range, y_range))
    if origin_label and not (broken_x or broken_y) and cross == (0.0, 0.0):
        layers.append(
            TextLayer(
                (0.0, 0.0),
                origin_label,
                id="axes.origin.label",
                role="axes",
                offset=ORIGIN_OFFSET_PT,
                anchor="right",
            )
        )
    return tuple(layers)


def _axis_break(
    axis: str,
    cross: tuple[float, float],
    x_range: tuple[float, float],
    y_range: tuple[float, float],
) -> tuple[Layer, ...]:
    """Two short slanted strokes across an axis near the origin: the scale starts above zero."""
    width = x_range[1] - x_range[0]
    height = y_range[1] - y_range[0]
    layers: list[Layer] = []
    for index, offset in enumerate((-1.0, 1.0)):
        if axis == "y":
            y = cross[1] + height * (BREAK_SHARE + offset * BREAK_SHARE / 3)
            half = width * BREAK_HALF_WIDTH
            points = (
                (cross[0] - half, y - height * BREAK_SLOPE * BREAK_HALF_WIDTH),
                (cross[0] + half, y + height * BREAK_SLOPE * BREAK_HALF_WIDTH),
            )
        else:
            x = cross[0] + width * (BREAK_SHARE + offset * BREAK_SHARE / 3)
            half = height * BREAK_HALF_WIDTH
            points = (
                (x - width * BREAK_SLOPE * BREAK_HALF_WIDTH, cross[1] - half),
                (x + width * BREAK_SLOPE * BREAK_HALF_WIDTH, cross[1] + half),
            )
        layers.append(PathLayer(points, id=f"axes.{axis}.break.{index}", role="axes", clip=False))
    return tuple(layers)


__all__ = ["axes_layers", "axis_title_layers", "is_symbol"]
