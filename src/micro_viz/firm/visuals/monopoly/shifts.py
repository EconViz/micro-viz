"""Demand shifts, multiplant monopoly and the Lerner markup."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import (
    Canvas,
    CanvasGrid,
    GridLink,
    SpanBraceLayer,
)

from micro_viz.core.theme import PlotTheme
from micro_viz.firm.costs import CostAnalysis
from micro_viz.firm.monopoly import MonopolyOutcome, MultiplantMonopoly, MultiplantOutcome
from micro_viz.firm.visuals.competition import (
    PANEL_SIZE,
    _finish,
    _level_mark,
    _start,
)
from micro_viz.firm.visuals.monopoly._base import (
    _PREFIX,
    _begin,
    _cost_curves,
    _demand_curves,
    _point_marks,
)
from micro_viz.firm.visuals.monopoly.single import _x_mark
from micro_viz.visuals.common import (
    FIGURE_DPI,
    FIGURE_SIZE,
    MARGIN,
    Range,
    curve,
    curve_name,
    dot,
    drop_line,
    guide,
    pad_range,
)
from micro_viz.visuals.movement import parallel_arrow, rotation_arrow


def monopoly_demand_shift_canvas(
    before: MonopolyOutcome,
    after: MonopolyOutcome,
    analysis: CostAnalysis,
    *,
    rotate: bool = False,
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
    """Demand moves (thin solid ``D'`` and ``MR'``): a parallel shift or, with ``rotate``, a
    change of slope around the quantity-axis end. A monopolist has no supply curve, so the same
    price can go with different outputs, and the new optimum is read off ``MR' = MC``."""
    old_demand, new_demand = before.demand, after.demand
    symbol = analysis.cost.output_symbol
    reach = max(old_demand.intercept, new_demand.intercept)
    start = _begin(
        old_demand,
        analysis,
        theme=theme,
        labels=labels,
        x_label=x_label,
        y_label=y_label,
        x_max=x_max,
        y_range=y_range or pad_range(0.0, reach, margin),
        margin=margin,
        title=title,
        size=size,
        dpi=dpi,
    )
    start.x_axis = (0.0, max(start.x_axis[1], new_demand.quantity_intercept * (1 + margin)))
    _demand_curves(start, old_demand, model=before)
    _demand_curves(
        start,
        new_demand,
        key="monopoly.demand_after",
        mr_key="monopoly.mr_after",
        suffix=".after",
        role="micro.curve.after.demand",
        mr_role="micro.curve.after",
        along=1.0,
        model=after,
    )
    _cost_curves(start, analysis, ("mc",))
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
    if rotate:
        far = old_demand.quantity_intercept
        start.layers.append(
            rotation_arrow(
                (far * 0.9, old_demand.price(far * 0.9)),
                (far * 0.9, new_demand.price(far * 0.9)),
                layer_id=f"{_PREFIX}.arrow.demand",
            )
        )
    else:
        level = before.price
        start.layers.append(
            parallel_arrow(
                (before.quantity, level),
                (new_demand.quantity(level), level),
                layer_id=f"{_PREFIX}.arrow.demand",
            )
        )
    return _finish(start)


