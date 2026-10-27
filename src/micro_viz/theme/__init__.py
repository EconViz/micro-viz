"""Compatibility entry point for shared theming."""

from micro_viz.core import theme as _theme
from micro_viz.core.theme import *  # noqa: F403

__all__ = _theme.__all__
