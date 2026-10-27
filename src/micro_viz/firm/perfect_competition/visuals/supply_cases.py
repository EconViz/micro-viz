"""Textbook panels deriving firm and industry short-run competitive supply."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import Canvas, CanvasGrid, GridLink, GridSpacing

from micro_viz.core.theme import PlotTheme
from micro_viz.firm.costs import CostAnalysis
from micro_viz.firm.perfect_competition import (
    IndustrySupply,
    profit_maximizing_output,
    shutdown_price,
    solve_competitive_firm,
)
from micro_viz.firm.perfect_competition.visuals._base import PANEL_SIZE, _finish, _start
from micro_viz.firm.perfect_competition.visuals.types import _point, _sample
from micro_viz.visuals.common import (
    FIGURE_DPI,
    MARGIN,
    axis_mark,
    curve,
    curve_name,
    drop_line,
    guide,
    pad_range,
    resolve_theme,
)

_SPACING = GridSpacing(column_gap=0.10, outer=0.03)


def _cost_top(analysis: CostAnalysis, prices: Sequence[float]) -> float:
    average_floor = min(
        point.average_total_cost
        for point in analysis.points
        if point.average_total_cost is not None
    )
    return max(*prices, shutdown_price(analysis.cost), average_floor * 1.12) * 1.55


def _cost_panel(
    analysis: CostAnalysis,
    prices: Sequence[float],
    *,
    point_names: Sequence[str],
    output_marks: Sequence[str | None],
    y_max: float | None,
    title: str | None,
    theme: PlotTheme,
    labels: Mapping[str, str] | None,
    size: tuple[float, float],
    dpi: int,
) -> Canvas:
    cost = analysis.cost
    top = y_max if y_max is not None else _cost_top(analysis, prices)
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
    for field, name, role, at in (
        ("marginal_cost", "SMC", "micro.curve.marginal", 0.83),
        ("average_total_cost", "SAC", "micro.curve.average", 0.91),
        ("average_variable_cost", "AVC", "micro.curve.variable", 0.97),
    ):
        path = curve(
            _sample(analysis, field, start.y_range[1]),
            layer_id=f"micro.competition.supply_cases.firm.{field}",
            role=role,
            model=analysis,
        )
        start.layers.extend((path, curve_name(path, name, at=at)))

    for index, (price, name, mark) in enumerate(
        zip(prices, point_names, output_marks, strict=True)
    ):
        output = profit_maximizing_output(cost, price)
        line = curve(
            ((0.0, price), (start.x_axis[1] * 0.90, price)),
            layer_id=f"micro.competition.supply_cases.firm.price.{index}",
            role="micro.curve.price" if index == len(prices) // 2 else "micro.curve.after",
        )
        start.layers.append(line)
        if index == len(prices) // 2:
            start.layers.append(curve_name(line, "$p = \\mathrm{AR} = \\mathrm{MR}$"))
        _point(
            start.layers,
            (output, price),
            name,
            f"micro.competition.supply_cases.firm.point.{name.lower()}",
        )
        if mark is not None:
            start.layers.extend(
                (
                    drop_line(
                        output,
                        price,
                        layer_id=f"micro.competition.supply_cases.firm.drop.{index}",
                    ),
                    axis_mark(
                        "x",
                        output,
                        mark,
                        layer_id=f"micro.competition.supply_cases.firm.output.{index}",
                    ),
                )
            )
    return _finish(start)


def competitive_firm_supply_grid(
    analysis: CostAnalysis,
    prices: tuple[float, float, float],
    *,
    market_quantities: tuple[float, float, float] = (3.6, 5.0, 6.2),
    market_quantity_max: float = 9.0,
    titles: tuple[str | None, str | None] = ("", ""),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    size: tuple[float, float] = PANEL_SIZE,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """Demand shifts beside the firm's SMC, including its shutdown point."""
    low_price, middle_price, high_price = prices
    low_q, middle_q, high_q = market_quantities
    if not (0 < low_price < middle_price < high_price):
        raise ValueError("prices must be positive and increasing")
    selected = resolve_theme(theme)
    shut = shutdown_price(analysis.cost)
    firm_prices = (low_price, shut, middle_price, high_price)
    top = _cost_top(analysis, firm_prices)
    market = _start(
        theme=selected,
        labels=labels,
        x_symbol="Q",
        x_label=None,
        y_label="p",
        y_text_id="competition.axis.price",
        x_max=market_quantity_max,
        y_range=pad_range(0.0, top, MARGIN),
        title=titles[0],
        size=size,
        dpi=dpi,
    )
    supply_slope = (high_price - low_price) / (high_q - low_q)
    supply_intercept = middle_price - supply_slope * middle_q
    supply = curve(
        (
            (0.9, supply_intercept + supply_slope * 0.9),
            (
                market_quantity_max * 0.87,
                supply_intercept + supply_slope * market_quantity_max * 0.87,
            ),
        ),
        layer_id="micro.competition.supply_cases.market.supply",
        role="micro.curve.marginal",
    )
    market.layers.extend((supply, curve_name(supply, "$S$")))
    cases = (
        (low_q, low_price, "$D_2$", "C"),
        (middle_q, middle_price, "$D$", "A"),
        (high_q, high_price, "$D_1$", "B"),
    )
    demand_slope = -3.0
    for index, (quantity, price, name, point_name) in enumerate(cases):
        intercept = price - demand_slope * quantity
        left = max(0.7, quantity - 3.0)
        right = min(market_quantity_max * 0.92, quantity + 3.0)
        path = curve(
            ((left, intercept + demand_slope * left), (right, intercept + demand_slope * right)),
            layer_id=f"micro.competition.supply_cases.market.demand.{index}",
            role="micro.curve.demand" if index == 1 else "micro.curve.after.demand",
        )
        market.layers.extend((path, curve_name(path, name)))
        market.layers.extend(
            (
                guide(
                    (0.0, price),
                    (quantity, price),
                    layer_id=f"micro.competition.supply_cases.market.price.{index}",
                ),
                axis_mark(
                    "y",
                    price,
                    f"p_{(2, 0, 1)[index]}",
                    layer_id=f"micro.competition.supply_cases.market.p.{index}",
                ),
            )
        )
        if index > 0:
            market.layers.extend(
                (
                    drop_line(
                        quantity,
                        price,
                        layer_id=f"micro.competition.supply_cases.market.drop.{index}",
                    ),
                    axis_mark(
                        "x",
                        quantity,
                        f"Q_{index - 1}",
                        layer_id=f"micro.competition.supply_cases.market.q.{index}",
                    ),
                )
            )
        _point(
            market.layers,
            (quantity, price),
            point_name,
            f"micro.competition.supply_cases.market.point.{point_name.lower()}",
        )

    firm = _cost_panel(
        analysis,
        firm_prices,
        point_names=("C", "E", "A", "B"),
        output_marks=(None, None, "q_0", "q_1"),
        y_max=top,
        title=titles[1],
        theme=selected,
        labels=labels,
        size=size,
        dpi=dpi,
    )
    return CanvasGrid(
        [[_finish(market), firm]],
        links=[
            GridLink(0, (market_quantity_max, price), 1, (0.0, price), role="micro.guide")
            for price in prices
        ],
        spacing=_SPACING,
    )


