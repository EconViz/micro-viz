"""micro-viz elements mapped to mosaickit's shared theme roles and compiled to styles.

mosaickit's shared themes (``mosaickit.themes``) give every EconViz package the same named
looks: each assigns a colour to a small set of roles plus line, marker and label scales.
:data:`ELEMENT_ROLES` is the only place that says which role each micro-viz element takes.
Sizes below are documented defaults; ``econ-viz.toml`` overrides them (see
``micro_viz.config``), and a figure never contains a colour or a font name of its own.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from types import MappingProxyType

from mosaickit import (
    Color,
    ConfigurationError,
    DashStyle,
    Fill,
    Marker,
    MathFont,
    Nudge,
    Stroke,
    StyleBundle,
    TextFonts,
    TextStyle,
    Theme,
)
from mosaickit import (
    Config as MosaicConfig,
)
from mosaickit.config import current_config
from mosaickit.themes import ThemeTokens, get_tokens

from micro_viz.i18n import text, validate_language
from micro_viz.label_groups import LABEL_GROUPS

ELEMENT_ROLES: Mapping[str, str] = MappingProxyType(
    {
        "axis": "ink",
        "label": "ink",
        "guide": "ink",
        "marker": "ink",
        "total": "secondary",
        "average": "primary",
        "marginal": "accent",
        "variable": "tertiary",
        "fixed": "muted",
        "region_light": "fill.light",
        "region_mid": "fill.mid",
        "region_dark": "fill.dark",
    }
)
"""The shared theme role of every micro-viz colour element."""

GENERIC_FONTS = ("sans", "serif", "mono")

WHITE = Color(1.0, 1.0, 1.0)
"""The canvas colour when a theme has none: EconViz figures never use a dark or clear canvas."""

CURVE_WIDTH = 3.5
"""Default width in points of a main curve (``[micro.stroke] curve``)."""
DASHED_WIDTH = 2.0
"""Default width in points of a dashed curve (``[micro.stroke] dashed``)."""
THIN_WIDTH = 1.0
"""Default width in points of axes and guide lines (``[micro.stroke] guide``)."""
MARKER_DIAMETER = 6.5
"""Default diameter in points of a marked point (``[micro.marker] diameter``)."""
REGION_OPACITY = 0.2
"""Default opacity of a shaded region (``[micro.opacity] region``)."""
LABEL_SIZE = 11.0
"""Default size in points of curve, region and point labels."""
ANNOTATION_SIZE = 10.0
"""Default size in points of annotations and guide labels."""
TITLE_SIZE = 12.0
"""Default size in points of a figure title."""


@dataclass(frozen=True, slots=True)
class PlotTheme:
    """The style inputs of every micro-viz figure, compiled to a mosaickit theme."""

    name: str
    colors: Mapping[str, str] = field(hash=False)
    background: str | None = None
    curve_width: float = CURVE_WIDTH
    dashed_width: float = DASHED_WIDTH
    guide_width: float = THIN_WIDTH
    marker_diameter: float = MARKER_DIAMETER
    region_opacity: float = REGION_OPACITY
    label_scale: float = 1.0
    # Fonts behave as in every diagram package built on mosaickit: a generic font, files
    # that replace the generic fonts, and a math font.
    font: str = "sans"
    fonts: TextFonts | None = None
    math_font: MathFont | str | os.PathLike[str] | None = None
    # The language of the built-in figure text: "en", "zh-TW" or "zh-CN".
    language: str = "en"
    # A default move for whole groups of labels (see micro_viz.label_groups).
    label_nudges: Mapping[str, Nudge] = field(default_factory=dict, hash=False)

    def __post_init__(self) -> None:
        validate_language(self.language)
        missing = sorted(set(ELEMENT_ROLES) - set(self.colors))
        if missing:
            raise ValueError(f"colors lacks the elements {', '.join(missing)}")
        for group, nudge in self.label_nudges.items():
            if group not in LABEL_GROUPS:
                raise ValueError(
                    f"label_nudges: unknown label group {group!r}; "
                    f"choose from {', '.join(LABEL_GROUPS)}"
                )
            if not isinstance(nudge, Nudge):
                raise TypeError(f"label_nudges[{group!r}] must be a mosaickit Nudge")
        if self.font not in GENERIC_FONTS:
            raise ValueError(
                f"font must be one of {', '.join(GENERIC_FONTS)}, got {self.font!r}; "
                "to use your own font files pass fonts=TextFonts(...)"
            )
        if self.fonts is not None and not isinstance(self.fonts, TextFonts):
            raise ValueError("fonts must be a mosaickit.TextFonts or None")
        math_font = self.math_font
        if isinstance(math_font, (str, os.PathLike)):
            try:
                math_font = MathFont(Path(math_font))
            except ConfigurationError as error:
                raise ValueError(f"math_font: {error}") from None
        elif math_font is not None and not isinstance(math_font, MathFont):
            raise ValueError("math_font must be a mosaickit.MathFont or a font file path")
        object.__setattr__(self, "math_font", math_font)
        object.__setattr__(self, "colors", MappingProxyType(dict(self.colors)))

    @classmethod
    def from_tokens(cls, tokens: ThemeTokens, **overrides: object) -> PlotTheme:
        """The theme of a shared mosaickit theme; keyword arguments override fields."""
        values: dict[str, object] = {
            "name": tokens.name,
            "colors": {
                element: _color(tokens.colors[role]) for element, role in ELEMENT_ROLES.items()
            },
            "background": tokens.colors["background"],
            "curve_width": CURVE_WIDTH * tokens.line_scale,
            "dashed_width": DASHED_WIDTH * tokens.line_scale,
            "guide_width": THIN_WIDTH * tokens.line_scale,
            "marker_diameter": MARKER_DIAMETER * tokens.marker_scale,
            "label_scale": tokens.label_scale,
        }
        values.update(overrides)
        return cls(**values)  # type: ignore[arg-type]

    @classmethod
    def from_palette(cls, palette: str, **overrides: object) -> PlotTheme:
        """The theme of the shared mosaickit theme called ``palette``."""
        return cls.from_tokens(get_tokens(palette), **overrides)

    def text(self, key: str, **fields: object) -> str:
        """Built-in figure text ``key`` in this theme's language."""
        return text(key, self.language, **fields)

    def mosaickit_config(self) -> MosaicConfig:
        """mosaickit's current settings with this theme's font files and math font."""
        base = current_config()
        if self.fonts is None and self.math_font is None:
            return base
        return replace(
            base,
            fonts=self.fonts if self.fonts is not None else base.fonts,
            math_font=self.math_font if self.math_font is not None else base.math_font,
        )

    def to_mosaickit(self) -> Theme:
        """Compile this theme to public mosaickit styles."""
        c = self.colors
        size = self.label_scale
        label = TextStyle(color=c["label"], size=LABEL_SIZE * size)
        note = TextStyle(color=c["label"], size=ANNOTATION_SIZE * size)
        diameter = self.marker_diameter
        dot = Marker(color=c["marker"], size=diameter**2, edge_color=c["marker"], edge_width=0)

        def curve(element: str, dash: DashStyle = DashStyle.SOLID) -> StyleBundle:
            width = self.curve_width if dash == DashStyle.SOLID else self.dashed_width
            return StyleBundle(
                stroke=Stroke(color=c[element], width=width, dash=dash),
                text=TextStyle(color=c[element], size=LABEL_SIZE * size),
            )

        def region(element: str) -> StyleBundle:
            return StyleBundle(
                fill=Fill(color=c[element], opacity=self.region_opacity),
                stroke=Stroke(width=0),
            )

        roles = {
            "canvas": StyleBundle(
                fill=Fill(
                    color=self.background if self.background is not None else WHITE, opacity=1
                )
            ),
            "axes": StyleBundle(stroke=Stroke(color=c["axis"], width=self.guide_width), text=label),
            "title": StyleBundle(text=TextStyle(color=c["label"], size=TITLE_SIZE * size)),
            "micro.curve.total": curve("total"),
            "micro.curve.average": curve("average"),
            "micro.curve.marginal": curve("marginal"),
            "micro.curve.variable": curve("variable"),
            "micro.curve.fixed": curve("fixed", DashStyle.DASHED),
            "micro.curve.average.variable": curve("variable"),
            "micro.curve.average.fixed": curve("fixed", DashStyle.DASHED),
            "micro.guide": StyleBundle(
                stroke=Stroke(color=c["guide"], width=self.guide_width, dash=DashStyle.DASHED),
                text=note,
            ),
            "micro.point": StyleBundle(
                marker=dot, text=TextStyle(color=c["marker"], size=label.size)
            ),
            "micro.mark": StyleBundle(text=note),
            "micro.region.light": region("region_light"),
            "micro.region.mid": region("region_mid"),
            "micro.region.dark": region("region_dark"),
            "micro.annotation": StyleBundle(text=note),
        }
        return Theme(
            f"micro-{self.name}",
            roles,
            defaults=StyleBundle(text=TextStyle(font=self.font)),
        )


def shared_theme(name: str) -> PlotTheme:
    """Build a package theme from a public mosaickit shared-theme name."""
    return PlotTheme.from_palette(name)


def _color(value: str | None) -> str:
    if value is None:
        raise ValueError("Theme role requires a color")
    return value


__all__ = ["ELEMENT_ROLES", "PlotTheme", "shared_theme"]
