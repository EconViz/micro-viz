from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from micro_viz import (
    BundlingError,
    Offer,
    ValuationProfile,
    best_mixed,
    best_pure,
    best_separate,
    choice,
    choice_regions,
    evaluate_offer,
    mixed_bundling_canvas,
    pure_bundling_canvas,
    separate_selling_regions_canvas,
    valuation_scatter_canvas,
)

ROOT = Path(__file__).parents[1]
NEGATIVE = ValuationProfile.correlated(16, low=10.0, high=90.0, direction=-1.0, spread=8.0)
COSTLY = ValuationProfile.correlated(
    16, low=10.0, high=90.0, direction=-1.0, spread=8.0, cost_1=15.0, cost_2=15.0
)


def _inside(polygon: tuple[tuple[float, float], ...], x: float, y: float) -> bool:
    sign = 0
    for a, b in zip(polygon, [*polygon[1:], polygon[0]], strict=True):
        cross = (b[0] - a[0]) * (y - a[1]) - (b[1] - a[1]) * (x - a[0])
        if abs(cross) < 1e-9:
            continue
        step = 1 if cross > 0 else -1
        if sign and step != sign:
            return False
        sign = step
    return True


def test_regions_match_choice() -> None:
    for offer in (Offer.separate(30.0, 50.0), Offer.pure(80.0), Offer.mixed(60.0, 55.0, 90.0)):
        regions = choice_regions(offer, 100.0)
        for r1 in range(1, 100, 7):
            for r2 in range(1, 100, 9):
                picked = choice(offer, r1 + 0.31, r2 + 0.17)
                assert _inside(regions[picked], r1 + 0.31, r2 + 0.17)


def test_pure_bundle_diagonal() -> None:
    offer = Offer.pure(80.0)
    assert choice(offer, 50.0, 31.0) == "bundle"
    assert choice(offer, 50.0, 29.0) == "none"


def test_mixed_never_below_separate_or_pure() -> None:
    for profile in (NEGATIVE, COSTLY):
        mixed = best_mixed(profile).profit
        assert mixed >= best_separate(profile).profit - 1e-9
        assert mixed >= best_pure(profile).profit - 1e-9


def test_pure_bundling_beats_separate_when_negatively_correlated() -> None:
    assert best_pure(NEGATIVE).profit >= best_separate(NEGATIVE).profit - 1e-9


def test_profit_counts_cost_of_each_good() -> None:
    profile = ValuationProfile(((60.0, 60.0),), cost_1=10.0, cost_2=20.0)
    outcome = evaluate_offer(profile, Offer.pure(100.0))
    assert outcome.revenue == pytest.approx(100.0)
    assert outcome.profit == pytest.approx(70.0)


def test_invalid_inputs() -> None:
    with pytest.raises(BundlingError):
        ValuationProfile(())
    with pytest.raises(BundlingError):
        ValuationProfile(((-1.0, 2.0),))
    with pytest.raises(BundlingError):
        ValuationProfile.correlated(1, low=1.0, high=2.0, direction=1.0, spread=0.0)


def test_canvases_build() -> None:
    offer = best_mixed(COSTLY).offer
    assert valuation_scatter_canvas(NEGATIVE, ("A", "B")) is not None
    assert separate_selling_regions_canvas(NEGATIVE, best_separate(NEGATIVE).offer) is not None
    assert pure_bundling_canvas(NEGATIVE, 90.0) is not None
    assert mixed_bundling_canvas(COSTLY, offer) is not None
    assert mixed_bundling_canvas(COSTLY, offer, numbered=True, title="T") is not None


def test_example_runs(tmp_path: Path) -> None:
    config = tmp_path / "econ-viz.toml"
    config.write_text('base = "manual"\n', encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "scripts" / "bundling.py"),
            "--output-dir",
            str(tmp_path / "out"),
            "--config",
            str(config),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    assert (tmp_path / "out" / "mixed_bundling.svg").exists()
