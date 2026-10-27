"""Shared micro-viz settings loaded from ``econ-viz.toml``.

mosaickit reads and checks the file (see ``mosaickit.econ_toml``); this module only declares
what micro-viz takes from it. The shared top level sets the starting colour model (``base``),
the fonts and the axis and label colours; micro-viz's own settings live in ``[micro]``::

    base = "manual"           # shared theme to start from (mosaickit.themes)

    [font]
    text = "serif"
    math = "fonts/texgyrepagella-math.otf"

    [fonts]
    serif = ["fonts/NotoSerifTC-Regular.otf", "fonts/NotoSerifTC-Bold.otf"]

    [micro]
    language = "zh-TW"        # language of built-in figure text

    [micro.color]             # any element of micro_viz.core.theme.ELEMENT_ROLES
    marginal = "#1a1a1a"

    [micro.stroke]            # widths in points
    curve = 3.5
    dashed = 2.0
    guide = 1.0

    [micro.marker]
    diameter = 6.5            # a marked point's diameter in points

    [micro.brace]
    gap = 4.0                 # gap in points between a shaded region and its brace

    [micro.region]
    fill = true               # shade regions; false keeps only their braces and names
    extent = "top"            # "top" reaches the top of the plot, "curve" stops at the curve

    [micro.opacity]
    region = 0.3              # opacity of shaded regions

    [micro.label.curve]       # move whole groups of labels (see micro_viz.core.label_groups)
    top = "2pt"               # also bottom, left, right; pt, mm, cm or in, no em

The label groups are ``point``, ``curve``, ``region``, ``mark`` and ``annotation``. Single
labels of single figures are moved with ``[figure.<file>.label."<id>"]``, which mosaickit
applies when the figure is saved. Load the file once and every figure made without an
explicit ``theme`` uses it::

    from micro_viz import Config
    Config.load("econ-viz.toml").use()

Relative paths are resolved against the file's directory. Anything left out keeps the
built-in default.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, make_dataclass, replace
from pathlib import Path
from typing import Any

from mosaickit import MathFont, econ_toml
from mosaickit.styles.nudge import Nudge, nudge_from
from mosaickit.themes import list_shared_themes

from micro_viz.core.i18n import LANGUAGES
from micro_viz.core.label_groups import LABEL_GROUPS, LABEL_SIDES
from micro_viz.core.theme import ELEMENT_ROLES, REGION_EXTENTS, PlotTheme, shared_theme

COLOR_MODELS = list_shared_themes()
COLOR_ELEMENTS = tuple(ELEMENT_ROLES)

_DIRECTIONS = {"top": "up", "bottom": "down", "left": "left", "right": "right"}

# The colours the file sets, one per element; None keeps the theme's own colour.
_Colors = make_dataclass(
    "_Colors",
    [(element, "str | None", field(default=None)) for element in COLOR_ELEMENTS],
    frozen=True,
)

# The label nudges the file sets, one length per group and side; None leaves it out.
_Nudges = make_dataclass(
    "_Nudges",
    [
        (f"{group}_{side}", "float | None", field(default=None))
        for group in LABEL_GROUPS
        for side in LABEL_SIDES
    ],
    frozen=True,
)


@dataclass(frozen=True)
class _Draft:
    """What the file sets, turned into a PlotTheme by ``_finish``."""

    theme: PlotTheme
    colors: Any = field(default_factory=_Colors)
    nudges: Any = field(default_factory=_Nudges)


def _base(name: str) -> Any:
    return lambda: _Draft(theme=shared_theme(name))


def _math_font(value: Any, ctx: econ_toml.Context) -> MathFont:
    return MathFont(Path(value))


def _label_nudges(nudges: Any) -> dict[str, Nudge]:
    """The nudge of each group the file moves; a group set to no move is left out."""
    found: dict[str, Nudge] = {}
    for group in LABEL_GROUPS:
        nudge = nudge_from(**{side: getattr(nudges, f"{group}_{side}") for side in LABEL_SIDES})
        if not nudge.is_zero:
            found[group] = nudge
    return found


def _finish(draft: _Draft, ctx: econ_toml.Context) -> PlotTheme:
    theme = draft.theme
    colors = {
        f.name: getattr(draft.colors, f.name)
        for f in fields(draft.colors)
        if getattr(draft.colors, f.name) is not None
    }
    changes: dict[str, Any] = {}
    if colors:
        changes["colors"] = {**theme.colors, **colors}
    nudges = _label_nudges(draft.nudges)
    if nudges:
        changes["label_nudges"] = nudges
    return replace(theme, **changes) if changes else theme


SCHEMA = econ_toml.register(
    econ_toml.Schema(
        package="micro",
        base={name: _base(name) for name in COLOR_MODELS},
        fields={
            "language": econ_toml.choice("theme.language", LANGUAGES),
            **{
                f"color.{element}": econ_toml.color(f"colors.{element}")
                for element in COLOR_ELEMENTS
            },
            "stroke.curve": econ_toml.positive("theme.curve_width"),
            "stroke.dashed": econ_toml.positive("theme.dashed_width"),
            "stroke.guide": econ_toml.positive("theme.guide_width"),
            "stroke.after": econ_toml.positive("theme.after_width"),
            "stroke.arrow": econ_toml.positive("theme.arrow_width"),
            "marker.diameter": econ_toml.positive("theme.marker_diameter"),
            "brace.gap": econ_toml.number("theme.brace_gap", minimum=0),
            "opacity.region": econ_toml.number(
                "theme.region_opacity", minimum=0, maximum=1, exclusive_minimum=True
            ),
            "region.fill": econ_toml.boolean("theme.region_fill"),
            "region.extent": econ_toml.choice("theme.region_extent", REGION_EXTENTS),
            **{
                f"label.{group}.{side}": econ_toml.length(f"nudges.{group}_{side}")
                for group in LABEL_GROUPS
                for side in LABEL_SIDES
            },
        },
        shared={
            "font": "theme.font",
            "fonts": "theme.fonts",
            "math_font": econ_toml.transform("theme.math_font", _math_font),
            "background": "theme.background",
            "axis": "colors.axis",
            "label": "colors.label",
        },
        finalize=_finish,
        docs={
            "language": "language of built-in figure text",
            "stroke.curve": "main curve width in points",
            "stroke.dashed": "dashed curve width in points",
            "stroke.guide": "axis and guide line width in points",
            "stroke.after": "width in points of a curve after a change (thin, solid)",
            "stroke.arrow": "width in points of a movement arrow (solid)",
            "marker.diameter": "marked point diameter in points",
            "brace.gap": "gap in points between a shaded region and its brace",
            "opacity.region": "opacity of shaded regions, above 0 and at most 1",
            "region.fill": "shade the marginal-return regions (false keeps braces and names)",
            "region.extent": "shade to the top of the plot (top) or only under the curve (curve)",
            **{f"color.{element}": "unset keeps the theme's colour" for element in COLOR_ELEMENTS},
            **{
                f"label.{group}.{side}": f"move {group} labels {_DIRECTIONS[side]} (a length)"
                for group in LABEL_GROUPS
                for side in LABEL_SIDES
            },
        },
    )
)


class Config(SCHEMA.config_class()):  # type: ignore[misc]
    """A theme read from ``econ-viz.toml``; :meth:`use` makes it the default."""

    __slots__ = ()

    @property
    def theme(self) -> PlotTheme:
        """The PlotTheme the file describes."""
        value: PlotTheme = self.value
        return value


def default_theme(palette: str | None = None) -> PlotTheme:
    """The theme a figure uses without an explicit one.

    A ``palette`` named in the call wins; otherwise the config set by :meth:`Config.use`,
    otherwise the built-in colour ``default`` theme.
    """
    if palette is not None:
        return shared_theme(palette)
    active = Config.active()
    return active.theme if active is not None else Config().theme


__all__ = ["COLOR_ELEMENTS", "COLOR_MODELS", "SCHEMA", "Config", "default_theme"]
