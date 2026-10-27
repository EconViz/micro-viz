"""Compatibility entry point for shared label grouping."""

from micro_viz.core import label_groups as _label_groups
from micro_viz.core.label_groups import *  # noqa: F403

__all__ = _label_groups.__all__
