from __future__ import annotations

import ast
from importlib.metadata import requires
from pathlib import Path

PACKAGE_ROOT = Path(__file__).parents[1] / "src" / "micro_viz"
DOMAIN_MODULES = {
    "competition",
    "costs",
    "factors",
    "information",
    "monopoly",
    "oligopoly",
    "pricing",
    "production",
    "uncertainty",
}


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


def test_p0_declares_only_mosaickit_as_a_runtime_dependency() -> None:
    assert requires("micro-viz") == ["mosaickit>=1.0.0rc9,<2.0.0"]
