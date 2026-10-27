from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from mosaickit import CanvasGrid, PathLayer

from micro_viz import (
    CapacityConstrainedProductionFunction,
    ProductionError,
    QuadraticProductionFunction,
    ShortRunProductionFunction,
    capacity_production_grid,
    quadratic_production_grid,
    rational_production_region_grid,
    shared_theme,
)
from micro_viz.firm.visuals import production, production_forms


def test_chapter_package_preserves_legacy_production_form_imports() -> None:
    assert production.quadratic_production_grid is production_forms.quadratic_production_grid
    assert production.capacity_production_grid is production_forms.capacity_production_grid
    assert (
        production.rational_production_region_grid
        is production_forms.rational_production_region_grid
    )


def test_quadratic_products_and_boundary_inputs() -> None:
    function = QuadraticProductionFunction(productivity=12.0, curvature=1.0)

    assert function.total_product_max_input == pytest.approx(6.0)
    assert function.zero_output_input == pytest.approx(12.0)
    assert function.total_product(6.0) == pytest.approx(36.0)
    assert function.average_product(6.0) == pytest.approx(6.0)
    assert function.marginal_product(6.0) == pytest.approx(0.0)
    assert function.average_product(0.0) is None


def test_capacity_products_change_at_the_capacity_input() -> None:
    function = CapacityConstrainedProductionFunction(productivity=4.0, capacity=16.0)

    assert function.capacity_input == pytest.approx(4.0)
    assert function.total_product(3.0) == pytest.approx(12.0)
    assert function.total_product(6.0) == pytest.approx(16.0)
    assert function.average_product(8.0) == pytest.approx(2.0)
    assert function.marginal_product(3.0) == pytest.approx(4.0)
    assert function.marginal_product(4.0) is None
    assert function.marginal_product(5.0) == pytest.approx(0.0)


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    "factory",
    [
        lambda: QuadraticProductionFunction(0.0, 1.0),
        lambda: QuadraticProductionFunction(1.0, -1.0),
        lambda: CapacityConstrainedProductionFunction(1.0, 0.0),
    ],
)
def test_production_form_parameters_must_be_positive(factory: Callable[[], object]) -> None:
    with pytest.raises(ProductionError, match="positive"):
        factory()


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    ("grid", "boundary"),
    [
        (quadratic_production_grid(QuadraticProductionFunction(12.0, 1.0)), 6.0),
        (
            capacity_production_grid(CapacityConstrainedProductionFunction(4.0, 16.0)),
            4.0,
        ),
    ],
)
def test_alternative_production_grids_align_the_boundary(
    grid: CanvasGrid, boundary: float, tmp_path: Path
) -> None:
    assert grid.rows == 2 and grid.cols == 1
    (link,) = grid.links
    assert link.start[0] == pytest.approx(boundary)
    assert link.end[0] == pytest.approx(boundary)

    upper, lower = (placement.canvas for placement in grid.placements)
    upper_curves = [layer for layer in upper.snapshot().layers if isinstance(layer, PathLayer)]
    lower_curves = [layer for layer in lower.snapshot().layers if isinstance(layer, PathLayer)]
    assert any(layer.role == "micro.curve.total" for layer in upper_curves)
    assert any(layer.role == "micro.curve.average" for layer in lower_curves)
    assert any(layer.role == "micro.curve.marginal" for layer in lower_curves)

    output = tmp_path / f"{boundary}.svg"
    grid.save(output, renderer="matplotlib")
    assert output.stat().st_size > 0


def test_alternative_production_grids_render_in_manual_theme(tmp_path: Path) -> None:
    theme = shared_theme("manual")
    quadratic_production_grid(QuadraticProductionFunction(12.0, 1.0), theme=theme).save(
        tmp_path / "quadratic.svg"
    )
    capacity_production_grid(CapacityConstrainedProductionFunction(4.0, 16.0), theme=theme).save(
        tmp_path / "capacity.svg"
    )
    assert (tmp_path / "quadratic.svg").stat().st_size > 0
    assert (tmp_path / "capacity.svg").stat().st_size > 0


def test_rational_region_reverses_capital_and_aligns_both_boundaries(tmp_path: Path) -> None:
    labor = ShortRunProductionFunction(0.0, 3.0, -0.4)
    capital = ShortRunProductionFunction(0.0, 3.0, -0.4)
    grid = rational_production_region_grid(labor, capital, theme=shared_theme("manual"))

    assert len(grid.links) == 2
    left, right = grid.links
    assert left.start[0] == pytest.approx(labor.average_product_max_input)
    assert right.start[0] == pytest.approx(labor.total_product_max_input)
    assert left.start[0] == pytest.approx(left.end[0])
    assert right.start[0] == pytest.approx(right.end[0])
    lower = grid.placements[1].canvas
    layers = {layer.id: layer for layer in lower.snapshot().layers}
    x_axis = layers["axes.x"]
    assert isinstance(x_axis, PathLayer)
    assert x_axis.path[0][0] > x_axis.path[-1][0]

    output = tmp_path / "rational.svg"
    grid.save(output)
    svg = output.read_text(encoding="utf-8")
    assert "micro.production.rational.labor" in svg
    assert "micro.production.rational.capital" in svg
