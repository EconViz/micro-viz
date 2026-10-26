"""Shared helpers of the example scripts: arguments, settings and output files."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

from micro_viz import Config, PlotTheme
from micro_viz.i18n import LANGUAGES

EXAMPLES = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = EXAMPLES / "econ-viz.toml"
DEFAULT_OUTPUT = EXAMPLES / "output"
OUTPUT_TOPICS = {
    "production": ("production", "production_extensions"),
    "isoquants": ("isoquants", "cost_minimization"),
    "costs": ("costs", "piecewise_costs", "long_run_costs"),
    "competition": ("competition", "long_run_competition"),
    "monopoly": ("monopoly",),
    "monopolistic_competition": ("monopolistic_competition",),
    "oligopoly": ("oligopoly", "dominant_firm"),
    "vertical": ("vertical",),
    "factor_markets": ("factor_markets", "monopsony", "exhaustible_resource"),
    "pricing": (
        "price_discrimination",
        "two_part_tariff",
        "bundling",
        "time_pricing",
        "advertising",
    ),
    "uncertainty": ("uncertainty",),
    "information": ("information",),
    "auctions": ("auctions",),
    "regulation": ("regulation",),
    "animation": (
        "animate_costs",
        "animate_monopolistic",
        "animate_monopoly",
        "animate_production",
    ),
}
TOPIC_OF_SCRIPT = {script: topic for topic, scripts in OUTPUT_TOPICS.items() for script in scripts}
FONT_PATTERNS = ("*.otf", "*.ttf")
TEXMF_FONT_DIRS = ("fonts/opentype/public/tex-gyre", "fonts/opentype/public/tex-gyre-math")


def default_output_dir(script: str) -> Path:
    """The folder ``DEFAULT_OUTPUT/<topic>`` of the example script named ``script``."""
    return DEFAULT_OUTPUT / TOPIC_OF_SCRIPT.get(script, script)


def parser(description: str | None) -> argparse.ArgumentParser:
    """An argument parser with the options every example takes; the output folder is per topic."""
    result = argparse.ArgumentParser(description=description)
    result.add_argument(
        "--output-dir",
        type=Path,
        default=default_output_dir(Path(sys.argv[0]).stem),
        help="where to write the figures (default: examples/output/<topic> of the script)",
    )
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
    theme: PlotTheme = config.theme
    if args.language is not None:
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
