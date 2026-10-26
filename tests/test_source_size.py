from __future__ import annotations

from pathlib import Path

SOURCE_ROOT = Path(__file__).parents[1] / "src"
MAX_LINES = 450


def test_no_source_file_exceeds_the_line_limit() -> None:
    counts = {
        path.relative_to(SOURCE_ROOT): len(path.read_text(encoding="utf-8").splitlines())
        for path in SOURCE_ROOT.rglob("*.py")
    }
    too_long = {str(path): count for path, count in sorted(counts.items()) if count > MAX_LINES}
    assert too_long == {}, f"source files above {MAX_LINES} lines: {too_long}"
