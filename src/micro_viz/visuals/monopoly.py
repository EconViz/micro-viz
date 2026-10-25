"""mosaickit visual builders for single-price monopoly."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import (
    AxisMarkLayer,
    Canvas,
    CanvasGrid,
    GridLink,
    Layer,
    RegionLabelLayer,
    SpanBraceLayer,
)

from micro_viz.competition import LinearDemand
from micro_viz.costs import CostAnalysis
from micro_viz.monopoly import MonopolyOutcome, MultiplantMonopoly, MultiplantOutcome
from micro_viz.theme import PlotTheme
from micro_viz.visuals.common import (
    FIGURE_DPI,
    FIGURE_SIZE,
    MARGIN,
    Point,
    Range,
    axis_mark,
    curve,
    curve_name,
    dot,
    drop_line,
    guide,
    pad_range,
    region,
)
from micro_viz.visuals.competition import (
    PANEL_SIZE,
    _between,
    _finish,
    _level_mark,
    _rectangle,
    _Start,
    _start,
)
from micro_viz.visuals.costs import _unit_points
from micro_viz.visuals.movement import parallel_arrow, rotation_arrow

_PREFIX = "micro.monopoly"


def _demand_points(demand: LinearDemand) -> tuple[Point, ...]:
    return ((0.0, demand.intercept), (demand.quantity_intercept, 0.0))


def _mr_points(demand: LinearDemand) -> tuple[Point, ...]:
    return ((0.0, demand.intercept), (demand.quantity_intercept / 2, 0.0))


def _begin(
    demand: LinearDemand,
    analysis: CostAnalysis | None,
    *,
    theme: PlotTheme | None,
    labels: Mapping[str, str] | None,
    x_label: str | None,
    y_label: str | None,
    x_max: float | None,
    y_range: Range | None,
    margin: float,
    title: str | None,
    size: tuple[float, float],
    dpi: int,
    symbol: str | None = None,
) -> _Start:
    """The axes of a monopoly figure: price up to the demand intercept."""
    reach = demand.quantity_intercept
    if analysis is not None:
        reach = max(reach, analysis.output_range[1])
    return _start(
        theme=theme,
        labels=labels,
        x_symbol=symbol or (analysis.cost.output_symbol if analysis is not None else "Q"),
        x_label=x_label,
        y_label=y_label,
        y_text_id="competition.axis.price",
        x_max=x_max if x_max is not None else reach * (1 + margin),
        y_range=y_range or pad_range(0.0, demand.intercept, margin),
        title=title,
        size=size,
        dpi=dpi,
    )


def _demand_curves(
    start: _Start,
    demand: LinearDemand,
    *,
    key: str = "monopoly.demand",
    mr_key: str = "monopoly.mr",
    suffix: str = "",
    role: str = "micro.curve.demand",
    mr_role: str = "micro.curve.marginal_revenue",
    mr: bool = True,
    along: float = 0.0,
    model: object | None = None,
) -> None:
    line = curve(
        _demand_points(demand), layer_id=f"{_PREFIX}.demand{suffix}", role=role, model=model
    )
    start.layers.extend((line, curve_name(line, start.texts(key), at=along)))
    if mr:
        marginal = curve(
            _mr_points(demand), layer_id=f"{_PREFIX}.mr{suffix}", role=mr_role, model=model
        )
        start.layers.extend((marginal, curve_name(marginal, start.texts(mr_key), at=0.82)))


def _cost_curves(
    start: _Start,
    analysis: CostAnalysis,
    names: Sequence[str],
    *,
    role: str | None = None,
    key_suffix: str = "",
    suffix: str = "",
) -> None:
    styles = {
        "mc": ("micro.curve.marginal", "monopoly.mc"),
        "atc": ("micro.curve.average", "monopoly.atc"),
    }
    for name in names:
        base_role, key = styles[name]
        path = curve(
            _unit_points(analysis, name),
            layer_id=f"{_PREFIX}.{name}{suffix}",
            role=role or base_role,
            model=analysis,
        )
        start.layers.extend((path, curve_name(path, start.texts(key + key_suffix))))


def _point_marks(
    start: _Start,
    symbol: str,
    quantity: float,
    price: float,
    *,
    mark_id: str,
    output_key: str = "monopoly.mark.output",
    price_key: str = "monopoly.mark.price",
    output_mark: bool = True,
) -> None:
    """Dashed guides from the point ``(quantity, price)`` to both axes with their names."""
    start.layers.append(drop_line(quantity, price, layer_id=f"{_PREFIX}.guide.{mark_id}.output"))
    if output_mark:
        start.layers.append(
            axis_mark(
                "x",
                quantity,
                start.texts(output_key, output=symbol),
                layer_id=f"{_PREFIX}.mark.{mark_id}",
            )
        )
    _level_mark(start, price, price_key, mark_id=mark_id, dotted=False)
    start.layers.append(
        guide((0.0, price), (quantity, price), layer_id=f"{_PREFIX}.guide.{mark_id}.price")
    )


def _region_label(start: _Start, layer_id: str, key: str) -> None:
    start.layers.append(
        RegionLabelLayer(
            layer_id,
            start.texts(key),
            id=f"{layer_id}.label",
            role="micro.annotation",
            z_index=8,
        )
    )


def _mc_path(analysis: CostAnalysis, low: float, high: float) -> list[Point]:
    cost = analysis.cost
    steps = 40
    return [
        (q, cost.marginal_cost(q))
        for q in (low + (high - low) * index / steps for index in range(steps + 1))
    ]


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


__all__ = [
    "lerner_markup_canvas",
    "monopoly_canvas",
    "monopoly_demand_shift_canvas",
    "monopoly_dwl_canvas",
    "monopoly_tax_canvas",
    "monopoly_totals_canvas",
    "monopoly_totals_grid",
    "multiplant_canvas",
]
