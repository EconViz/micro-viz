"""The depictor and the functions that run it over layers."""

from __future__ import annotations

import warnings
from collections.abc import Sequence
from dataclasses import replace
from typing import TYPE_CHECKING

from mosaickit import (
    AxisMarkLayer,
    BraceLayer,
    FillLayer,
    Layer,
    MarkerLayer,
    PathLayer,
    PointLabelLayer,
    RegionLabelLayer,
    SpanBraceLayer,
    TextLayer,
)

from micro_viz.animation.depict._braces import _Braces

if TYPE_CHECKING:
    from kinetickit.scene import Node


class Depictor(_Braces):
    """Turns the layers of one canvas into kinetickit nodes on a :class:`Stage`."""

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
