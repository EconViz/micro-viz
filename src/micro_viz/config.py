"""micro-viz settings declared through MosaicKit's ``econ-viz.toml`` schema."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import cast

from mosaickit import MathFont, econ_toml
from mosaickit.themes import list_shared_themes

from micro_viz.theme import PlotTheme, shared_theme


def _base(name: str) -> Callable[[], PlotTheme]:
    return partial(shared_theme, name)


_BASES = {name: _base(name) for name in list_shared_themes()}
# MosaicKit's Schema uses the key "default" when no file is present. micro-viz's
# product default is the manual's black-and-white look; colorblind remains available.
_BASES["default"] = _base("manual")

SCHEMA = econ_toml.register(
    econ_toml.Schema(
        package="micro",
        base=_BASES,
        shared={
            "font": "font",
            "fonts": "fonts",
            "math_font": econ_toml.transform(
                "math_font", lambda value, ctx: MathFont(ctx.resolve(value))
            ),
            "background": "background_color",
            "axis": "axis_color",
            "label": "label_color",
        },
    )
)


class Config(SCHEMA.config_class()):  # type: ignore[misc]
    """A micro-viz theme loaded from the shared ``econ-viz.toml`` file."""

    __slots__ = ()

    @property
    def theme(self) -> PlotTheme:
        """The package theme described by this configuration."""
        return cast(PlotTheme, self.value)


def default_theme() -> PlotTheme:
    """Return the active theme, or the built-in black-and-white manual theme."""
    active = Config.active()
    return active.theme if active is not None else Config().theme


__all__ = ["Config", "SCHEMA", "default_theme"]
