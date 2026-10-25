"""mosaickit visual builders for short-run perfect competition."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from mosaickit import Canvas, CanvasGrid, GridLink, Layer, RegionLabelLayer, SpanBraceLayer

from micro_viz.competition import (
    CompetitiveOutcome,
    IndustrySupply,
    LinearDemand,
    Regime,
    RevenueCostAnalysis,
    shutdown_price,
    solve_competitive_firm,
)
from micro_viz.costs import CostAnalysis
from micro_viz.theme import PlotTheme
from micro_viz.visuals.axes import axes_layers
from micro_viz.visuals.common import (
    FIGURE_DPI,
    FIGURE_SIZE,
    MARGIN,
    Point,
    Range,
    Texts,
    axis_mark,
    curve,
    curve_name,
    dot,
    drop_line,
    guide,
    new_canvas,
    nudge_labels,
    pad_range,
    region,
    resolve_theme,
)
from micro_viz.visuals.costs import _UNIT_STYLE, _unit_points

PANEL_SIZE = (6.0, 4.5)
"""Default size in inches of each panel of a multi-panel figure."""
SAMPLES = 61
"""Default points of a curve built from the model (supply and shift curves)."""


@dataclass(slots=True)
class _Start:
    canvas: Canvas
    theme: PlotTheme
    texts: Texts
    x_axis: Range
    y_range: Range
    layers: list[Layer]


def _start(
    *,
    theme: PlotTheme | None,
    labels: Mapping[str, str] | None,
    x_symbol: str,
    x_label: str | None,
    y_label: str | None,
    y_text_id: str,
    x_max: float,
    y_range: Range,
    title: str | None,
    size: tuple[float, float],
    dpi: int,
) -> _Start:
    selected = resolve_theme(theme)
    texts = Texts(selected, labels)
    x_axis: Range = (0.0, x_max)
    horizontal = x_label if x_label is not None else x_symbol
    vertical = y_label if y_label is not None else texts(y_text_id)
    canvas = new_canvas(
        selected,
        x_range=x_axis,
        y_range=y_range,
        x_label=horizontal,
        y_label=vertical,
        title=title,
        size=size,
        dpi=dpi,
    )
    layers = list(axes_layers(x_axis, y_range, x_label=horizontal, y_label=vertical))
    return _Start(canvas, selected, texts, x_axis, y_range, layers)


def _finish(start: _Start) -> Canvas:
    start.canvas.extend(nudge_labels(start.layers, start.theme.label_nudges))
    return start.canvas


def _unit_curves(
    start: _Start, analysis: CostAnalysis, names: Sequence[str], *, prefix: str = "micro.cost"
) -> None:
    for name in names:
        role, key, along = _UNIT_STYLE[name]
        path = curve(
            _unit_points(analysis, name),
            layer_id=f"{prefix}.{name}",
            role=role,
            model=analysis,
        )
        start.layers.extend((path, curve_name(path, start.texts(key), at=along)))


def _price_line(start: _Start, price: float, *, key: str, layer_id: str) -> None:
    path = curve(
        ((0.0, price), (start.x_axis[1], price)),
        layer_id=layer_id,
        role="micro.curve.price",
    )
    start.layers.extend((path, curve_name(path, start.texts(key))))


def _top(analysis: CostAnalysis, names: Sequence[str], *extra: float) -> float:
    values = [value for name in names for _, value in _unit_points(analysis, name)]
    return max([*values, *extra])


def _x_max(analysis: CostAnalysis, x_max: float | None, margin: float) -> float:
    return x_max if x_max is not None else analysis.output_range[1] * (1 + margin)


def _output_marks(
    start: _Start,
    symbol: str,
    output: float,
    level: float,
    *,
    mark_id: str,
    key: str = "competition.mark.output",
    **fields: object,
) -> None:
    start.layers.append(drop_line(output, level, layer_id=f"micro.competition.guide.{mark_id}"))
    start.layers.append(dot((output, level), layer_id=f"micro.competition.point.{mark_id}"))
    start.layers.append(
        axis_mark(
            "x",
            output,
            start.texts(key, output=symbol, **fields),
            layer_id=f"micro.competition.mark.{mark_id}",
        )
    )


def _level_mark(
    start: _Start, level: float, key: str, *, mark_id: str, dotted: bool = True, **fields: object
) -> None:
    if dotted:
        start.layers.append(
            guide(
                (0.0, level),
                (start.x_axis[1], level),
                layer_id=f"micro.competition.guide.{mark_id}",
            )
        )
    start.layers.append(
        axis_mark(
            "y",
            level,
            start.texts(key, **fields),
            layer_id=f"micro.competition.mark.{mark_id}",
        )
    )


def _rectangle(left: float, right: float, low: float, high: float) -> tuple[Point, ...]:
    return ((left, low), (right, low), (right, high), (left, high))


def _between(upper: Sequence[Point], lower: Sequence[Point]) -> tuple[Point, ...]:
    """A polygon bounded above by ``upper`` (left to right) and below by ``lower``."""
    return (*upper, *reversed(lower))


def _slice(points: Sequence[Point], low: float, high: float) -> list[Point]:
    return [point for point in points if low <= point[0] <= high]


def _lower_crossing(function: Callable[[float], float], level: float, high: float) -> float:
    """The smallest output in ``0..high`` where ``function`` is at most ``level`` (bisection)."""
    if function(0.0) <= level:
        return 0.0
    low, up = 0.0, high
    for _ in range(60):
        middle = (low + up) / 2
        if function(middle) > level:
            low = middle
        else:
            up = middle
    return up


def _mc_between(analysis: CostAnalysis, low: float, high: float, samples: int = 41) -> list[Point]:
    cost = analysis.cost
    return [
        (q, cost.marginal_cost(q))
        for q in (low + (high - low) * index / (samples - 1) for index in range(samples))
    ]


def competitive_firm_canvas(
    analysis: CostAnalysis,
    outcome: CompetitiveOutcome,
    *,
    lost_profit: tuple[float, float] | None = None,
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
    """The price-taking firm: ATC, AVC and MC against the price line ``P = MR``.

    The output ``q*`` is where the price meets MC. A profit is the rectangle between the price
    and ATC(q*) over ``0..q*``; a loss (price below ATC but above AVC) is the same rectangle
    shaded as a loss; below the lowest AVC the firm shuts down and only the price line and the
    curves remain. ``lost_profit=(q1, q2)`` shades the profit lost by producing ``q1 < q*`` or
    ``q2 > q*`` instead.
    """
    cost = analysis.cost
    price = outcome.price
    symbol = cost.output_symbol
    names = ("mc", "atc", "avc")
    vertical = y_range or pad_range(0.0, _top(analysis, names, price), margin)
    start = _start(
        theme=theme,
        labels=labels,
        x_symbol=symbol,
        x_label=x_label,
        y_label=y_label,
        y_text_id="competition.axis.price",
        x_max=_x_max(analysis, x_max, margin),
        y_range=vertical,
        title=title,
        size=size,
        dpi=dpi,
    )
    texts = start.texts
    q = outcome.output
    if q > 0 and outcome.average_total_cost is not None:
        shade = "mid" if outcome.profit >= 0 else "dark"
        kind = "profit" if outcome.profit >= 0 else "loss"
        low, high = sorted((price, outcome.average_total_cost))
        if high > low:
            layer_id = f"micro.competition.{kind}"
            start.layers.append(
                region(_rectangle(0.0, q, low, high), layer_id=layer_id, shade=shade, model=outcome)
            )
            start.layers.append(
                RegionLabelLayer(
                    layer_id,
                    texts(f"competition.{kind}"),
                    id=f"{layer_id}.label",
                    role="micro.annotation",
                    z_index=8,
                )
            )
    if lost_profit is not None and q > 0:
        first, second = lost_profit
        if not 0 < first < q < second <= analysis.output_range[1]:
            raise ValueError("lost_profit must satisfy 0 < q1 < q* < q2 within the output range")
        left = _mc_between(analysis, first, q)
        right = _mc_between(analysis, q, second)
        for name, points, extra, index in (
            ("lower", _between([(first, price), (q, price)], left), first, 1),
            ("higher", _between([(q, price), (second, price)], right), second, 2),
        ):
            layer_id = f"micro.competition.lost_profit.{name}"
            start.layers.append(region(points, layer_id=layer_id, shade="dark", model=outcome))
            start.layers.append(
                RegionLabelLayer(
                    layer_id,
                    texts("competition.lost_profit"),
                    id=f"{layer_id}.label",
                    role="micro.annotation",
                    placement="callout",
                    z_index=8,
                )
            )
            _output_marks(
                start,
                symbol,
                extra,
                cost.marginal_cost(extra),
                mark_id=name,
                key="competition.mark.output_index",
                index=index,
            )
    _unit_curves(start, analysis, names)
    _price_line(start, price, key="competition.price", layer_id="micro.competition.price")
    if q > 0:
        _output_marks(start, symbol, q, price, mark_id="output")
        _level_mark(start, price, "competition.mark.price", mark_id="price")
        if outcome.average_total_cost is not None:
            _level_mark(
                start,
                outcome.average_total_cost,
                "competition.mark.cost",
                mark_id="cost",
            )
            start.layers.append(
                guide(
                    (q, outcome.average_total_cost),
                    (q, price),
                    layer_id="micro.competition.guide.average_cost_gap",
                )
            )
        if outcome.regime is Regime.LOSS and outcome.average_variable_cost is not None:
            _level_mark(
                start,
                outcome.average_variable_cost,
                "competition.mark.variable_cost",
                mark_id="variable_cost",
            )
    else:
        _level_mark(start, price, "competition.mark.price", mark_id="price")
    return _finish(start)


def firm_supply_canvas(
    analysis: CostAnalysis,
    *,
    prices: Sequence[float] = (),
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
    """The firm's supply curve: the part of MC above the lowest AVC, drawn solid.

    The part of MC below the shutdown price is dashed. Each price in ``prices`` is a dashed
    line to the output the firm supplies at it; the shutdown price (lowest AVC) is marked on the
    price axis.
    """
    cost = analysis.cost
    symbol = cost.output_symbol
    low = shutdown_price(cost)
    names = ("mc", "atc", "avc")
    vertical = y_range or pad_range(0.0, _top(analysis, names, *prices), margin)
    start = _start(
        theme=theme,
        labels=labels,
        x_symbol=symbol,
        x_label=x_label,
        y_label=y_label,
        y_text_id="competition.axis.price",
        x_max=_x_max(analysis, x_max, margin),
        y_range=vertical,
        title=title,
        size=size,
        dpi=dpi,
    )
    texts = start.texts
    mc = _unit_points(analysis, "mc")
    below = [point for point in mc if point[1] <= low]
    above = [point for point in mc if point[1] >= low]
    for name in ("atc", "avc"):
        _unit_curves(start, analysis, (name,))
    if len(below) > 1:
        start.layers.append(
            curve(below, layer_id="micro.competition.mc_below", role="micro.curve.fixed")
        )
    supply = curve(above, layer_id="micro.competition.supply", role="micro.curve.marginal")
    start.layers.extend((supply, curve_name(supply, texts("competition.supply"))))
    _level_mark(start, low, "competition.mark.shutdown", mark_id="shutdown")
    start.layers.append(
        dot((cost_min_avc_output(analysis, low), low), layer_id="micro.competition.point.shutdown")
    )
    for index, price in enumerate(prices, start=1):
        quantity = solve_competitive_firm(cost, price).output
        _level_mark(
            start, price, "competition.mark.price_index", mark_id=f"price.{index}", index=index
        )
        if quantity > 0:
            _output_marks(
                start,
                symbol,
                quantity,
                price,
                mark_id=f"output.{index}",
                key="competition.mark.output_index",
                index=index,
            )
    return _finish(start)


def cost_min_avc_output(analysis: CostAnalysis, shutdown: float) -> float:
    """The output at which AVC is lowest (where MC crosses it), from the sampled curve."""
    avc = analysis.minimum_average_variable_cost
    if avc is not None:
        return avc.output
    candidates = [
        (point.average_variable_cost, point.output)
        for point in analysis.points
        if point.average_variable_cost is not None
    ]
    return min(candidates)[1] if candidates else 0.0


def revenue_cost_profit_canvas(
    analysis: RevenueCostAnalysis,
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
    """Total revenue, total cost and the profit curve against output.

    Profit is largest where the slopes of TR and TC are equal: a dashed tangent to TC at ``q*``
    parallels TR, and a dashed vertical segment shows the profit there. Dashed drop lines mark
    the break-even outputs and ``q*``.
    """
    cost = analysis.cost
    symbol = cost.output_symbol
    revenue = tuple((p.output, p.total_revenue) for p in analysis.points)
    total = tuple((p.output, p.total_cost) for p in analysis.points)
    profit = tuple((p.output, p.profit) for p in analysis.points)
    values = [value for _, value in (*revenue, *total, *profit)]
    vertical = y_range or pad_range(min(0.0, *values), max(values), margin)
    start = _start(
        theme=theme,
        labels=labels,
        x_symbol=symbol,
        x_label=x_label,
        y_label=y_label,
        y_text_id="cost.axis.total",
        x_max=x_max if x_max is not None else analysis.output_range[1] * (1 + margin),
        y_range=vertical,
        title=title,
        size=size,
        dpi=dpi,
    )
    texts = start.texts
    for name, points, role, key in (
        ("tr", revenue, "micro.curve.price", "competition.tr"),
        ("tc", total, "micro.curve.total", "cost.tc"),
        ("profit", profit, "micro.curve.average", "competition.profit_curve"),
    ):
        path = curve(points, layer_id=f"micro.competition.{name}", role=role, model=analysis)
        start.layers.extend((path, curve_name(path, texts(key))))
    best = analysis.profit_maximizing_output
    if best > 0:
        at_cost = cost.total_cost(best)
        at_revenue = analysis.price * best
        slope = cost.marginal_cost(best)
        reach = analysis.output_range[1] * 0.12
        start.layers.append(
            guide(
                (max(0.0, best - reach), at_cost - slope * min(reach, best)),
                (best + reach, at_cost + slope * reach),
                layer_id="micro.competition.guide.tangent",
            )
        )
        start.layers.append(
            guide((best, at_cost), (best, at_revenue), layer_id="micro.competition.guide.profit")
        )
        start.layers.append(dot((best, at_cost), layer_id="micro.competition.point.tc"))
        start.layers.append(dot((best, at_revenue), layer_id="micro.competition.point.tr"))
        start.layers.append(
            drop_line(
                best,
                max(at_revenue, at_cost),
                layer_id="micro.competition.guide.output",
                floor=vertical[0],
            )
        )
        start.layers.append(
            axis_mark(
                "x",
                best,
                texts("competition.mark.output", output=symbol),
                layer_id="micro.competition.mark.output",
            )
        )
    for index, root in enumerate(analysis.break_even_outputs):
        start.layers.append(
            drop_line(
                root,
                analysis.price * root,
                layer_id=f"micro.competition.guide.break_even.{index}",
                floor=vertical[0],
            )
        )
        start.layers.append(
            dot(
                (root, analysis.price * root),
                layer_id=f"micro.competition.point.break_even.{index}",
            )
        )
        start.layers.append(
            axis_mark(
                "x",
                root,
                texts("competition.mark.break_even", output=symbol, index=index),
                layer_id=f"micro.competition.mark.break_even.{index}",
            )
        )
    return _finish(start)


def producer_surplus_canvas(
    analysis: CostAnalysis,
    outcome: CompetitiveOutcome,
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
    """Producer surplus: the area between the price and MC from zero to ``q*``.

    The area equals revenue minus variable cost, the rectangle under the price line less the
    area under MC.
    """
    cost = analysis.cost
    symbol = cost.output_symbol
    names = ("mc", "avc")
    vertical = y_range or pad_range(0.0, _top(analysis, names, outcome.price), margin)
    start = _start(
        theme=theme,
        labels=labels,
        x_symbol=symbol,
        x_label=x_label,
        y_label=y_label,
        y_text_id="competition.axis.price",
        x_max=_x_max(analysis, x_max, margin),
        y_range=vertical,
        title=title,
        size=size,
        dpi=dpi,
    )
    q = outcome.output
    if q > 0:
        samples = 61
        low = _lower_crossing(cost.marginal_cost, outcome.price, q)
        mc = _mc_between(analysis, low, q, samples)
        polygon = _between([(low, outcome.price), (q, outcome.price)], mc)
        layer_id = "micro.competition.producer_surplus"
        start.layers.append(region(polygon, layer_id=layer_id, shade="mid", model=outcome))
        start.layers.append(
            RegionLabelLayer(
                layer_id,
                start.texts("competition.producer_surplus"),
                id=f"{layer_id}.label",
                role="micro.annotation",
                z_index=8,
            )
        )
    _unit_curves(start, analysis, names)
    _price_line(start, outcome.price, key="competition.price", layer_id="micro.competition.price")
    if q > 0:
        _output_marks(start, symbol, q, outcome.price, mark_id="output")
    _level_mark(start, outcome.price, "competition.mark.price", mark_id="price")
    return _finish(start)


def cost_shift_canvas(
    before: CostAnalysis,
    after: CostAnalysis,
    price: float,
    *,
    tax: float | None = None,
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
    """MC before and after a cost increase, with the price line and the two outputs.

    The firm moves from ``q1`` (where P meets MC before) to the smaller ``q2``; the wedge
    between the two MC curves from ``q2`` to ``q1`` is shaded. Pass ``tax`` when ``after`` is the
    cost function with a per-unit tax of that size: AVC is drawn too and a brace marks the tax
    between the curves at ``q1``.
    """
    old = solve_competitive_firm(before.cost, price)
    new = solve_competitive_firm(after.cost, price)
    symbol = before.cost.output_symbol
    names = ("mc", "avc") if tax is not None else ("mc",)
    top = max(_top(before, names, price), _top(after, names, price))
    vertical = y_range or pad_range(0.0, top, margin)
    start = _start(
        theme=theme,
        labels=labels,
        x_symbol=symbol,
        x_label=x_label,
        y_label=y_label,
        y_text_id="competition.axis.price",
        x_max=_x_max(before, x_max, margin),
        y_range=vertical,
        title=title,
        size=size,
        dpi=dpi,
    )
    texts = start.texts
    first, second = old.output, new.output
    if first > second > 0:
        wedge = _between(_mc_between(after, second, first), _mc_between(before, second, first))
        start.layers.append(region(wedge, layer_id="micro.competition.cost_wedge", shade="mid"))
    before_mc = curve(
        _unit_points(before, "mc"),
        layer_id="micro.competition.mc_before",
        role="micro.curve.marginal",
    )
    after_mc = curve(
        _unit_points(after, "mc"),
        layer_id="micro.competition.mc_after",
        role="micro.curve.variable",
    )
    key_after = "competition.mc_taxed" if tax is not None else "competition.mc_after"
    start.layers.extend(
        (
            before_mc,
            curve_name(before_mc, texts("competition.mc_before")),
            after_mc,
            curve_name(after_mc, texts(key_after)),
        )
    )
    if tax is not None:
        avc_before = curve(
            _unit_points(before, "avc"),
            layer_id="micro.competition.avc_before",
            role="micro.curve.average.variable",
        )
        avc_after = curve(
            _unit_points(after, "avc"),
            layer_id="micro.competition.avc_after",
            role="micro.curve.average.fixed",
        )
        start.layers.extend(
            (
                avc_before,
                curve_name(avc_before, texts("cost.avc"), at=0.8),
                avc_after,
                curve_name(avc_after, texts("competition.avc_taxed"), at=0.9),
            )
        )
    _price_line(start, price, key="competition.price", layer_id="micro.competition.price")
    for index, quantity in enumerate((first, second), start=1):
        if quantity > 0:
            _output_marks(
                start,
                symbol,
                quantity,
                price,
                mark_id=f"output.{index}",
                key="competition.mark.output_index",
                index=index,
            )
    _level_mark(start, price, "competition.mark.price", mark_id="price", dotted=False)
    if tax is not None and first > 0:
        low = before.cost.marginal_cost(first)
        start.layers.append(
            SpanBraceLayer(
                (first, low),
                (first, low + tax),
                texts("competition.tax"),
                side="right",
                id="micro.competition.tax",
                z_index=8,
            )
        )
    return _finish(start)


def industry_supply_canvas(
    industry: IndustrySupply,
    *,
    prices: Sequence[float] = (),
    price_max: float,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    x_label: str | None = None,
    y_label: str | None = None,
    x_max: float | None = None,
    y_range: Range | None = None,
    margin: float = MARGIN,
    samples: int = SAMPLES,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Industry supply as the horizontal sum of the firms' supply curves.

    Each firm's supply (MC above its lowest AVC) is a dashed curve; the industry supply, the
    sum of the firms' quantities at each price, is solid and steps where a firm enters at its
    shutdown price. Each price in ``prices`` is a dashed line to the industry quantity.
    """
    symbol = industry.firms[0].output_symbol
    total = industry.curve(price_max, samples=samples)
    quantity_top = max(point[0] for point in total)
    start = _start(
        theme=theme,
        labels=labels,
        x_symbol=symbol,
        x_label=x_label,
        y_label=y_label,
        y_text_id="competition.axis.price",
        x_max=x_max if x_max is not None else quantity_top * (1 + margin),
        y_range=y_range or pad_range(0.0, price_max, margin),
        title=title,
        size=size,
        dpi=dpi,
    )
    texts = start.texts
    for index, firm in enumerate(industry.firms, start=1):
        from micro_viz.competition import FirmSupply

        points = FirmSupply(firm).curve(price_max, samples=samples)
        path = curve(
            tuple(points),
            layer_id=f"micro.competition.firm.{index}",
            role="micro.curve.fixed",
        )
        start.layers.extend((path, curve_name(path, texts("competition.firm", index=index))))
    supply = curve(total, layer_id="micro.competition.industry", role="micro.curve.marginal")
    start.layers.extend((supply, curve_name(supply, texts("competition.supply"))))
    for index, price in enumerate(prices, start=1):
        quantity = industry.quantity(price)
        _level_mark(
            start, price, "competition.mark.price_index", mark_id=f"price.{index}", index=index
        )
        if quantity > 0:
            _output_marks(
                start,
                symbol,
                quantity,
                price,
                mark_id=f"output.{index}",
                key="competition.mark.output_index",
                index=index,
            )
    return _finish(start)


