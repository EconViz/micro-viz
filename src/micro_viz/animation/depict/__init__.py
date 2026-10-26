"""Depict mosaickit layers as kinetickit nodes (public fields only).

The stage maps data coordinates to the plot area in points with y up, so a node's position is
a point of the figure. Every node's id derives from the layer's stable id, which is what lets
kinetickit match a layer between two frames and animate the change.
"""

# ruff: noqa: I001

from micro_viz.animation.depict._support import (
    ARC_STEPS as ARC_STEPS,
    CURVE_NAME_OFFSET as CURVE_NAME_OFFSET,
    FONT_FAMILIES as FONT_FAMILIES,
    GENERIC_SLOTS as GENERIC_SLOTS,
    ITALIC_CAPITAL_A as ITALIC_CAPITAL_A,
    ITALIC_PLANCK as ITALIC_PLANCK,
    ITALIC_SMALL_A as ITALIC_SMALL_A,
    MARKER_SCALE as MARKER_SCALE,
    POINT_LABEL_OFFSET as POINT_LABEL_OFFSET,
    Point as Point,
    TITLE_RAISE as TITLE_RAISE,
    _arc as _arc,
    _brace_outline as _brace_outline,
    _color as _color,
    _flatten as _flatten,
)
from micro_viz.animation.depict.depictor import (
    Depictor as Depictor,
    depict_all as depict_all,
    warn_skipped as warn_skipped,
)
from micro_viz.animation.depict.typography import (
    Typography as Typography,
    _COMMAND as _COMMAND,
    _italic_letters as _italic_letters,
)
