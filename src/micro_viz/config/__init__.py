"""Compatibility entry point for shared configuration."""

from micro_viz.core import config as _config
from micro_viz.core.config import *  # noqa: F403

__all__ = _config.__all__
