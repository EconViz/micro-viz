"""Single-price monopoly, its welfare loss and the tax."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import (
    AxisMarkLayer,
    Canvas,
    Layer,
)

from micro_viz.costs import CostAnalysis
from micro_viz.monopoly import MonopolyOutcome
from micro_viz.theme import PlotTheme
from micro_viz.visuals.common import (
    FIGURE_DPI,
    FIGURE_SIZE,
    MARGIN,
    Range,
    axis_mark,
    dot,
    drop_line,
    region,
)
from micro_viz.visuals.competition import (
    _between,
    _finish,
    _rectangle,
    _Start,
)
from micro_viz.visuals.monopoly._base import (
    _PREFIX,
    _begin,
    _cost_curves,
    _demand_curves,
    _mc_path,
    _point_marks,
    _region_label,
)
from micro_viz.visuals.movement import parallel_arrow


def monopoly_canvas(
    outcome: MonopolyOutcome,
    analysis: CostAnalysis,
    *,
    curves: Sequence[str] = ("mc", "atc"),
    profit: bool = False,
    lost_profit: tuple[float, float] | None = None,
    extra: Sequence[Layer] = (),
    output_mark: bool = True,
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
    """The monopolist: demand ``D`` (= AR), ``MR``, and the cost curves in ``curves``.

    Output ``Q_m`` is where ``MR = MC``; the price ``p_m`` is read off demand. ``profit`` shades
    the rectangle between the price and ATC over ``0..Q_m``; ``lost_profit=(Q_1, Q_2)`` shades
    the profit lost by producing ``Q_1 < Q_m`` or ``Q_2 > Q_m`` (the area between MR and MC).
    """
    demand = outcome.demand
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
    q, price = outcome.quantity, outcome.price
    gap = price - outcome.average_total_cost if outcome.average_total_cost is not None else 0.0
    if (
        profit
        and outcome.average_total_cost is not None
        and q > 0
        and abs(gap) > 1e-9 * max(1.0, price)
    ):
        layer_id = f"{_PREFIX}.profit"
        polygon = _rectangle(0.0, q, outcome.average_total_cost, price)
        start.layers.append(region(polygon, layer_id=layer_id, shade="mid", model=outcome))
        _region_label(start, layer_id, "monopoly.profit")
    if lost_profit is not None:
        first, second = lost_profit
        for name, low, high in (("lower", first, q), ("upper", q, second)):
            mr = [
                (x, outcome.demand.intercept - 2 * outcome.demand.slope * x)
                for x in (low + (high - low) * i / 20 for i in range(21))
            ]
            layer_id = f"{_PREFIX}.lost_profit.{name}"
            start.layers.append(
                region(
                    _between(mr, _mc_path(analysis, low, high)),
                    layer_id=layer_id,
                    shade="light",
                    model=outcome,
                )
            )
            _region_label(start, layer_id, "monopoly.lost_profit")
    _demand_curves(start, demand, model=outcome)
    _cost_curves(start, analysis, curves)
    _point_marks(start, symbol, q, price, mark_id="monopoly", output_mark=output_mark)
    start.layers.append(dot((q, price), layer_id=f"{_PREFIX}.point.monopoly"))
    start.layers.append(dot((q, outcome.marginal_cost), layer_id=f"{_PREFIX}.point.mr_mc"))
    if lost_profit is not None:
        for index, value in enumerate(lost_profit, start=1):
            start.layers.append(
                drop_line(
                    value,
                    analysis.cost.marginal_cost(value),
                    layer_id=f"{_PREFIX}.guide.lost.{index}",
                )
            )
            start.layers.append(
                dot(
                    (value, analysis.cost.marginal_cost(value)),
                    layer_id=f"{_PREFIX}.point.lost.{index}",
                )
            )
            start.layers.append(
                _x_mark(start, symbol, value, f"{_PREFIX}.mark.lost.{index}", index)
            )
    start.layers.extend(extra)
    return _finish(start)


def _x_mark(start: _Start, symbol: str, value: float, layer_id: str, index: int) -> AxisMarkLayer:
    return axis_mark(
        "x",
        value,
        start.texts("monopoly.mark.output_index", output=symbol, index=index),
        layer_id=layer_id,
    )


def monopoly_dwl_canvas(
    outcome: MonopolyOutcome,
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
    """Monopoly against the competitive outcome ``p = MC``: a transfer rectangle and the
    deadweight-loss triangle between demand and MC from ``Q_m`` to ``Q_c``."""
    demand = outcome.demand
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
    qm, pm = outcome.quantity, outcome.price
    qc, pc = outcome.competitive_quantity, outcome.competitive_price
    transfer_id = f"{_PREFIX}.transfer"
    start.layers.append(
        region(_rectangle(0.0, qm, pc, pm), layer_id=transfer_id, shade="mid", model=outcome)
    )
    _region_label(start, transfer_id, "monopoly.transfer")
    loss_id = f"{_PREFIX}.dwl"
    upper = [(x, demand.price(x)) for x in (qm + (qc - qm) * i / 20 for i in range(21))]
    start.layers.append(
        region(
            _between(upper, _mc_path(analysis, qm, qc)),
            layer_id=loss_id,
            shade="dark",
            model=outcome,
        )
    )
    _region_label(start, loss_id, "monopoly.dwl")
    _demand_curves(start, demand, model=outcome)
    _cost_curves(start, analysis, ("mc",))
    _point_marks(start, symbol, qm, pm, mark_id="monopoly")
    _point_marks(
        start,
        symbol,
        qc,
        pc,
        mark_id="competitive",
        output_key="monopoly.mark.output_competitive",
        price_key="monopoly.mark.price_competitive",
    )
    start.layers.append(dot((qm, pm), layer_id=f"{_PREFIX}.point.monopoly"))
    start.layers.append(dot((qc, pc), layer_id=f"{_PREFIX}.point.competitive"))
    return _finish(start)


def monopoly_tax_canvas(
    before: MonopolyOutcome,
    after: MonopolyOutcome,
    analysis_before: CostAnalysis,
    analysis_after: CostAnalysis,
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
    """A per-unit tax lifts MC (thin solid ``MC'``); the arrow rises from the old MC at ``Q_m``
    to the new one and the price moves from ``p_m`` to ``p'``."""
    demand = before.demand
    symbol = analysis_before.cost.output_symbol
    start = _begin(
        demand,
        analysis_after,
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
    _demand_curves(start, demand, model=before)
    _cost_curves(start, analysis_before, ("mc",))
    _cost_curves(
        start,
        analysis_after,
        ("mc",),
        role="micro.curve.after",
        key_suffix="_after",
        suffix=".after",
    )
    _point_marks(start, symbol, before.quantity, before.price, mark_id="before")
    _point_marks(
        start,
        symbol,
        after.quantity,
        after.price,
        mark_id="after",
        output_key="monopoly.mark.output_after",
        price_key="monopoly.mark.price_after",
    )
    start.layers.append(dot((before.quantity, before.price), layer_id=f"{_PREFIX}.point.before"))
    start.layers.append(dot((after.quantity, after.price), layer_id=f"{_PREFIX}.point.after"))
    old = (before.quantity, before.marginal_cost)
    new = (before.quantity, analysis_after.cost.marginal_cost(before.quantity))
    start.layers.append(
        parallel_arrow(old, new, layer_id=f"{_PREFIX}.arrow.tax", label=start.texts("monopoly.tax"))
    )
    return _finish(start)
