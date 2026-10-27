"""Monopoly totals: revenue and cost against output."""

from __future__ import annotations

from collections.abc import Mapping

from mosaickit import (
    Canvas,
    CanvasGrid,
)

from micro_viz.core.theme import PlotTheme
from micro_viz.firm.costs import CostAnalysis
from micro_viz.firm.monopoly import MonopolyOutcome
from micro_viz.firm.monopoly.visuals._base import _PREFIX
from micro_viz.firm.monopoly.visuals.single import monopoly_canvas
from micro_viz.firm.perfect_competition.visuals import (
    PANEL_SIZE,
    _finish,
    _start,
)
from micro_viz.visuals.common import (
    FIGURE_DPI,
    FIGURE_SIZE,
    MARGIN,
    axis_mark,
    curve,
    curve_name,
    dot,
    drop_line,
    pad_range,
)


def monopoly_totals_canvas(
    outcome: MonopolyOutcome,
    *,
    output_range: tuple[float, float],
    samples: int = 121,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Total revenue ``R``, total cost ``TC`` and profit against output, with the maximum
    profit at ``Q_m`` where the slopes of ``R`` and ``TC`` are equal."""
    demand, cost = outcome.demand, outcome.cost
    low, high = output_range
    grid = [low + (high - low) * i / (samples - 1) for i in range(samples)]
    revenue = [(q, demand.price(q) * q) for q in grid]
    total = [(q, cost.total_cost(q)) for q in grid]
    profit = [(q, demand.price(q) * q - cost.total_cost(q)) for q in grid]
    values = [v for _, v in (*revenue, *total, *profit)]
    start = _start(
        theme=theme,
        labels=labels,
        x_symbol=cost.output_symbol,
        x_label=None,
        y_label=None,
        y_text_id="cost.axis.total",
        x_max=high * (1 + margin),
        y_range=pad_range(min(0.0, min(values)), max(values), margin),
        title=title,
        size=size,
        dpi=dpi,
    )
    for name, points, role in (
        ("tr", revenue, "micro.curve.demand"),
        ("tc", total, "micro.curve.total"),
        ("profit", profit, "micro.curve.average.variable"),
    ):
        path = curve(points, layer_id=f"{_PREFIX}.{name}", role=role, model=outcome)
        start.layers.extend(
            (
                path,
                curve_name(
                    path, start.texts(f"monopoly.{'profit_curve' if name == 'profit' else name}")
                ),
            )
        )
    q = outcome.quantity
    start.layers.append(
        drop_line(
            q, demand.price(q) * q, layer_id=f"{_PREFIX}.guide.output", floor=min(0.0, min(values))
        )
    )
    start.layers.append(dot((q, demand.price(q) * q), layer_id=f"{_PREFIX}.point.revenue"))
    start.layers.append(dot((q, cost.total_cost(q)), layer_id=f"{_PREFIX}.point.cost"))
    start.layers.append(
        axis_mark(
            "x",
            q,
            start.texts("monopoly.mark.output", output=cost.output_symbol),
            layer_id=f"{_PREFIX}.mark.output",
        )
    )
    return _finish(start)


def monopoly_totals_grid(
    outcome: MonopolyOutcome,
    analysis: CostAnalysis,
    *,
    titles: tuple[str | None, str | None] = (None, None),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL_SIZE,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """Totals above, unit curves with the profit rectangle below, sharing the optimum ``Q_m``."""
    upper = monopoly_totals_canvas(
        outcome,
        output_range=analysis.output_range,
        title=titles[0],
        theme=theme,
        labels=labels,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    lower = monopoly_canvas(
        outcome,
        analysis,
        profit=True,
        title=titles[1],
        theme=theme,
        labels=labels,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    return CanvasGrid([[upper], [lower]])
