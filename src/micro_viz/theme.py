"""Shared EconViz theme tokens compiled into MosaicKit styles."""

from __future__ import annotations

from dataclasses import dataclass

from mosaickit import (
    Config as MosaicConfig,
)
from mosaickit import (
    DashStyle,
    Fill,
    MathFont,
    Stroke,
    StyleBundle,
    TextFonts,
    TextStyle,
    Theme,
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
    secondary_color: str
    accent_color: str
    increasing_fill_color: str
    diminishing_fill_color: str
    negative_fill_color: str
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
            secondary_color=_color(colors["secondary"]),
            accent_color=_color(colors["accent"]),
            increasing_fill_color=_color(colors["fill.light"]),
            diminishing_fill_color=_color(colors["fill.mid"]),
            negative_fill_color=_color(colors["fill.dark"]),
            line_scale=tokens.line_scale,
            label_scale=tokens.label_scale,
        )

    def to_mosaickit(self) -> Theme:
        """Compile this package theme to public MosaicKit styles."""
        # EconViz diagram packages do not provide a dark or transparent canvas.
        background = self.background_color if self.background_color is not None else "#ffffff"
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
                "micro.production.total": StyleBundle(
                    stroke=Stroke(color=self.primary_color, width=2.5 * self.line_scale),
                    text=TextStyle(
                        color=self.primary_color,
                        size=11.0 * self.label_scale,
                        font=self.font,
                    ),
                ),
                "micro.production.average": StyleBundle(
                    stroke=Stroke(
                        color=self.secondary_color,
                        width=2.25 * self.line_scale,
                        dash=DashStyle.DASHED,
                    ),
                    text=TextStyle(
                        color=self.secondary_color,
                        size=11.0 * self.label_scale,
                        font=self.font,
                    ),
                ),
                "micro.production.marginal": StyleBundle(
                    stroke=Stroke(color=self.accent_color, width=2.25 * self.line_scale),
                    text=TextStyle(
                        color=self.accent_color,
                        size=11.0 * self.label_scale,
                        font=self.font,
                    ),
                ),
                "micro.production.region.increasing": StyleBundle(
                    fill=Fill(color=self.increasing_fill_color, opacity=0.10)
                ),
                "micro.production.region.diminishing": StyleBundle(
                    fill=Fill(color=self.diminishing_fill_color, opacity=0.08)
                ),
                "micro.production.region.negative": StyleBundle(
                    fill=Fill(color=self.negative_fill_color, opacity=0.10)
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
    return PlotTheme.from_tokens(get_tokens(name))


def _color(value: str | None) -> str:
    if value is None:
        raise ValueError("Theme role requires a color")
    return value


__all__ = ["PlotTheme", "shared_theme"]
