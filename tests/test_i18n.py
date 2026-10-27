from __future__ import annotations

import pytest

from micro_viz import shared_theme
from micro_viz.core.i18n import LANGUAGES, labels, text, validate_language


def test_every_language_has_the_same_text_ids() -> None:
    reference = set(labels("en"))
    assert reference
    for language in LANGUAGES:
        assert set(labels(language)) == reference


def test_text_fills_placeholders_and_rejects_unknown_ids() -> None:
    assert text("production.mark.inflection", "en", input="K") == "K_1"
    assert text("production.product", "zh-TW") != text("production.product", "en")
    with pytest.raises(KeyError):
        text("production.nonexistent")


def test_unknown_language_is_rejected() -> None:
    with pytest.raises(ValueError, match="language must be one of"):
        validate_language("fr")
    with pytest.raises(ValueError):
        labels("fr")


def test_theme_text_uses_its_language() -> None:
    from dataclasses import replace

    theme = replace(shared_theme("manual"), language="zh-CN")
    assert theme.text("production.region.negative") == labels("zh-CN")["production.region.negative"]
