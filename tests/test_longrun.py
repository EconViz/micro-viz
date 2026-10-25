from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from micro_viz import (
    LongRunError,
    PlantFamily,
    lac_lmc_canvas,
    plant_family_canvas,
)

ROOT = Path(__file__).parents[1]
FAMILY = PlantFamily(10.0, 4.0, 1.0, 0.6)


def test_lac_is_lowest_at_the_efficient_scale_and_lmc_cuts_it_there() -> None:
    assert FAMILY.lac(10.0) == pytest.approx(4.0, abs=1e-6)
    assert all(FAMILY.lac(q) >= 4.0 - 1e-9 for q in (3.0, 6.0, 9.0, 11.0, 15.0))
    assert FAMILY.lmc(10.0) == pytest.approx(FAMILY.lac(10.0), abs=1e-3)
    assert FAMILY.lmc(6.0) < FAMILY.lac(6.0)
    assert FAMILY.lmc(14.0) > FAMILY.lac(14.0)


def test_sac_touches_lac_at_the_tangency_with_equal_slopes_and_marginal_costs() -> None:
    plant = 12.0
    touch = FAMILY.tangent_output(plant)
    assert FAMILY.sac(plant, touch) == pytest.approx(FAMILY.lac(touch), abs=1e-6)
    assert FAMILY.smc(plant, touch) == pytest.approx(FAMILY.lmc(touch), abs=1e-2)
    for q in (touch * 0.8, touch * 1.2):
        assert FAMILY.sac(plant, q) >= FAMILY.lac(q) - 1e-9


def test_output_at_lmc_inverts_the_rising_part() -> None:
    q = FAMILY.output_at_lmc(FAMILY.lmc(13.0))
    assert q == pytest.approx(13.0, abs=1e-3)
    with pytest.raises(LongRunError):
        FAMILY.output_at_lmc(0.1)
    with pytest.raises(LongRunError):
        PlantFamily(0.0, 4.0, 1.0, 0.6)


def test_builders_and_example(tmp_path: Path) -> None:
    ids = {layer.id for layer in lac_lmc_canvas(FAMILY, 18.0, title="T").snapshot().layers}
    assert {"micro.longrun.curve.1", "micro.longrun.curve.2"} <= ids
    canvas = plant_family_canvas(FAMILY, (8.0, 10.0, 12.0), 18.0, smc_for=2)
    assert len(canvas.snapshot().layers) > len(ids)
    config = tmp_path / "econ-viz.toml"
    config.write_text('base = "manual"\n', encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "scripts" / "long_run_costs.py"),
            "--output-dir",
            str(tmp_path / "out"),
            "--config",
            str(config),
            "--title",
            "Own title",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    assert "Own title" in (tmp_path / "out" / "lac_lmc.svg").read_text(encoding="utf-8")
