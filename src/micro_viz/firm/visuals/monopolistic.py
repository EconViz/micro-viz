"""mosaickit figure builders for monopolistic competition."""

from __future__ import annotations

from collections.abc import Mapping

from mosaickit import Canvas, CanvasGrid

from micro_viz.core.theme import PlotTheme
from micro_viz.firm.competition import solve_competitive_firm
from micro_viz.firm.costs import CostAnalysis
from micro_viz.firm.monopolistic.model import MonopolisticOutcome
from micro_viz.firm.visuals.competition import PANEL_SIZE, competitive_firm_canvas
from micro_viz.firm.visuals.monopoly import monopoly_canvas
from micro_viz.visuals.common import (
    FIGURE_DPI,
    MARGIN,
    Range,
    Texts,
    pad_range,
    region_brace,
    resolve_theme,
)


def monopolistic_long_run_canvas(
    outcome: MonopolisticOutcome,
    analysis: CostAnalysis,
    *,
    excess_capacity: bool = False,
    y_range: Range | None = None,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """The long run: demand tangent to ATC at the output where ``MR = MC``, price above MC.

    ``excess_capacity`` braces the output between the long-run output and the output at
    minimum ATC.
    """
    texts = Texts(resolve_theme(theme), labels)
    y_range = y_range or pad_range(0.0, outcome.short_run.demand.intercept, margin)
    extra = []
    if excess_capacity:
        extra.append(
            region_brace(
                outcome.long_run.quantity,
                outcome.minimum_atc_output,
                outcome.minimum_atc * 0.0,
                texts("monopolistic.excess_capacity"),
                layer_id="micro.monopolistic.brace.excess",
            )
        )
    return monopoly_canvas(
        outcome.long_run,
        analysis,
        extra=extra,
        output_mark=not excess_capacity,
        y_range=y_range,
        title=title,
        theme=theme,
        labels=labels,
        margin=margin,
        size=size,
        dpi=dpi,
    )


def monopolistic_short_run_canvas(
    outcome: MonopolisticOutcome,
    analysis: CostAnalysis,
    *,
    y_range: Range | None = None,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """The short run: the monopoly optimum with the profit rectangle before entry."""
    return monopoly_canvas(
        outcome.short_run,
        analysis,
        profit=True,
        y_range=y_range,
        title=title,
        theme=theme,
        labels=labels,
        margin=margin,
        size=size,
        dpi=dpi,
    )


def monopolistic_competition_grid(
    outcome: MonopolisticOutcome,
    analysis: CostAnalysis,
    *,
    titles: tuple[str | None, str | None] = (None, None),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL_SIZE,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """Short run (profit rectangle) beside the long run after entry (tangency, no profit)."""
    short = monopolistic_short_run_canvas(
        outcome,
        analysis,
        title=titles[0],
        theme=theme,
        labels=labels,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    longer = monopolistic_long_run_canvas(
        outcome,
        analysis,
        title=titles[1],
        theme=theme,
        labels=labels,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    return CanvasGrid([[short, longer]])


def excess_capacity_grid(
    outcome: MonopolisticOutcome,
    analysis: CostAnalysis,
    *,
    titles: tuple[str | None, str | None] = (None, None),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL_SIZE,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """Monopolistic competition (price above MC, excess capacity) beside perfect competition
    (``p = MC`` at minimum ATC)."""
    monopolistic = monopolistic_long_run_canvas(
        outcome,
        analysis,
        excess_capacity=True,
        title=titles[0],
        theme=theme,
        labels=labels,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    perfect = competitive_firm_canvas(
        analysis,
        solve_competitive_firm(analysis.cost, outcome.minimum_atc),
        y_range=pad_range(0.0, outcome.short_run.demand.intercept, margin),
        title=titles[1],
        theme=theme,
        labels=labels,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    return CanvasGrid([[monopolistic, perfect]])


__all__ = [
    "excess_capacity_grid",
    "monopolistic_competition_grid",
    "monopolistic_long_run_canvas",
    "monopolistic_short_run_canvas",
]
