from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from micro_viz import (
    IntertemporalPricing,
    LinearDemand,
    PeakLoadPricing,
    PricingError,
    intertemporal_pricing_canvas,
    peak_load_canvas,
)

ROOT = Path(__file__).parents[1]
FIRST = LinearDemand(30.0, 1.0)
SECOND = LinearDemand(22.0, 1.0)


def test_each_group_priced_where_mr_equals_mc() -> None:
    result = IntertemporalPricing(FIRST, SECOND, 4.0).solve()
    assert result.first_price == pytest.approx(17.0)
    assert result.second_price == pytest.approx(13.0)
    assert result.first_price > result.second_price
    assert result.first_quantity == pytest.approx(13.0)
    assert result.profit == pytest.approx(13.0 * 13.0 + 9.0 * 9.0)


def test_later_group_must_value_less() -> None:
    with pytest.raises(PricingError):
        IntertemporalPricing(SECOND, FIRST, 4.0)


def test_capacity_cost_falls_on_the_peak() -> None:
    model = PeakLoadPricing(LinearDemand(30.0, 1.0), LinearDemand(20.0, 1.0), 4.0, 6.0)
    result = model.solve()
    assert not result.shared_capacity
    assert result.peak_price > result.off_peak_price
    peak_mr = 30.0 - 2.0 * result.peak_quantity
    assert peak_mr == pytest.approx(4.0 + 6.0)
    off_mr = 20.0 - 2.0 * result.off_peak_quantity
    assert off_mr == pytest.approx(4.0)
    assert result.capacity == pytest.approx(result.peak_quantity)


def test_shared_capacity_when_off_peak_is_large() -> None:
    model = PeakLoadPricing(LinearDemand(30.0, 1.0), LinearDemand(29.0, 1.0), 4.0, 10.0)
    result = model.solve()
    assert result.shared_capacity
    assert result.peak_quantity == pytest.approx(result.off_peak_quantity)
    mr_sum = (30.0 - 2 * result.capacity) + (29.0 - 2 * result.capacity)
    assert mr_sum == pytest.approx(2 * 4.0 + 10.0)


def test_invalid_costs() -> None:
    with pytest.raises(PricingError):
        PeakLoadPricing(FIRST, SECOND, -1.0, 1.0)
    with pytest.raises(PricingError):
        IntertemporalPricing(FIRST, SECOND, float("nan"))


def test_canvases_follow_parameters() -> None:
    assert intertemporal_pricing_canvas(IntertemporalPricing(FIRST, SECOND, 4.0), title="T")
    plain = peak_load_canvas(PeakLoadPricing(FIRST, SECOND, 4.0, 0.0)).snapshot().layers
    costly = peak_load_canvas(PeakLoadPricing(FIRST, SECOND, 4.0, 3.0)).snapshot().layers
    assert len(costly) > len(plain)


def test_example_runs(tmp_path: Path) -> None:
    config = tmp_path / "econ-viz.toml"
    config.write_text('base = "manual"\n', encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "scripts" / "time_pricing.py"),
            "--output-dir",
            str(tmp_path / "out"),
            "--config",
            str(config),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    assert (tmp_path / "out" / "peak_load.svg").exists()
