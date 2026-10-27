from __future__ import annotations

from mosaickit import CanvasGrid, TextLayer

from micro_viz import (
    CubicCost,
    LinearDemand,
    competitive_profit_grid,
    monopoly_profit_grid,
)


def _ids(grid: CanvasGrid) -> set[str]:
    return {
        layer.id for placement in grid.placements for layer in placement.canvas.snapshot().layers
    }


def test_competitive_profit_grid_links_totals_to_lowercase_pi() -> None:
    grid = competitive_profit_grid(CubicCost(10.0, 5.0, -1.0, 0.1), 8.0, output_max=11.0)
    assert (grid.rows, grid.cols, len(grid.placements)) == (2, 1, 2)
    assert {
        "micro.profit.competitive.tr",
        "micro.profit.competitive.tc",
        "micro.profit.competitive.profit",
    } <= _ids(grid)
    texts = [
        layer.text
        for placement in grid.placements
        for layer in placement.canvas.snapshot().layers
        if isinstance(layer, TextLayer)
    ]
    assert "$\\pi$" in texts


def test_monopoly_profit_grid_uses_hump_shaped_revenue() -> None:
    grid = monopoly_profit_grid(
        LinearDemand(15.0, 0.7),
        CubicCost(8.0, 3.0, -0.3, 0.05),
        output_max=15.0,
    )
    assert {
        "micro.profit.monopoly.tr",
        "micro.profit.monopoly.tc",
        "micro.profit.monopoly.profit",
    } <= _ids(grid)
    assert grid.links
