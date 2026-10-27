from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from mosaickit import ConfigurationError
from mosaickit.econ_toml import figure_overrides

from micro_viz import Config, default_theme, shared_theme
from micro_viz.core.config import SCHEMA


@pytest.fixture(autouse=True)  # type: ignore[untyped-decorator]
def reset_config() -> Iterator[None]:
    Config.reset()
    yield
    Config.reset()


def test_defaults_to_color_theme_on_white() -> None:
    theme = Config().theme
    assert theme.name == "default"
    assert theme.background is None
    assert theme.colors["axis"] == "#222222"
    assert theme.colors["label"] == "#222222"
    assert theme.colors["average"] == "#377EB8"
    canvas_style = theme.to_mosaickit().resolve("canvas", fallback_category="fill")
    assert canvas_style.fill is not None
    assert canvas_style.fill.color.to_hex().lower() == "#ffffff"


def test_absent_settings_match_empty_settings(tmp_path: Path) -> None:
    assert Config.discover(tmp_path) == Config.from_dict({}) == Config()


def test_explicit_theme_uses_shared_mosaickit_tokens() -> None:
    configured = Config.from_dict({"base": "colorblind"})
    assert configured.theme == shared_theme("colorblind")
    assert configured.theme.colors["average"] == "#377EB8"


def test_named_default_is_the_color_product_default() -> None:
    assert Config.from_dict({"base": "default"}).theme == shared_theme("default")
    assert shared_theme("default").name == "default"


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
    assert config.theme.background == "#fefefe"
    assert config.theme.colors["axis"] == "#111111"
    assert config.theme.colors["label"] == "#222222"


def test_shared_font_reaches_fallback_and_title_text() -> None:
    theme = Config.from_dict({"font": {"text": "serif"}}).theme.to_mosaickit()
    fallback = theme.resolve("micro.unlisted", fallback_category="text").text
    title = theme.resolve("title", fallback_category="text").text
    assert fallback is not None and fallback.font == "serif"
    assert title is not None and title.font == "serif"


def test_other_package_tables_are_ignored() -> None:
    assert Config.from_dict({"macro": {"anything": True}}) == Config()


def test_unknown_micro_setting_is_rejected() -> None:
    with pytest.raises(ConfigurationError, match=r"\[micro\].*unknown key 'colour'"):
        Config.from_dict({"micro": {"colour": "#ffffff"}})


def test_empty_micro_table_is_the_default() -> None:
    assert Config.from_dict({"micro": {}}) == Config()
    template = SCHEMA.template()
    assert "language" in template and "[micro.label.curve]" in template


def test_micro_table_sets_language_widths_opacity_and_colours() -> None:
    theme = Config.from_dict(
        {
            "base": "manual",
            "micro": {
                "language": "zh-TW",
                "stroke": {"curve": 5, "guide": 2},
                "marker": {"diameter": 8},
                "opacity": {"region": 0.5},
                "color": {"marginal": "#123456"},
            },
        }
    ).theme
    assert theme.language == "zh-TW"
    assert (theme.curve_width, theme.guide_width, theme.marker_diameter) == (5, 2, 8)
    assert theme.region_opacity == 0.5
    assert theme.colors["marginal"] == "#123456"
    assert theme.colors["average"] == shared_theme("manual").colors["average"]


def test_unknown_language_and_bad_widths_are_rejected() -> None:
    with pytest.raises(ConfigurationError):
        Config.from_dict({"micro": {"language": "fr"}})
    with pytest.raises(ConfigurationError):
        Config.from_dict({"micro": {"stroke": {"curve": 0}}})
    with pytest.raises(ConfigurationError):
        Config.from_dict({"micro": {"opacity": {"region": 1.5}}})


def test_label_group_nudges_come_from_the_settings() -> None:
    theme = Config.from_dict(
        {"micro": {"label": {"curve": {"top": "4pt", "right": "2pt"}, "region": {"left": "1pt"}}}}
    ).theme
    assert set(theme.label_nudges) == {"curve", "region"}
    assert theme.label_nudges["curve"].dy == pytest.approx(4.0)
    assert theme.label_nudges["curve"].dx == pytest.approx(2.0)
    assert theme.label_nudges["region"].dx == pytest.approx(-1.0)


def test_config_activates_shared_figure_label_overrides() -> None:
    Config.from_dict({"figure": {"smoke": {"label": {"smoke.title": {"top": "4pt"}}}}}).use()
    assert figure_overrides("smoke")["smoke.title"].dy == pytest.approx(4.0)


def test_active_config_becomes_the_default() -> None:
    configured = Config.from_dict({"base": "paper"}).use()
    assert default_theme() == configured.theme
