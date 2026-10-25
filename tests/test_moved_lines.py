from __future__ import annotations

import pytest
from mosaickit import Stroke

from micro_viz import Config, PlotTheme, default_theme

MARGIN_POINTS = 1.0


def _widths(theme: PlotTheme) -> tuple[Stroke, Stroke, Stroke]:
    roles = theme.to_mosaickit()
    main = roles.roles["micro.curve.marginal"].stroke
    after = roles.roles["micro.curve.after"].stroke
    arrow = roles.roles["micro.arrow"].stroke
    return main, after, arrow


def test_after_curves_and_arrows_are_clearly_thinner_than_main_curves() -> None:
    theme = default_theme()
    assert theme.after_width + MARGIN_POINTS <= theme.curve_width
    assert theme.arrow_width + MARGIN_POINTS <= theme.curve_width
    assert theme.guide_width <= theme.arrow_width <= theme.after_width


def test_compiled_roles_use_the_tokens_and_are_solid() -> None:
    theme = default_theme()
    main, after, arrow = _widths(theme)
    assert after.width == pytest.approx(theme.after_width)
    assert arrow.width == pytest.approx(theme.arrow_width)
    assert after.width < main.width and arrow.width < main.width
    assert after.dash == main.dash


def test_widths_come_from_the_shared_settings() -> None:
    config = Config.from_dict({"base": "manual", "micro": {"stroke": {"after": 0.8, "arrow": 0.6}}})
    assert config.theme.after_width == pytest.approx(0.8)
    assert config.theme.arrow_width == pytest.approx(0.6)
