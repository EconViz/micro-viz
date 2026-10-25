"""Shared helpers of the example scripts: arguments, settings and output files."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from collections.abc import Sequence
from pathlib import Path

from micro_viz import Config, PlotTheme
from micro_viz.i18n import LANGUAGES

EXAMPLES = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = EXAMPLES / "econ-viz.toml"
DEFAULT_OUTPUT = EXAMPLES / "output"
FONT_PATTERNS = ("*.otf", "*.ttf")
TEXMF_FONT_DIRS = ("fonts/opentype/public/tex-gyre", "fonts/opentype/public/tex-gyre-math")


def parser(description: str | None) -> argparse.ArgumentParser:
    """An argument parser with the options every example takes."""
    result = argparse.ArgumentParser(description=description)
    result.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    result.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="an econ-viz.toml")
    result.add_argument(
        "--fonts-dir",
        type=Path,
        action="append",
        default=[],
        help="a directory of the font files the settings name (repeatable)",
    )
    result.add_argument("--language", choices=LANGUAGES, default=None)
    return result


def font_directories(extra: Sequence[Path]) -> list[Path]:
    """The directories searched for the settings' font files: the given ones, then TeX's."""
    directories = list(extra)
    try:
        root = subprocess.run(
            ["kpsewhich", "-var-value", "TEXMFDIST"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return directories
    directories.extend(Path(root) / relative for relative in TEXMF_FONT_DIRS)
    return directories


def load_theme(args: argparse.Namespace, workdir: Path) -> PlotTheme:
    """The theme of ``args.config``, with its font files linked beside a copy in ``workdir``."""
    for directory in font_directories(args.fonts_dir):
        for pattern in FONT_PATTERNS:
            for font in directory.glob(pattern):
                link = workdir / font.name
                if not link.exists():
                    link.symlink_to(font)
    copy = workdir / args.config.name
    shutil.copy(args.config, copy)
    config = Config.load(copy).use()
    theme = config.theme
    if args.language is not None:
        from dataclasses import replace

        theme = replace(theme, language=args.language)
    return theme


class Session:
    """A temporary directory holding the settings and fonts while figures are drawn."""

    def __init__(self, args: argparse.Namespace) -> None:
        self._directory = tempfile.TemporaryDirectory(prefix="micro-viz-examples-")
        self.theme = load_theme(args, Path(self._directory.name))
        self.output_dir: Path = args.output_dir

    def path(self, name: str) -> Path:
        """The output file ``name`` inside the output directory, which is created."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return self.output_dir / name

    def close(self) -> None:
        self._directory.cleanup()
