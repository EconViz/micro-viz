"""Profit, producer surplus and cost-shift figures."""

from __future__ import annotations

from collections.abc import Mapping

from mosaickit import Canvas, RegionLabelLayer, SpanBraceLayer

from micro_viz.core.theme import PlotTheme
from micro_viz.firm.costs import CostAnalysis
from micro_viz.firm.costs.visuals import _unit_points
from micro_viz.firm.perfect_competition import (
    CompetitiveOutcome,
    RevenueCostAnalysis,
    solve_competitive_firm,
)
from micro_viz.firm.perfect_competition.visuals._base import (
    _between,
    _finish,
    _level_mark,
    _lower_crossing,
    _mc_between,
    _output_marks,
    _price_line,
    _start,
    _top,
    _unit_curves,
    _x_max,
)
from micro_viz.visuals.common import (
    FIGURE_DPI,
    FIGURE_SIZE,
    MARGIN,
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
