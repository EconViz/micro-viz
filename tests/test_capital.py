from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

import pytest

from micro_viz import CapitalError, ExhaustibleResourcePath, resource_price_path_canvas

ROOT = Path(__file__).parents[1]
PATH = ExhaustibleResourcePath(100.0, 2.0, 10.0, 0.05, 600.0)


def test_net_price_grows_at_the_interest_rate() -> None:
    for time in (0.0, 5.0, 12.0):
        net_now = PATH.price(time) - PATH.extraction_cost
        net_later = PATH.price(time + 3.0) - PATH.extraction_cost
        assert net_later / net_now == pytest.approx(math.exp(0.05 * 3.0))


def test_path_extracts_exactly_the_stock() -> None:
    steps = 4000
    horizon = PATH.exhaustion_time
    total = sum(PATH.quantity((i + 0.5) * horizon / steps) for i in range(steps)) * horizon / steps
    assert total == pytest.approx(600.0, rel=1e-3)
    assert PATH.price(horizon) == pytest.approx(PATH.choke_price)


def test_higher_interest_rate_starts_lower_and_ends_sooner() -> None:
    faster = ExhaustibleResourcePath(100.0, 2.0, 10.0, 0.10, 600.0)
    assert faster.initial_price < PATH.initial_price
    assert faster.exhaustion_time < PATH.exhaustion_time


def test_bigger_stock_lowers_the_starting_price() -> None:
    larger = ExhaustibleResourcePath(100.0, 2.0, 10.0, 0.05, 900.0)
    assert larger.initial_price < PATH.initial_price
    assert PATH.initial_price > PATH.extraction_cost


def test_invalid_inputs() -> None:
    with pytest.raises(CapitalError):
        ExhaustibleResourcePath(100.0, 2.0, 60.0, 0.05, 600.0)
    with pytest.raises(CapitalError):
        ExhaustibleResourcePath(100.0, 2.0, 10.0, 0.0, 600.0)
    with pytest.raises(CapitalError):
        ExhaustibleResourcePath(100.0, 2.0, 10.0, 0.05, -1.0)


def test_canvas_follows_parameters() -> None:
    grid = resource_price_path_canvas(PATH, titles=("A", "B"))
    assert grid is not None


def test_example_runs(tmp_path: Path) -> None:
    config = tmp_path / "econ-viz.toml"
    config.write_text('base = "manual"\n', encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "scripts" / "exhaustible_resource.py"),
            "--output-dir",
            str(tmp_path / "out"),
            "--config",
            str(config),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    assert (tmp_path / "out" / "resource_price_path.svg").exists()
