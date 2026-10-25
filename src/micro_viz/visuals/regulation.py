"""mosaickit visual builders for the regulation of a monopoly."""

from __future__ import annotations

from collections.abc import Mapping

from mosaickit import Canvas

from micro_viz.costs import CostAnalysis
from micro_viz.regulation import CeilingOutcome, NaturalMonopolyPricing
from micro_viz.theme import PlotTheme
from micro_viz.visuals.common import (
    FIGURE_DPI,
    FIGURE_SIZE,
    MARGIN,
    Range,
    curve,
    curve_name,
    dot,
    region,
)
from micro_viz.visuals.competition import _finish, _rectangle
from micro_viz.visuals.monopoly import (
    _begin,
    _cost_curves,
    _demand_curves,
    _point_marks,
    _region_label,
)

_PREFIX = "micro.regulation"


def price_ceiling_canvas(
    outcome: CeilingOutcome,
    analysis: CostAnalysis,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    x_label: str | None = None,
    y_label: str | None = None,
    x_max: float | None = None,
    y_range: Range | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """A price ceiling: average revenue is flat at the ceiling up to ``Q_max`` and marginal
    revenue equals the ceiling there, then jumps down to the unregulated ``MR``."""
    demand = outcome.unregulated.demand
    symbol = analysis.cost.output_symbol
    start = _begin(
        demand,
        analysis,
        theme=theme,
        labels=labels,
        x_label=x_label,
        y_label=y_label,
        x_max=x_max,
        y_range=y_range,
        margin=margin,
        title=title,
        size=size,
        dpi=dpi,
    )
    _demand_curves(start, demand, model=outcome.unregulated)
    ceiling, qmax = outcome.ceiling, outcome.ceiling_quantity
    flat = curve(
        ((0.0, ceiling), (qmax, ceiling)),
        layer_id=f"{_PREFIX}.ceiling",
        role="micro.curve.after",
    )
    start.layers.extend((flat, curve_name(flat, start.texts("regulation.ceiling_curve"))))
    drop = curve(
        ((qmax, max(outcome.marginal_revenue(qmax), 0.0)), (qmax, ceiling)),
        layer_id=f"{_PREFIX}.mr_drop",
        role="micro.curve.after",
    )
    start.layers.append(drop)
    _cost_curves(start, analysis, ("mc", "atc"))
    _point_marks(
        start,
        symbol,
        outcome.unregulated.quantity,
        outcome.unregulated.price,
        mark_id="unregulated",
    )
    _point_marks(
        start,
        symbol,
        outcome.quantity,
        outcome.price,
        mark_id="regulated",
        output_key="regulation.mark.output_ac",
        price_key="regulation.mark.ceiling",
    )
    start.layers.append(
        dot(
            (outcome.unregulated.quantity, outcome.unregulated.price), layer_id=f"{_PREFIX}.point.m"
        )
    )
    start.layers.append(dot((outcome.quantity, outcome.price), layer_id=f"{_PREFIX}.point.r"))
    return _finish(start)


def natural_monopoly_canvas(
    pricing: NaturalMonopolyPricing,
    analysis: CostAnalysis,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    x_label: str | None = None,
    y_label: str | None = None,
    x_max: float | None = None,
    y_range: Range | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """A natural monopoly with falling ATC: the unregulated price, ``P = MC`` (with the loss
    shaded) and ``P = ATC`` (no profit)."""
    demand = pricing.demand
    symbol = analysis.cost.output_symbol
    start = _begin(
        demand,
        analysis,
        theme=theme,
        labels=labels,
        x_label=x_label,
        y_label=y_label,
        x_max=x_max,
        y_range=y_range,
        margin=margin,
        title=title,
        size=size,
        dpi=dpi,
    )
    mc_point = pricing.marginal_cost
    atc = analysis.cost.average_total_cost(mc_point.quantity) or mc_point.price
    if atc - mc_point.price > 1e-9:
        layer_id = f"{_PREFIX}.loss"
        polygon = _rectangle(0.0, mc_point.quantity, mc_point.price, atc)
        start.layers.append(region(polygon, layer_id=layer_id, shade="mid", model=pricing))
        _region_label(start, layer_id, "regulation.loss")
    _demand_curves(start, demand, model=pricing)
    _cost_curves(start, analysis, ("mc", "atc"))
    _point_marks(
        start, symbol, pricing.unregulated.quantity, pricing.unregulated.price, mark_id="m"
    )
    _point_marks(
        start,
        symbol,
        mc_point.quantity,
        mc_point.price,
        mark_id="mc",
        output_key="regulation.mark.output_mc",
        price_key="regulation.mark.price_mc",
    )
    average = pricing.average_cost
    _point_marks(
        start,
        symbol,
        average.quantity,
        average.price,
        mark_id="ac",
        output_key="regulation.mark.output_ac",
        price_key="regulation.mark.price_ac",
    )
    for name, point in (("m", pricing.unregulated), ("mc", mc_point), ("ac", average)):
        start.layers.append(dot((point.quantity, point.price), layer_id=f"{_PREFIX}.point.{name}"))
    return _finish(start)


__all__ = ["natural_monopoly_canvas", "price_ceiling_canvas"]
