"""Animate any micro-viz figure with kinetickit (the optional ``micro-viz[animation]`` extra).

A figure is animated through the same canvas builder that draws it: pass a *factory* that
builds the canvas for one value of the swept parameter (a shift, a price, an output level)
and the values to sweep. mosaickit draws every frame; kinetickit moves between frames,
matching layers by their stable ids, so a curve morphs into its next state and a marker
glides along it. Static figures never import this package or kinetickit.

``save_svg`` writes a native Animated SVG (vector, text outlined and embedded by GlyphKit);
``save_gif`` writes a GIF of mosaickit-rendered frames (needs the ``raster`` capability of
kinetickit, installed by the extra).
"""

from __future__ import annotations

from micro_viz.animation.export import (
    Frames,
    animation_from_canvases,
    canvases_for,
    save_gif,
    save_svg,
)
from micro_viz.animation.stage import Stage

__all__ = [
    "Frames",
    "Stage",
    "animation_from_canvases",
    "canvases_for",
    "save_gif",
    "save_svg",
]
