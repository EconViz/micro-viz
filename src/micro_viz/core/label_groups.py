"""Shared label groups used by theme nudges.

``[micro.label.<group>]`` moves every label of a group by default; a label named in
``[figure.<file>.label."<id>"]`` is moved by that instead (mosaickit applies it when the
figure is saved). The groups follow what a label names:

``point``
    Labelled dots: the maximum-product point, the AP = MP point and the like.
``curve``
    Curves named beside their end: ``TP``, ``AP``, ``MP`` and the curves of later figures.
``region``
    Names inside shaded regions, including those drawn as a callout.
``mark``
    Price lines, quantity marks and the other guides that carry a value.
``annotation``
    Everything else that is text.

Axis titles, the origin and the axis marks (``L_1``, ``Q^*``) belong to no group and cannot
be nudged.
"""

from __future__ import annotations

from mosaickit import (
    AxisMarkLayer,
    AxisNoteLayer,
    BraceLayer,
    Layer,
    PointLabelLayer,
    RegionLabelLayer,
    SpanBraceLayer,
    TextLayer,
)

LABEL_GROUPS = ("point", "curve", "region", "mark", "annotation")
"""The label groups, in the order of ``[micro.label.<group>]``."""

LABEL_SIDES = ("top", "bottom", "left", "right")
"""The directions of a nudge: ``top``, ``bottom``, ``left`` and ``right`` as in mosaickit."""

CURVE_ROLE = "micro.curve"
POINT_ROLE = "micro.point"
MARK_ROLE = "micro.mark"


def _under(role: str, prefix: str) -> bool:
    return role == prefix or role.startswith(f"{prefix}.")


def label_group(layer: Layer) -> str | None:
    """The group of ``layer``'s label, or ``None`` for one that takes no default nudge."""
    if isinstance(layer, (AxisMarkLayer, AxisNoteLayer)):
        return None
    if isinstance(layer, RegionLabelLayer):
        return "region"
    if isinstance(layer, PointLabelLayer):
        if _under(layer.role, CURVE_ROLE):
            return "curve"
        if _under(layer.role, POINT_ROLE):
            return "point"
        if _under(layer.role, MARK_ROLE):
            return "mark"
        return "annotation"
    if isinstance(layer, TextLayer):
        return None if layer.role == "axes" or layer.id.startswith("axes.") else "annotation"
    if isinstance(layer, (BraceLayer, SpanBraceLayer)):
        return "annotation"
    return None


__all__ = ["LABEL_GROUPS", "LABEL_SIDES", "label_group"]
