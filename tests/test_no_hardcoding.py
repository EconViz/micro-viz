"""The package keeps colours, fonts, paths and display text out of its logic."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from micro_viz.core.i18n import labels

SOURCE = Path(__file__).parents[1] / "src" / "micro_viz"
EXAMPLES = Path(__file__).parents[1] / "examples" / "scripts"
HEX_COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b")
ABSOLUTE_PATH = re.compile(r"(?<![\w.])(/Users/|/home/|/tmp/|[A-Za-z]:\\\\)")
FONT_NAMES = (
    "Pagella",
    "Arial",
    "Helvetica",
    "DejaVu",
    "Times",
    "Noto",
    "Courier",
    "Georgia",
    "Calibri",
    "Verdana",
)


def _python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py"))


def _string_literals(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                docstrings.add(id(body[0].value))
    return [
        (node.lineno, node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstrings
    ]


def test_source_has_no_colour_literals_font_names_or_absolute_paths() -> None:
    offenders: list[str] = []
    for path in (*_python_files(SOURCE), *_python_files(EXAMPLES)):
        for line, value in _string_literals(path):
            if HEX_COLOR.search(value):
                offenders.append(f"{path.name}:{line} colour {value!r}")
            if ABSOLUTE_PATH.search(value):
                offenders.append(f"{path.name}:{line} path {value!r}")
            if any(name in value for name in FONT_NAMES):
                offenders.append(f"{path.name}:{line} font {value!r}")
    assert offenders == []


def test_visual_modules_contain_no_display_words() -> None:
    """Text drawn in a figure comes from the label table, not from the builders."""
    table_words = {value for value in labels("en").values() if value.isalpha() and len(value) > 3}
    offenders = [
        f"{path.name}:{line} {value!r}"
        for path in _python_files(SOURCE / "visuals")
        for line, value in _string_literals(path)
        if value in table_words
    ]
    assert offenders == []


def test_visual_builders_default_to_no_title() -> None:
    import inspect

    from micro_viz import visuals

    for name in visuals.__all__:
        parameters = inspect.signature(getattr(visuals, name)).parameters
        title = parameters["title"] if "title" in parameters else parameters["titles"]
        assert title.default is None or all(item in (None, "") for item in title.default)
