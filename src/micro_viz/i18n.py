"""Built-in figure text in English, Traditional Chinese or Simplified Chinese.

Every word micro-viz puts in a figure lives in ``locale/labels.json``, keyed by a stable id
(``"production.tp"``) and then by language, so no figure logic contains display text. A
builder looks its text up through :func:`text`; anything a caller passes as ``title=``, an
axis name or ``labels=`` is used as given and never translated.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from functools import cache
from importlib import resources

LANGUAGES = ("en", "zh-TW", "zh-CN")
"""The languages the label table covers; the first is the fallback."""


def validate_language(language: str) -> str:
    """Return ``language`` if micro-viz can draw it, else raise ``ValueError``."""
    if language not in LANGUAGES:
        raise ValueError(f"language must be one of {', '.join(LANGUAGES)}; got {language!r}")
    return language


@cache
def _table() -> Mapping[str, Mapping[str, str]]:
    source = resources.files("micro_viz.locale").joinpath("labels.json").read_text("utf-8")
    table: dict[str, dict[str, str]] = json.loads(source)
    return table


def labels(language: str) -> Mapping[str, str]:
    """Every built-in text id of ``language`` with its text."""
    return _table()[validate_language(language)]


def text(key: str, language: str = LANGUAGES[0], **fields: object) -> str:
    """The text of ``key`` in ``language``, with ``{name}`` placeholders filled from ``fields``.

    Raises ``KeyError`` for an id the table does not have, so a typo cannot silently draw
    nothing or draw the id itself.
    """
    template = labels(language)[key]
    return template.format(**fields) if fields else template


__all__ = ["LANGUAGES", "labels", "text", "validate_language"]
