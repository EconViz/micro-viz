"""The pixel stage an animated SVG is drawn on, and how data coordinates map onto it."""

from __future__ import annotations

from dataclasses import dataclass

POINTS_PER_INCH = 72.0
"""Logical pixels of an animated SVG are points, so styles in points carry over unchanged."""


@dataclass(frozen=True, slots=True)
class Stage:
    """Margins in points around the plot area of an animated SVG.

    The plot area is the canvas size (inches times 72) minus the margins. The defaults leave
    room for axis titles, axis marks and the braces drawn under the horizontal axis.
    """

    top: float = 36.0
    right: float = 44.0
    bottom: float = 88.0
    left: float = 56.0
    gutter: float = 8.0
    """Gap in points between an axis and a mark or name written beside it."""
    arrow_length: float = 9.0
    """Length in points of an axis arrow head."""
    arrow_half_width: float = 3.5
    """Half the width in points of an axis arrow head."""
    brace_depth: float = 40.0
    """Distance in points from the horizontal axis to a brace drawn under it."""
    brace_height: float = 8.0
    """Height in points of a brace."""
    dash_scale: tuple[float, float] = (3.7, 1.6)
    """Dash and gap of a dashed line, in line widths."""
    dot_scale: tuple[float, float] = (1.0, 1.65)
    """Dash and gap of a dotted line, in line widths."""
    seconds_per_step: float = 1.2
    """Time one step between two values of the swept parameter takes."""
    max_path_points: int = 61
    """A curve with more points is thinned to this many (ends kept), so a morph stays small."""
    text_size: float = 11.0
    """Size in points of text whose theme role sets none."""
    title_size: float = 12.0
    """Size in points of a title whose theme role sets none."""
    dot_diameter: float = 6.5
    """Diameter in points of a marker whose theme role sets none."""
