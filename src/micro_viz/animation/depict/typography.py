"""Text assets in the canvas's configured fonts."""

from __future__ import annotations

import importlib
import re
from functools import lru_cache
from pathlib import Path as FilePath
from typing import Any

from mosaickit import (
    Canvas,
)

from micro_viz.animation.depict._support import (
    FONT_FAMILIES,
    ITALIC_CAPITAL_A,
    ITALIC_PLANCK,
    ITALIC_SMALL_A,
)

_COMMAND = re.compile(r"\\[A-Za-z]+|[A-Za-z]")


def _italic_letters(latex: str, coverage: frozenset[int]) -> str:
    """Set single letters in the Mathematical Italic alphabet where the font has it, as TeX does."""

    def replace_letter(match: re.Match[str]) -> str:
        value = match.group(0)
        if len(value) != 1:
            return value
        if value == "h":
            target = ITALIC_PLANCK
        elif value.isupper():
            target = ITALIC_CAPITAL_A + ord(value) - ord("A")
        else:
            target = ITALIC_SMALL_A + ord(value) - ord("a")
        return chr(target) if target in coverage else value

    return _COMMAND.sub(replace_letter, latex)


class Typography:
    """GlyphKit text assets in the canvas's configured fonts (DejaVu when none are set)."""

    def __init__(self, canvas: Canvas) -> None:
        self.fonts = canvas.config.fonts
        self.math_font = canvas.config.math_font
        self._engines: dict[str, Any] = {}
        self._coverage: frozenset[int] = frozenset()

    def _paths(self, slot: str) -> tuple[FilePath, ...]:
        configured = getattr(self.fonts, slot, None) if self.fonts is not None else None
        if configured:
            return tuple(configured)
        font_manager = importlib.import_module("matplotlib.font_manager")
        family = FONT_FAMILIES[slot]
        return tuple(
            dict.fromkeys(
                FilePath(
                    font_manager.findfont(font_manager.FontProperties(family=family, weight=w))
                )
                for w in ("normal", "bold")
            )
        )

    def _typography(self, slot: str) -> Any:
        if slot not in self._engines:
            from glyphkit import FontLibrary, FontSource
            from kinetickit.integrations.glyphkit import GlyphKitTypography

            sources = tuple(FontSource.path(path) for path in self._paths(slot))
            library = FontLibrary.from_sources(sources)
            families = tuple(dict.fromkeys(face.family for face in library.manifest().faces))
            self._engines[slot] = GlyphKitTypography(library, families=families, embed=False)
        return self._engines[slot]

    def _math(self) -> Any:
        if "math" not in self._engines and self.math_font is not None:
            from glyphkit import FontLibrary, FontSource
            from kinetickit.integrations.glyphkit import GlyphKitTypography

            library = FontLibrary.from_sources((FontSource.path(self.math_font.path),))
            families = tuple(dict.fromkeys(face.family for face in library.manifest().faces))
            self._engines["math"] = GlyphKitTypography(library, families=families, embed=False)
            face = next((item for item in library.faces if item.has_math), None)
            self._coverage = face.coverage if face is not None else frozenset()
        return self._engines.get("math")

    @lru_cache(maxsize=512)  # noqa: B019
    def asset(self, text: str, slot: str, size: float, weight: int, math: bool) -> Any:
        if math and self.math_font is not None:
            engine = self._math()
            latex = (
                _italic_letters(text.strip("$"), self._coverage)
                if self.math_font.italic
                else text.strip("$")
            )
            return engine.math(latex, size=size)
        plain = text.strip("$") if math else text
        return self._typography(slot).asset(plain, size=size, weight=weight)