def _industry_supply_grid(
    analysis: CostAnalysis,
    firms: int,
    price: float,
    *,
    demand: bool,
    titles: tuple[str | None, str | None],
    theme: PlotTheme | None,
    labels: Mapping[str, str] | None,
    size: tuple[float, float],
    dpi: int,
) -> CanvasGrid:
    selected = resolve_theme(theme)
    cost = analysis.cost
    shut = shutdown_price(cost)
    industry = IndustrySupply(tuple(cost for _ in range(firms)))
    firm_qs = profit_maximizing_output(cost, shut)
    firm_q = solve_competitive_firm(cost, price).output
    market_qs = firms * firm_qs
    market_q = firms * firm_q
    price_top = _cost_top(analysis, (shut, price))
    market_x = market_q * 1.42
    market = _start(
        theme=selected,
        labels=labels,
        x_symbol="Q",
        x_label=None,
        y_label="p",
        y_text_id="competition.axis.price",
        x_max=market_x,
        y_range=pad_range(0.0, price_top, MARGIN),
        title=titles[0],
        size=size,
        dpi=dpi,
    )
    supply_points = [
        point for point in industry.curve(price_top, samples=151) if point[0] <= market_x
    ]
    supply = curve(
        supply_points,
        layer_id="micro.competition.supply_cases.industry.supply",
        role="micro.curve.marginal",
        model=industry,
    )
    market.layers.extend((supply, curve_name(supply, "$S$", at=0.92)))
    if demand:
        slope = -price / market_q
        intercept = price - slope * market_q
        demand_path = curve(
            (
                (market_q * 0.18, intercept + slope * market_q * 0.18),
                (market_x * 0.92, intercept + slope * market_x * 0.92),
            ),
            layer_id="micro.competition.supply_cases.industry.demand",
            role="micro.curve.demand",
        )
        market.layers.extend((demand_path, curve_name(demand_path, "$D$")))
    market.layers.extend(
        (
            guide(
                (0.0, price),
                (market_q, price),
                layer_id="micro.competition.supply_cases.industry.price",
            ),
            drop_line(market_q, price, layer_id="micro.competition.supply_cases.industry.output"),
            axis_mark(
                "y",
                price,
                "p_{SR}" if demand else "p_0",
                layer_id="micro.competition.supply_cases.industry.p",
            ),
            axis_mark(
                "x",
                market_q,
                "Q_{SR}" if demand else "Q_0",
                layer_id="micro.competition.supply_cases.industry.q",
            ),
        )
    )
    _point(market.layers, (market_q, price), "A", "micro.competition.supply_cases.industry.a")
    if not demand:
        market.layers.extend(
            (
                guide(
                    (0.0, shut),
                    (market_qs, shut),
                    layer_id="micro.competition.supply_cases.industry.shutdown",
                ),
                drop_line(
                    market_qs,
                    shut,
                    layer_id="micro.competition.supply_cases.industry.shutdown_output",
                ),
                axis_mark("y", shut, "p_s", layer_id="micro.competition.supply_cases.industry.ps"),
                axis_mark(
                    "x", market_qs, "Q_s", layer_id="micro.competition.supply_cases.industry.qs"
                ),
            )
        )
        _point(market.layers, (market_qs, shut), "E", "micro.competition.supply_cases.industry.e")

    firm = _cost_panel(
        analysis,
        (shut, price),
        point_names=("E", "A"),
        output_marks=("q_s", "q_{SR}" if demand else "q_0"),
        y_max=price_top,
        title=titles[1],
        theme=selected,
        labels=labels,
        size=size,
        dpi=dpi,
    )
    links = [
        GridLink(0, (market_x, price), 1, (0.0, price), role="micro.guide"),
    ]
    if not demand:
        links.append(GridLink(0, (market_x, shut), 1, (0.0, shut), role="micro.guide"))
    return CanvasGrid([[_finish(market), firm]], links=links, spacing=_SPACING)


def competitive_industry_supply_grid(
    analysis: CostAnalysis,
    firms: int,
    price: float,
    *,
    titles: tuple[str | None, str | None] = ("", ""),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    size: tuple[float, float] = PANEL_SIZE,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """Industry short-run supply beside one representative firm's supply segment."""
    return _industry_supply_grid(
        analysis,
        firms,
        price,
        demand=False,
        titles=titles,
        theme=theme,
        labels=labels,
        size=size,
        dpi=dpi,
    )


def competitive_market_supply_equilibrium_grid(
    analysis: CostAnalysis,
    firms: int,
    price: float,
    *,
    titles: tuple[str | None, str | None] = ("", ""),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    size: tuple[float, float] = PANEL_SIZE,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """Market demand meeting short-run industry supply beside a representative firm."""
    return _industry_supply_grid(
        analysis,
        firms,
        price,
        demand=True,
        titles=titles,
        theme=theme,
        labels=labels,
        size=size,
        dpi=dpi,
    )


__all__ = [
    "competitive_firm_supply_grid",
    "competitive_industry_supply_grid",
    "competitive_market_supply_equilibrium_grid",
]
