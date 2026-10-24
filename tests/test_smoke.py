from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import cast

from mosaickit import Canvas, Color

REPOSITORY_ROOT = Path(__file__).parents[1]
SCRIPT = REPOSITORY_ROOT / "examples" / "scripts" / "smoke.py"


def _example_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("micro_viz_smoke", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_smoke_canvas_uses_stable_namespaced_layer() -> None:
    module = _example_module()
    canvas = cast(Canvas, module.smoke_canvas())
    assert canvas.spec.title is None
    curve = next(layer for layer in canvas.snapshot().layers if layer.id.startswith("micro."))
    assert curve.id == "micro.scaffold.curve"
    assert curve.role == "micro.scaffold.curve"
    style = canvas.theme.resolve(curve.role, fallback_category=curve.fallback_category)
    assert style.stroke is not None and isinstance(style.stroke.color, Color)
    assert style.stroke.color.to_hex().lower() == "#8c8c8c"


def test_smoke_example_renders_manual_svg(tmp_path: Path) -> None:
    output = tmp_path / "smoke.svg"
    subprocess.run(
        [sys.executable, str(SCRIPT), "--output", str(output)],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    svg = output.read_text(encoding="utf-8")
    assert output.stat().st_size > 0
    assert "#8c8c8c" in svg.lower()
    assert "#1a1a1a" in svg.lower()


def test_title_is_optional() -> None:
    module = _example_module()
    canvas = cast(Canvas, module.smoke_canvas(title="Renderer smoke test"))
    assert canvas.spec.title == "Renderer smoke test"