def market_and_firm_canvas(
    demand: LinearDemand,
    price: float,
    *,
    firm_output_max: float,
    titles: tuple[str | None, str | None] = (None, None),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL_SIZE,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """The firm beside the market: horizontal demand ``d`` at the market price, and the
    downward market demand ``D``, with a dashed link carrying the price across.

    The firm panel's output axis runs to ``firm_output_max``; the market quantity is where
    the price meets ``D``.
    """
    selected = resolve_theme(theme)
    market_quantity = demand.quantity(price)
    firm = _start(
        theme=selected,
        labels=labels,
        x_symbol="q",
        x_label=None,
        y_label=None,
        y_text_id="competition.axis.price",
        x_max=firm_output_max,
        y_range=pad_range(0.0, demand.intercept, margin),
        title=titles[0],
        size=size,
        dpi=dpi,
    )
    line = curve(
        ((0.0, price), (firm_output_max, price)),
        layer_id="micro.competition.firm_demand",
        role="micro.curve.price",
    )
    firm.layers.extend((line, curve_name(line, firm.texts("competition.demand_firm"))))
    _level_mark(firm, price, "competition.mark.price", mark_id="price", dotted=False)
    market = _start(
        theme=selected,
        labels=labels,
        x_symbol=firm.texts("competition.axis.industry_output"),
        x_label=None,
        y_label=None,
        y_text_id="competition.axis.price",
        x_max=demand.quantity_intercept * (1 + margin),
        y_range=pad_range(0.0, demand.intercept, margin),
        title=titles[1],
        size=size,
        dpi=dpi,
    )
    curve_d = curve(
        ((0.0, demand.intercept), (demand.quantity_intercept, 0.0)),
        layer_id="micro.competition.market_demand",
        role="micro.curve.average",
    )
    market.layers.extend(
        (curve_d, curve_name(curve_d, market.texts("competition.demand_industry")))
    )
    market.layers.append(
        guide(
            (0.0, price), (market_quantity, price), layer_id="micro.competition.guide.market_price"
        )
    )
    _output_marks(
        market,
        "Q",
        market_quantity,
        price,
        mark_id="market_output",
        key="competition.mark.industry_output",
    )
    _level_mark(market, price, "competition.mark.price", mark_id="market_price", dotted=False)
    upper = _finish(firm)
    lower = _finish(market)
    link = GridLink(0, (firm_output_max, price), 1, (0.0, price), role="micro.guide")
    return CanvasGrid([[upper, lower]], links=[link])


__all__ = [
    "PANEL_SIZE",
    "competitive_firm_canvas",
    "cost_shift_canvas",
    "firm_supply_canvas",
    "industry_supply_canvas",
    "market_and_firm_canvas",
    "producer_surplus_canvas",
    "revenue_cost_profit_canvas",
]
