from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from micro_viz import (
    LongRunError,
    PlantFamily,
    external_scale_effect_canvas,
    lac_lmc_canvas,
    plant_family_canvas,
    scale_cost_canvas,
)

ROOT = Path(__file__).parents[1]
FAMILY = PlantFamily(10.0, 4.0, 1.0, 0.6)


def test_scale_cost_figures_have_two_sac_curves_tangent_to_lac() -> None:
    for regime in ("economies", "constant", "diseconomies"):
        canvas = scale_cost_canvas(regime)  # type: ignore[arg-type]
        ids = {layer.id for layer in canvas.snapshot().layers}
        assert {
            f"micro.longrun.scale.{regime}.lac",
            f"micro.longrun.scale.{regime}.sac.1",
            f"micro.longrun.scale.{regime}.sac.2",
            f"micro.longrun.scale.{regime}.point.1",
            f"micro.longrun.scale.{regime}.point.2",
        } <= ids


def test_external_scale_effects_shift_the_whole_lac_curve() -> None:
    for effect in ("economy", "diseconomy"):
        canvas = external_scale_effect_canvas(effect)  # type: ignore[arg-type]
        ids = {layer.id for layer in canvas.snapshot().layers}
        assert {
            f"micro.longrun.external.{effect}.before",
            f"micro.longrun.external.{effect}.after",
            f"micro.longrun.external.{effect}.arrow",
        } <= ids


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
            str(ROOT / "examples" / "scripts" / "costs" / "long_run_costs.py"),
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


def test_envelope_curves_spread_across_the_axis_and_mark_each_tangency() -> None:
    canvas = plant_family_canvas(FAMILY, (8.0, 10.0, 12.0), 18.0, smc_for=(0, 1, 2))
    ids = {layer.id for layer in canvas.snapshot().layers}
    assert {f"micro.longrun.xmark.{n}" for n in (1, 2, 3)} <= ids
    bare = plant_family_canvas(FAMILY, (8.0, 10.0, 12.0), 18.0, drops=False)
    assert "micro.longrun.xmark.1" not in {layer.id for layer in bare.snapshot().layers}


def test_envelope_figure_touches_lac_and_smc_passes_the_lowest_sac() -> None:
    from micro_viz import EnvelopeFigure

    figure = EnvelopeFigure(6.0, 52.0, 18.0, 8.0, 88.0, 26.0, 76.0, 10.0)
    assert figure.lac(18.0) == pytest.approx(8.0)
    for index, tangent in ((1, 18.0), (3, 88.0)):
        assert figure.sac(index, tangent) == pytest.approx(figure.lac(tangent))
        assert figure.smc(index, tangent) == pytest.approx(figure.lmc(tangent), rel=0.25)
    for q in (5.0, 30.0, 52.0, 70.0, 95.0):
        for index in (1, 2, 3):
            assert figure.sac(index, q) >= figure.lac(q) - 1e-9
    assert figure.minimum_point(2) == (52.0, 6.0)
    for index in (1, 2, 3):
        x, cost = figure.minimum_point(index)
        assert figure.smc(index, x) == pytest.approx(cost)
    assert figure.lmc(52.0) == pytest.approx(figure.lac(52.0))
    assert figure.sac(1, figure.right_output) == pytest.approx(8.0)
    assert figure.sac(2, figure.right_output) == pytest.approx(10.0)
    with pytest.raises(LongRunError):
        EnvelopeFigure(6.0, 52.0, 18.0, 8.0, 88.0, 60.0, 76.0, 10.0)


def test_envelope_figure_labels_find_free_places(tmp_path: Path) -> None:
    import warnings

    from mosaickit.errors import LayoutWarning

    from micro_viz import EnvelopeFigure, envelope_figure_canvas, shared_theme

    figure = EnvelopeFigure(6.0, 52.0, 18.0, 8.0, 88.0, 26.0, 76.0, 10.0)
    canvas = envelope_figure_canvas(figure, 100.0, 12.0, theme=shared_theme("manual"))
    with warnings.catch_warnings():
        warnings.simplefilter("error", LayoutWarning)
        canvas.save(tmp_path / "envelope.svg")
    assert canvas.spec.width > 2 * canvas.spec.height
