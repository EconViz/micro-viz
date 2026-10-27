"""Market-and-firm panels for the four short-run competitive-firm cases."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import Canvas, CanvasGrid, GridLink, GridSpacing, PointLabelLayer

from micro_viz.core.theme import PlotTheme
from micro_viz.firm.competition import Regime, profit_maximizing_output, solve_competitive_firm
from micro_viz.firm.costs import CostAnalysis
from micro_viz.firm.visuals.competition._base import PANEL_SIZE, _finish, _start
from micro_viz.visuals.common import (
    FIGURE_DPI,
    MARGIN,
    axis_mark,
    curve,
    curve_name,
    dot,
    drop_line,
    guide,
    pad_range,
    region,
    resolve_theme,
)
from micro_viz.visuals.movement import parallel_arrow


def _indexed(name: str, index: int | None) -> str:
    return name if index is None else rf"$\mathrm{{{name}}}_{{{index}}}$"


def _sample(analysis: CostAnalysis, name: str, ceiling: float) -> tuple[tuple[float, float], ...]:
    points = []
    for point in analysis.points:
        value = getattr(point, name)
        if value is not None and 0.0 <= value <= ceiling:
            points.append((point.output, value))
    return tuple(points)


def _point(layers: list, xy: tuple[float, float], name: str, layer_id: str) -> None:  # type: ignore[type-arg]
    layers.append(dot(xy, layer_id=f"{layer_id}.point"))
    layers.append(PointLabelLayer(xy, name, id=f"{layer_id}.label", role="micro.point"))


def _market_panel(
    *,
    price: float,
    quantity: float,
    quantity_max: float,
    y_max: float,
    title: str | None,
    theme: PlotTheme,
    labels: Mapping[str, str] | None,
    size: tuple[float, float],
    dpi: int,
) -> Canvas:
    start = _start(
        theme=theme,
        labels=labels,
        x_symbol="Q",
        x_label=None,
        y_label="p",
        y_text_id="competition.axis.price",
        x_max=quantity_max,
        y_range=pad_range(0.0, y_max, MARGIN),
        title=title,
        size=size,
        dpi=dpi,
    )
    slope = price / quantity
    supply = curve(
        ((quantity * 0.18, price * 0.18), (quantity_max * 0.92, slope * quantity_max * 0.92)),
        layer_id="micro.competition.types.market.supply",
        role="micro.curve.marginal",
    )
    intercept = price + slope * quantity
    demand = curve(
        (
            (quantity * 0.18, intercept - slope * quantity * 0.18),
            (quantity_max * 0.92, intercept - slope * quantity_max * 0.92),
        ),
        layer_id="micro.competition.types.market.demand",
        role="micro.curve.demand",
    )
    start.layers.extend(
        (
            supply,
            curve_name(supply, "$S$"),
            demand,
            curve_name(demand, "$D$"),
            guide((0.0, price), (quantity, price), layer_id="micro.competition.types.market.price"),
            drop_line(quantity, price, layer_id="micro.competition.types.market.quantity"),
            axis_mark("y", price, "p_0", layer_id="micro.competition.types.market.p0"),
            axis_mark("x", quantity, "Q_0", layer_id="micro.competition.types.market.q0"),
        )
    )
    _point(start.layers, (quantity, price), "A", "micro.competition.types.market.a")
    return _finish(start)


def _firm_panel(
    analysis: CostAnalysis,
    price: float,
    *,
    title: str | None,
    curve_index: int | None,
    theme: PlotTheme,
    labels: Mapping[str, str] | None,
    size: tuple[float, float],
    dpi: int,
) -> tuple[Canvas, float, float]:
    cost = analysis.cost
    outcome = solve_competitive_firm(cost, price)
    output = outcome.output or profit_maximizing_output(cost, price)
    if output <= 0:
        raise ValueError("price must meet marginal cost at a positive output")
    atc = cost.average_total_cost(output)
    avc = cost.average_variable_cost(output)
    if atc is None or avc is None:
        raise ValueError("positive output must have finite average costs")
    top = max(price, atc, avc) * 1.55
    start = _start(
        theme=theme,
        labels=labels,
        x_symbol="q",
        x_label=None,
        y_label="p",
        y_text_id="competition.axis.price",
        x_max=analysis.output_range[1] * (1 + MARGIN),
        y_range=pad_range(0.0, top, MARGIN),
        title=title,
        size=size,
        dpi=dpi,
    )
    curves: Sequence[tuple[str, str, str, float]] = (
        ("marginal_cost", _indexed("SMC", curve_index), "micro.curve.marginal", 0.82),
        ("average_total_cost", _indexed("SAC", curve_index), "micro.curve.average", 0.90),
    )
    if outcome.regime in (Regime.LOSS, Regime.SHUTDOWN):
        curves = (
            *curves,
            (
                "average_variable_cost",
                _indexed("AVC", curve_index),
                "micro.curve.variable",
                0.96,
            ),
        )
    for field, name, role, at in curves:
        points = _sample(analysis, field, start.y_range[1])
        path = curve(
            points,
            layer_id=f"micro.competition.types.firm.{field}",
            role=role,
            model=analysis,
        )
        start.layers.extend((path, curve_name(path, name, at=at)))

    if outcome.regime is Regime.PROFIT:
        start.layers.append(
            region(
                ((0.0, atc), (output, atc), (output, price), (0.0, price)),
                layer_id="micro.competition.types.firm.profit",
                shade="mid",
                model=outcome,
            )
        )
    elif outcome.regime is Regime.LOSS:
        start.layers.append(
            region(
                ((0.0, price), (output, price), (output, atc), (0.0, atc)),
                layer_id="micro.competition.types.firm.loss",
                shade="dark",
                model=outcome,
            )
        )
    elif outcome.regime is Regime.SHUTDOWN:
        start.layers.extend(
            (
                region(
                    ((0.0, price), (output, price), (output, avc), (0.0, avc)),
                    layer_id="micro.competition.types.firm.operating_loss",
                    shade="dark",
                    model=outcome,
                ),
                region(
                    ((0.0, avc), (output, avc), (output, atc), (0.0, atc)),
                    layer_id="micro.competition.types.firm.fixed_cost",
                    shade="mid",
                    model=outcome,
                ),
            )
        )

    price_line = curve(
        ((0.0, price), (start.x_axis[1] * 0.92, price)),
        layer_id="micro.competition.types.firm.price",
        role="micro.curve.price",
    )
    start.layers.extend((price_line, curve_name(price_line, "p = AR = MR")))
    start.layers.extend(
        (
            drop_line(output, price, layer_id="micro.competition.types.firm.output"),
            axis_mark("x", output, "q_0", layer_id="micro.competition.types.firm.q0"),
        )
    )
    _point(start.layers, (output, price), "A", "micro.competition.types.firm.a")
    if outcome.regime is Regime.PROFIT:
        _point(start.layers, (0.0, price), "B", "micro.competition.types.firm.b")
        _point(start.layers, (output, atc), "C", "micro.competition.types.firm.c")
        start.layers.append(
            guide((0.0, atc), (output, atc), layer_id="micro.competition.types.firm.atc")
        )
    elif outcome.regime in (Regime.LOSS, Regime.SHUTDOWN):
        _point(start.layers, (output, atc), "B", "micro.competition.types.firm.b")
        _point(start.layers, (output, avc), "C", "micro.competition.types.firm.c")
        _point(start.layers, (0.0, atc), "E", "micro.competition.types.firm.e")
        _point(start.layers, (0.0, avc), "F", "micro.competition.types.firm.f")
        start.layers.extend(
            (
                guide((0.0, atc), (output, atc), layer_id="micro.competition.types.firm.atc"),
                guide((0.0, avc), (output, avc), layer_id="micro.competition.types.firm.avc"),
            )
        )
    return _finish(start), output, top


def competitive_short_run_grid(
    analysis: CostAnalysis,
    price: float,
    *,
    market_quantity: float = 5.0,
    market_quantity_max: float = 9.0,
    titles: tuple[str | None, str | None] = ("", ""),
    curve_index: int | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    size: tuple[float, float] = PANEL_SIZE,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """A competitive market beside one firm in profit, break-even, loss, or shutdown."""
    selected = resolve_theme(theme)
    firm, _, top = _firm_panel(
        analysis,
        price,
        title=titles[1],
        curve_index=curve_index,
        theme=selected,
        labels=labels,
        size=size,
        dpi=dpi,
    )
    market = _market_panel(
        price=price,
        quantity=market_quantity,
        quantity_max=market_quantity_max,
        y_max=top,
        title=titles[0],
        theme=selected,
        labels=labels,
        size=size,
        dpi=dpi,
    )
    return CanvasGrid(
        [[market, firm]],
        links=[GridLink(0, (market_quantity_max, price), 1, (0.0, price), role="micro.guide")],
        spacing=GridSpacing(column_gap=0.10, outer=0.03),
    )


def competitive_demand_increase_grid(
    analysis: CostAnalysis,
    prices: tuple[float, float],
    *,
    market_quantities: tuple[float, float] = (4.5, 5.8),
    market_quantity_max: float = 9.0,
    titles: tuple[str | None, str | None] = ("", ""),
    curve_index: int | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    size: tuple[float, float] = PANEL_SIZE,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """A rightward market-demand shift and the corresponding output change of one firm."""
    low_price, high_price = prices
    low_q, high_q = market_quantities
    if not (0 < low_price < high_price and 0 < low_q < high_q < market_quantity_max):
        raise ValueError("prices and market quantities must be positive and increasing")
    selected = resolve_theme(theme)
    low = solve_competitive_firm(analysis.cost, low_price)
    firm_q0 = low.output or profit_maximizing_output(analysis.cost, low_price)
    firm_q1 = solve_competitive_firm(analysis.cost, high_price).output
    atc0 = analysis.cost.average_total_cost(firm_q0)
    avc0 = analysis.cost.average_variable_cost(firm_q0)
    if atc0 is None or avc0 is None:
        raise ValueError("positive output must have finite average costs")
    top = max(high_price, atc0, avc0) * 1.5
    y_range = pad_range(0.0, top, MARGIN)

    market = _start(
        theme=selected,
        labels=labels,
        x_symbol="Q",
        x_label=None,
        y_label="p",
        y_text_id="competition.axis.price",
        x_max=market_quantity_max,
        y_range=y_range,
        title=titles[0],
        size=size,
        dpi=dpi,
    )
    supply_slope = (high_price - low_price) / (high_q - low_q)
    supply_intercept = low_price - supply_slope * low_q
    demand_slope = -1.15
    for name, q, p, role, at in (
        ("$D$", low_q, low_price, "micro.curve.demand", 1.0),
        ("$D_1$", high_q, high_price, "micro.curve.after.demand", 1.0),
    ):
        intercept = p - demand_slope * q
        points = (
            (max(0.6, q - 3.6), intercept + demand_slope * max(0.6, q - 3.6)),
            (
                min(market_quantity_max * 0.92, q + 3.6),
                intercept + demand_slope * min(market_quantity_max * 0.92, q + 3.6),
            ),
        )
        path = curve(points, layer_id=f"micro.competition.shift.market.{name}", role=role)
        market.layers.extend((path, curve_name(path, name, at=at)))
    supply_points = (
        (0.8, supply_intercept + supply_slope * 0.8),
        (market_quantity_max * 0.88, supply_intercept + supply_slope * market_quantity_max * 0.88),
    )
    supply = curve(
        supply_points, layer_id="micro.competition.shift.market.supply", role="micro.curve.marginal"
    )
    market.layers.extend((supply, curve_name(supply, "$S$")))
    for index, (q, p, point_name) in enumerate(
        ((low_q, low_price, "A"), (high_q, high_price, "B"))
    ):
        market.layers.extend(
            (
                guide((0.0, p), (q, p), layer_id=f"micro.competition.shift.market.price.{index}"),
                drop_line(q, p, layer_id=f"micro.competition.shift.market.quantity.{index}"),
                axis_mark(
                    "y", p, f"p_{index}", layer_id=f"micro.competition.shift.market.p{index}"
                ),
                axis_mark(
                    "x", q, f"Q_{index}", layer_id=f"micro.competition.shift.market.q{index}"
                ),
            )
        )
        _point(
            market.layers,
            (q, p),
            point_name,
            f"micro.competition.shift.market.{point_name.lower()}",
        )

    firm = _start(
        theme=selected,
        labels=labels,
        x_symbol="q",
        x_label=None,
        y_label="p",
        y_text_id="competition.axis.price",
        x_max=analysis.output_range[1] * (1 + MARGIN),
        y_range=y_range,
        title=titles[1],
        size=size,
        dpi=dpi,
    )
    names: Sequence[tuple[str, str, str, float]] = (
        ("marginal_cost", _indexed("SMC", curve_index), "micro.curve.marginal", 0.82),
        ("average_total_cost", _indexed("SAC", curve_index), "micro.curve.average", 0.92),
    )
    if low.regime in (Regime.LOSS, Regime.SHUTDOWN):
        names = (
            *names,
            (
                "average_variable_cost",
                _indexed("AVC", curve_index),
                "micro.curve.variable",
                0.97,
            ),
        )
    for field, name, role, at in names:
        path = curve(
            _sample(analysis, field, y_range[1]),
            layer_id=f"micro.competition.shift.firm.{field}",
            role=role,
            model=analysis,
        )
        firm.layers.extend((path, curve_name(path, name, at=at)))
    if low.regime is Regime.PROFIT:
        firm.layers.append(
            region(
                ((0.0, atc0), (firm_q0, atc0), (firm_q0, low_price), (0.0, low_price)),
                layer_id="micro.competition.shift.firm.initial_profit",
                shade="mid",
                model=low,
            )
        )
    for index, (q, p, point_name) in enumerate(
        ((firm_q0, low_price, "A"), (firm_q1, high_price, "B"))
    ):
        price_line = curve(
            ((0.0, p), (firm.x_axis[1] * 0.92, p)),
            layer_id=f"micro.competition.shift.firm.price.{index}",
            role="micro.curve.price" if index == 0 else "micro.curve.after",
        )
        firm.layers.extend(
            (
                price_line,
                curve_name(
                    price_line,
                    rf"$p_{index} = \mathrm{{AR}} = \mathrm{{MR}}$",
                    at=1.0,
                ),
                drop_line(q, p, layer_id=f"micro.competition.shift.firm.output.{index}"),
                axis_mark("x", q, f"q_{index}", layer_id=f"micro.competition.shift.firm.q{index}"),
            )
        )
        _point(
            firm.layers, (q, p), point_name, f"micro.competition.shift.firm.{point_name.lower()}"
        )
    firm.layers.append(
        parallel_arrow(
            (firm_q0, y_range[1] * 0.12),
            (firm_q1, y_range[1] * 0.12),
            layer_id="micro.competition.shift.firm.output_move",
        )
    )
    links = [GridLink(0, (market_quantity_max, p), 1, (0.0, p), role="micro.guide") for p in prices]
    return CanvasGrid(
        [[_finish(market), _finish(firm)]],
        links=links,
        spacing=GridSpacing(column_gap=0.10, outer=0.03),
    )


__all__ = ["competitive_demand_increase_grid", "competitive_short_run_grid"]
