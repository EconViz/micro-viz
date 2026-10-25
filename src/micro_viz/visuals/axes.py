"""Axes, axis titles and the origin, drawn like every EconViz manual figure."""

from __future__ import annotations

from mosaickit import ArrowPlacement, AxisSpec, Layer, TextLayer, build_axes

TITLE_GAP_PT = 6.0
"""Gap in points between an arrow tip and its axis title."""

ORIGIN_OFFSET_PT = (-7.0, -7.0)
"""Offset in points of the origin label from the crossing of the axes."""


def is_symbol(label: str) -> bool:
    """Single letters (``p``, ``Q``) and ``$...$`` titles are set as math; words stay upright."""
    is_math = len(label) > 1 and label.startswith("$") and label.endswith("$")
    return is_math or (len(label) == 1 and label.isalpha())


def axis_title_layers(
    x_max: float, y_max: float, *, x_label: str, y_label: str
) -> tuple[TextLayer, ...]:
    """Axis titles past the arrow tips: y above its arrow, x to the right of its arrow."""
    layers: list[TextLayer] = []
    if y_label:
        layers.append(
            TextLayer(
                (0.0, float(y_max)),
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
                (float(x_max), 0.0),
                x_label,
                id="axes.x.label",
                role="axes",
                offset=(TITLE_GAP_PT, 0) if symbol else (0, -TITLE_GAP_PT),
                anchor="left" if symbol else "top-right",
                math=symbol,
            )
        )
    return tuple(layers)


def axes_layers(
    x_range: tuple[float, float],
    y_range: tuple[float, float],
    *,
    x_label: str,
    y_label: str,
    arrows: bool = True,
    origin_label: str | None = "0",
) -> tuple[Layer, ...]:
    """Both axes with arrows, their titles and (unless ``None``) the origin label."""
    arrow = ArrowPlacement.END if arrows else None
    layers = list(build_axes(AxisSpec(x_range, arrow=arrow), AxisSpec(y_range, arrow=arrow)))
    layers.extend(axis_title_layers(x_range[1], y_range[1], x_label=x_label, y_label=y_label))
    if origin_label:
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


__all__ = ["axes_layers", "axis_title_layers", "is_symbol"]
