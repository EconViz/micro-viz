from importlib.metadata import entry_points, version

import micro_viz


def test_version_matches_installed_metadata() -> None:
    assert micro_viz.__version__ == "0.1.0.dev0"
    assert version("micro-viz") == micro_viz.__version__


def test_config_entry_point_is_registered() -> None:
    matches = [entry for entry in entry_points(group="econviz.config") if entry.name == "micro"]
    assert len(matches) == 1
    assert matches[0].load() is micro_viz.Config


def test_public_api_is_explicit() -> None:
    assert set(micro_viz.__all__) == {
        "Config",
        "MarginalReturns",
        "PlotTheme",
        "ProductionAnalysis",
        "ProductionError",
        "ProductionPoint",
        "ReturnsRegion",
        "ShortRunProductionFunction",
        "__version__",
        "analyze_production",
        "default_theme",
        "shared_theme",
    }
