from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from mosaickit import ConfigurationError
from mosaickit.econ_toml import figure_overrides

from micro_viz import Config, default_theme, shared_theme
from micro_viz.config import SCHEMA


@pytest.fixture(autouse=True)  # type: ignore[untyped-decorator]
def reset_config() -> Iterator[None]:
    Config.reset()
    yield
    Config.reset()


def test_defaults_to_manual_theme() -> None:
    theme = Config().theme
    assert theme.name == "manual"
    assert theme.background_color == "#ffffff"
    assert theme.axis_color == "#1a1a1a"
    assert theme.label_color == "#1a1a1a"
    assert theme.primary_color == "#8c8c8c"


def test_absent_settings_match_empty_settings(tmp_path: Path) -> None:
    assert Config.discover(tmp_path) == Config.from_dict({}) == Config()


def test_explicit_theme_uses_shared_mosaickit_tokens() -> None:
    configured = Config.from_dict({"base": "colorblind"})
    assert configured.theme == shared_theme("colorblind")
    assert configured.theme.primary_color == "#377EB8"


def test_named_default_is_the_manual_product_default() -> None:
    assert Config.from_dict({"base": "default"}).theme == shared_theme("default")
    assert shared_theme("default").name == "manual"


def test_shared_colors_override_the_selected_theme() -> None:
    config = Config.from_dict(
        {
            "base": "manual",
            "color": {
                "background": "#fefefe",
                "axis": "#111111",
                "label": "#222222",
            },
        }
    )
    assert config.theme.background_color == "#fefefe"
    assert config.theme.axis_color == "#111111"
    assert config.theme.label_color == "#222222"


def test_shared_font_reaches_fallback_and_title_text() -> None:
    theme = Config.from_dict({"font": {"text": "serif"}}).theme.to_mosaickit()
    fallback = theme.resolve("micro.annotation", fallback_category="text").text
    title = theme.resolve("title", fallback_category="text").text
    assert fallback is not None and fallback.font == "serif"
    assert title is not None and title.font == "serif"


def test_other_package_tables_are_ignored() -> None:
    assert Config.from_dict({"macro": {"anything": True}}) == Config()


def test_unknown_micro_setting_is_rejected() -> None:
    with pytest.raises(ConfigurationError, match=r"\[micro\].*unknown key 'colour'"):
        Config.from_dict({"micro": {"colour": "#ffffff"}})


def test_empty_micro_table_is_the_complete_scaffold_template() -> None:
    assert Config.from_dict({"micro": {}}) == Config()
    assert SCHEMA.template() == "# [micro]\n"


def test_config_activates_shared_figure_label_overrides() -> None:
    Config.from_dict({"figure": {"smoke": {"label": {"smoke.title": {"top": "4pt"}}}}}).use()
    assert figure_overrides("smoke")["smoke.title"].dy == pytest.approx(4.0)


def test_active_config_becomes_the_default() -> None:
    configured = Config.from_dict({"base": "paper"}).use()
    assert default_theme() == configured.theme
