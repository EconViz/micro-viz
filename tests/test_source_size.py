from __future__ import annotations

from pathlib import Path

SOURCE_ROOT = Path(__file__).parents[1] / "src"
MAX_LINES = 450
KNOWN_OVERSIZED = {
    Path("micro_viz/firm/costs/visuals/derivation.py"),
    Path("micro_viz/firm/costs/visuals/long_run.py"),
}


def test_no_source_file_exceeds_the_line_limit() -> None:
    counts = {
        path.relative_to(SOURCE_ROOT): len(path.read_text(encoding="utf-8").splitlines())
        for path in SOURCE_ROOT.rglob("*.py")
    }
    too_long = {
        str(path): count
        for path, count in sorted(counts.items())
        if count > MAX_LINES and path not in KNOWN_OVERSIZED
    }
    assert too_long == {}, f"source files above {MAX_LINES} lines: {too_long}"


def test_known_oversized_files_do_not_grow() -> None:
    limits = {
        Path("micro_viz/firm/costs/visuals/derivation.py"): 519,
        Path("micro_viz/firm/costs/visuals/long_run.py"): 511,
    }
    counts = {
        path: len((SOURCE_ROOT / path).read_text(encoding="utf-8").splitlines()) for path in limits
    }
    assert all(counts[path] <= limit for path, limit in limits.items())
