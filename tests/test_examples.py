from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).parents[1]
PRODUCTION_SCRIPT = REPOSITORY_ROOT / "examples" / "scripts" / "production.py"


PLAIN_CONFIG = 'base = "manual"\n'
FONTS = Path(__file__).parents[2] / "agora" / "fonts"


def _plain_config(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "econ-viz.toml"
    path.write_text(PLAIN_CONFIG, encoding="utf-8")
    return path


def _run(output: Path, *arguments: str) -> tuple[str, str]:
    config = _plain_config(output.parent / f"{output.name}-config")
    subprocess.run(
        [
            sys.executable,
            str(PRODUCTION_SCRIPT),
            "--output-dir",
            str(output),
            "--config",
            str(config),
            *arguments,
        ],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return (
        (output / "total_product.svg").read_text(encoding="utf-8"),
        (output / "average_marginal_product.svg").read_text(encoding="utf-8"),
    )


def test_production_example_renders_both_manual_theme_figures(tmp_path: Path) -> None:
    total, products = _run(tmp_path)
    combined = f"{total}\n{products}".lower()
    assert "#8c8c8c" in combined
    assert "#1a1a1a" in combined
    assert "#377eb8" not in combined
    assert "micro.production.tp" in total
    assert "micro.production.mp" in products


def test_example_parameters_and_title_reach_the_figures(tmp_path: Path) -> None:
    baseline = _run(tmp_path / "a")
    changed = _run(tmp_path / "b", "--cubic", "-0.4", "--max-input", "8", "--title", "Own title")
    assert baseline != changed
    assert "Own title" not in baseline[0]


@pytest.mark.skipif(  # type: ignore[untyped-decorator]
    not FONTS.is_dir(), reason="the manual's Noto fonts are not checked out"
)
@pytest.mark.parametrize("language", ["zh-TW", "zh-CN"])  # type: ignore[untyped-decorator]
def test_bundled_chinese_settings_draw_built_in_text(tmp_path: Path, language: str) -> None:
    config = REPOSITORY_ROOT / "examples" / f"econ-viz.{language}.toml"
    subprocess.run(
        [
            sys.executable,
            str(PRODUCTION_SCRIPT),
            "--output-dir",
            str(tmp_path),
            "--config",
            str(config),
            "--fonts-dir",
            str(FONTS),
        ],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert (tmp_path / "average_marginal_product.svg").stat().st_size > 0


def test_animation_example_writes_an_animated_svg(tmp_path: Path) -> None:
    pytest.importorskip("kinetickit")
    config = _plain_config(tmp_path / "config")
    script = REPOSITORY_ROOT / "examples" / "scripts" / "animate_production.py"
    subprocess.run(
        [
            sys.executable,
            str(script),
            "--output-dir",
            str(tmp_path),
            "--config",
            str(config),
            "--steps",
            "2",
            "--from",
            "3",
            "--to",
            "5",
        ],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    svg = (tmp_path / "average_marginal_product_animated.svg").read_text(encoding="utf-8")
    assert "<animate" in svg and "micro.production.mp" in svg
