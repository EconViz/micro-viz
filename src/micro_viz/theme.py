"""Shared EconViz theme tokens compiled into MosaicKit styles."""

from __future__ import annotations

from dataclasses import dataclass

from mosaickit import (
    TRANSPARENT,
    Fill,
    MathFont,
    Stroke,
    StyleBundle,
    TextFonts,
    TextStyle,
    Theme,
)
from mosaickit import (
    Config as MosaicConfig,
)
from mosaickit.themes import ThemeTokens, get_tokens


@dataclass(frozen=True, slots=True)
class PlotTheme:
    """The shared style inputs needed before domain-specific roles exist."""

    name: str
    background_color: str | None
    axis_color: str
    label_color: str
    primary_color: str
    line_scale: float = 1.0
    label_scale: float = 1.0
    font: str = "sans"
    fonts: TextFonts | None = None
    math_font: MathFont | None = None

    @classmethod
    def from_tokens(cls, tokens: ThemeTokens) -> PlotTheme:
        """Build the scaffold theme from one of MosaicKit's shared themes."""
        colors = tokens.colors
        return cls(
            name=tokens.name,
            background_color=colors["background"],
            axis_color=_color(colors["ink"]),
            label_color=_color(colors["ink"]),
            primary_color=_color(colors["primary"]),
            line_scale=tokens.line_scale,
            label_scale=tokens.label_scale,
        )

    def to_mosaickit(self) -> Theme:
        """Compile this package theme to public MosaicKit styles."""
        background = self.background_color if self.background_color is not None else TRANSPARENT
        text = TextStyle(
            color=self.label_color,
            size=11.0 * self.label_scale,
            font=self.font,
        )
        return Theme(
            self.name,
            {
                "canvas": StyleBundle(fill=Fill(color=background, opacity=1.0)),
                "axes": StyleBundle(
                    stroke=Stroke(color=self.axis_color, width=self.line_scale),
                    text=text,
                ),
                "primary": StyleBundle(
                    stroke=Stroke(color=self.primary_color, width=2.5 * self.line_scale),
                    text=text,
                ),
                "title": StyleBundle(
                    text=TextStyle(
                        color=self.label_color,
                        size=12.0 * self.label_scale,
                        font=self.font,
                    )
                ),
            },
            defaults=StyleBundle(text=text),
        )

    def mosaickit_config(self) -> MosaicConfig:
        """Return the MosaicKit configuration used to render this theme."""
        return MosaicConfig(
            theme=self.to_mosaickit(),
            fonts=self.fonts,
            math_font=self.math_font,
        )


def shared_theme(name: str) -> PlotTheme:
    """Build a package theme from a public MosaicKit shared-theme name."""
    # This package deliberately uses the manual look for its product default. The
    # shared default and colorblind themes have identical tokens, so users who want
    # that colored palette can select colorblind without losing a visual option.
    token_name = "manual" if name.strip().lower() == "default" else name
    return PlotTheme.from_tokens(get_tokens(token_name))


def _color(value: str | None) -> str:
    if value is None:
        raise ValueError("Theme role requires a color")
    return value


__all__ = ["PlotTheme", "shared_theme"]
