"""Movement arrows: one place decides how a change of a curve is drawn.

A parallel shift is a straight, solid arrow from a point of the old curve to the new curve,
along an axis. A rotation (a change of slope) is a separate case: mosaickit draws only straight
arrows, so the rotation arrow joins the two curves at their far end.
"""

from __future__ import annotations

from mosaickit import ArrowLayer

from micro_viz.visuals.common import Point


def parallel_arrow(
    start: Point, end: Point, *, layer_id: str, label: str | None = None
) -> ArrowLayer:
    """A solid arrow for a parallel shift, from the old curve (``start``) to the new (``end``)."""
    return ArrowLayer(start, end, label=label, id=layer_id, role="micro.arrow", z_index=5)


def rotation_arrow(start: Point, end: Point, *, layer_id: str) -> ArrowLayer:
    """A solid arrow for a rotation, joining the old curve to the new one at their far end."""
    return ArrowLayer(start, end, id=layer_id, role="micro.arrow", z_index=5)
