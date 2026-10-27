"""The competitive firm and its supply curve."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import Canvas, RegionLabelLayer

from micro_viz.core.theme import PlotTheme
from micro_viz.firm.competition import (
    CompetitiveOutcome,
    Regime,
    shutdown_price,
    solve_competitive_firm,
)
from micro_viz.firm.costs import CostAnalysis
from micro_viz.firm.visuals.competition._base import (
    _between,
    _finish,
    _level_mark,
    _mc_between,
    _output_marks,
    _price_line,
    _rectangle,
    _start,
    _top,
    _unit_curves,
    _x_max,
)
from micro_viz.firm.visuals.costs import _unit_points
from micro_viz.visuals.common import (
    FIGURE_DPI,
    FIGURE_SIZE,
    MARGIN,
    Range,
    curve,
    curve_name,
    dot,
    guide,
    pad_range,
    region,
)


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
        if high - low > 1e-9 * max(1.0, abs(high)):
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
        if outcome.average_total_cost is not None and abs(
            outcome.average_total_cost - price
        ) > 1e-9 * max(1.0, price):
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
