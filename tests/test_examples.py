from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).parents[1]
PRODUCTION_SCRIPT = REPOSITORY_ROOT / "examples" / "scripts" / "production.py"


def test_production_example_renders_both_manual_theme_figures(tmp_path: Path) -> None:
    subprocess.run(
        [sys.executable, str(PRODUCTION_SCRIPT), "--output-dir", str(tmp_path)],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    outputs = (tmp_path / "total_product.svg", tmp_path / "average_marginal_product.svg")
    assert all(output.stat().st_size > 0 for output in outputs)
    combined = "\n".join(output.read_text(encoding="utf-8").lower() for output in outputs)
    assert "#8c8c8c" in combined
    assert "#1a1a1a" in combined
    assert "#377eb8" not in combined