def multiplant_canvas(
    firm: MultiplantMonopoly,
    outcome: MultiplantOutcome,
    *,
    titles: tuple[str | None, ...] | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL_SIZE,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """Each plant's MC beside the horizontally summed ``MC_T`` against ``D`` and ``MR``.

    The level ``MC*`` where ``MR = MC_T`` is carried across the panels by dashed links; each plant
    produces where its own MC reaches it.
    """
    demand = firm.demand
    top = demand.intercept
    ceiling = pad_range(0.0, top, margin)
    names = titles or tuple(None for _ in range(len(firm.plants) + 1))
    cells: list[Canvas] = []
    level = outcome.marginal_cost
    for index, plant in enumerate(firm.plants):
        output = outcome.plant_outputs[index]
        reach = max(firm.outputs_at(top)[index], output) * (1 + margin)
        start = _start(
            theme=theme,
            labels=labels,
            x_symbol=plant.output_symbol,
            x_label=None,
            y_label=None,
            y_text_id="competition.axis.price",
            x_max=reach,
            y_range=ceiling,
            title=names[index],
            size=size,
            dpi=dpi,
        )
        low = plant.marginal_cost(0.0)
        points = [
            (firm.outputs_at(m)[index], m)
            for m in (min(low, top) + (top - min(low, top)) * i / 60 for i in range(61))
        ]
        path = curve(points, layer_id=f"{_PREFIX}.plant.{index + 1}", role="micro.curve.marginal")
        start.layers.extend(
            (path, curve_name(path, start.texts("monopoly.plant", index=index + 1)))
        )
        start.layers.append(
            guide((0.0, level), (reach, level), layer_id=f"{_PREFIX}.guide.plant.{index + 1}")
        )
        if index == 0:
            _level_mark(start, level, "monopoly.mark.marginal", mark_id="level", dotted=False)
        start.layers.append(
            drop_line(output, level, layer_id=f"{_PREFIX}.guide.plant.{index + 1}.output")
        )
        start.layers.append(dot((output, level), layer_id=f"{_PREFIX}.point.plant.{index + 1}"))
        start.layers.append(
            _x_mark(
                start, plant.output_symbol, output, f"{_PREFIX}.mark.plant.{index + 1}", index + 1
            )
        )
        cells.append(_finish(start))
    total = outcome.quantity
    start = _begin(
        demand,
        None,
        theme=theme,
        labels=labels,
        x_label=None,
        y_label=None,
        x_max=None,
        y_range=ceiling,
        margin=margin,
        title=names[len(firm.plants)],
        size=size,
        dpi=dpi,
        symbol=firm.plants[0].output_symbol,
    )
    _demand_curves(start, demand, model=outcome)
    summed = curve(
        firm.summed_marginal_cost(top), layer_id=f"{_PREFIX}.mc_total", role="micro.curve.marginal"
    )
    start.layers.extend((summed, curve_name(summed, start.texts("monopoly.mc_total"))))
    _point_marks(
        start,
        firm.plants[0].output_symbol,
        total,
        outcome.price,
        mark_id="total",
        output_key="monopoly.mark.output_total",
    )
    start.layers.append(guide((0.0, level), (total, level), layer_id=f"{_PREFIX}.guide.level"))
    start.layers.append(dot((total, level), layer_id=f"{_PREFIX}.point.total"))
    cells.append(_finish(start))
    links = []
    xs = [cell.spec.x_range[1] for cell in cells]
    for index in range(len(cells) - 1):
        links.append(
            GridLink(index, (xs[index], level), index + 1, (0.0, level), role="micro.guide")
        )
    return CanvasGrid([cells], links=links)


def lerner_markup_canvas(
    outcomes: Sequence[MonopolyOutcome],
    analyses: Sequence[CostAnalysis],
    *,
    titles: Sequence[str | None] | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL_SIZE,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """One panel per demand: a brace on ``p - MC`` shows the markup, small with elastic demand
    and large with inelastic demand (the Lerner index is ``1 / |e|``)."""
    cells = []
    heading = list(titles) if titles is not None else [None] * len(outcomes)
    for outcome, analysis, name in zip(outcomes, analyses, heading, strict=True):
        start = _begin(
            outcome.demand,
            analysis,
            theme=theme,
            labels=labels,
            x_label=None,
            y_label=None,
            x_max=None,
            y_range=None,
            margin=margin,
            title=name,
            size=size,
            dpi=dpi,
        )
        _demand_curves(start, outcome.demand, model=outcome)
        _cost_curves(start, analysis, ("mc",))
        _point_marks(
            start, analysis.cost.output_symbol, outcome.quantity, outcome.price, mark_id="monopoly"
        )
        start.layers.append(
            dot((outcome.quantity, outcome.price), layer_id=f"{_PREFIX}.point.monopoly")
        )
        start.layers.append(
            dot((outcome.quantity, outcome.marginal_cost), layer_id=f"{_PREFIX}.point.mr_mc")
        )
        start.layers.append(
            SpanBraceLayer(
                (outcome.quantity, outcome.marginal_cost),
                (outcome.quantity, outcome.price),
                start.texts("monopoly.markup"),
                side="right",
                id=f"{_PREFIX}.brace.markup",
                z_index=8,
            )
        )
        cells.append(_finish(start))
    return CanvasGrid([cells])
