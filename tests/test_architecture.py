from __future__ import annotations

import ast
import subprocess
import sys
import textwrap
from importlib.metadata import requires
from pathlib import Path

PACKAGE_ROOT = Path(__file__).parents[1] / "src" / "micro_viz"
DOMAIN_MODULES = {
    "firm/competition",
    "firm/costs",
    "firm/monopoly",
    "firm/oligopoly",
    "firm/production",
    "firm/strategy/pricing",
    "markets/factors",
    "markets/information",
    "risk/uncertainty",
}

TOP_LEVEL_PACKAGES = {"_api", "animation", "core", "firm", "markets", "risk", "visuals"}


def test_package_root_contains_only_broad_domains_and_required_files() -> None:
    directories = {
        path.name for path in PACKAGE_ROOT.iterdir() if path.is_dir() and path.name != "__pycache__"
    }
    files = {path.name for path in PACKAGE_ROOT.iterdir() if path.is_file()}

    assert directories == TOP_LEVEL_PACKAGES
    assert files == {"__init__.py", "py.typed"}


def test_shared_visuals_root_contains_only_rendering_infrastructure() -> None:
    root = PACKAGE_ROOT / "visuals"
    directories = {
        path.name for path in root.iterdir() if path.is_dir() and path.name != "__pycache__"
    }
    files = {path.name for path in root.iterdir() if path.is_file()}

    assert directories == set()
    assert files == {"__init__.py", "axes.py", "common.py", "movement.py", "plane.py"}


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_package_never_imports_rendering_backends() -> None:
    forbidden = ("matplotlib", "plotly", "seaborn")
    offenders = {
        path.relative_to(PACKAGE_ROOT): sorted(
            name
            for name in _imports(path)
            if any(name == root or name.startswith(f"{root}.") for root in forbidden)
        )
        for path in PACKAGE_ROOT.rglob("*.py")
        if any(
            name == root or name.startswith(f"{root}.")
            for name in _imports(path)
            for root in forbidden
        )
    }
    assert offenders == {}


def test_future_domain_modules_stay_independent_of_mosaickit() -> None:
    offenders = {
        path.relative_to(PACKAGE_ROOT): sorted(
            name for name in _imports(path) if name == "mosaickit" or name.startswith("mosaickit.")
        )
        for module in DOMAIN_MODULES
        for path in (PACKAGE_ROOT / module).rglob("*.py")
        if (PACKAGE_ROOT / module).is_dir()
        if any(name == "mosaickit" or name.startswith("mosaickit.") for name in _imports(path))
    }
    assert offenders == {}


def test_only_mosaickit_is_required_and_kinetickit_is_an_optional_extra() -> None:
    declared = requires("micro-viz") or []
    required = [item for item in declared if "extra ==" not in item]
    optional = [item for item in declared if "extra ==" in item]
    assert required == ["mosaickit>=1.0.0rc16,<2.0.0"]
    assert len(optional) == 1 and optional[0].startswith("kinetickit[raster]")
    assert "extra == 'animation'" in optional[0]


def test_only_the_animation_package_imports_kinetickit() -> None:
    offenders = {
        path.relative_to(PACKAGE_ROOT): sorted(
            name
            for name in _imports(path)
            if name == "kinetickit" or name.startswith("kinetickit.")
        )
        for path in PACKAGE_ROOT.rglob("*.py")
        if "animation" not in path.relative_to(PACKAGE_ROOT).parts
        and any(name == "kinetickit" or name.startswith("kinetickit.") for name in _imports(path))
    }
    assert offenders == {}


def test_static_figures_work_without_kinetickit() -> None:
    code = textwrap.dedent(
        """
        import sys
        sys.modules["kinetickit"] = None
        from micro_viz import (
            ShortRunProductionFunction, analyze_production, total_product_canvas,
        )
        import micro_viz.animation
        canvas = total_product_canvas(
            analyze_production(ShortRunProductionFunction(6, 3, -0.5), input_range=(0, 6))
        )
        assert canvas.snapshot().layers
        try:
            micro_viz.animation.save_svg(lambda value: canvas, [1.0, 2.0], "unused.svg")
        except ImportError as error:
            assert "micro-viz[animation]" in str(error)
        else:
            raise SystemExit("save_svg needs kinetickit")
        """
    )
    result = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_expression_engine_is_detachable() -> None:
    """``micro_viz.core.expr`` imports nothing else of micro-viz, and nothing reaches into it."""
    for path in (PACKAGE_ROOT / "core" / "expr").rglob("*.py"):
        for name in _imports(path):
            if name == "micro_viz" or name.startswith("micro_viz."):
                assert name == "micro_viz.core.expr" or name.startswith("micro_viz.core.expr."), (
                    f"{path.name} imports {name}"
                )
    for path in PACKAGE_ROOT.rglob("*.py"):
        if path.relative_to(PACKAGE_ROOT).parts[:2] == ("core", "expr"):
            continue
        for name in _imports(path):
            assert not name.startswith("micro_viz.core.expr."), f"{path.name} reaches into {name}"
