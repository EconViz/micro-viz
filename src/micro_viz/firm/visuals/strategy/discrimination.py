"""mosaickit figure builders for price discrimination."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import Canvas, CanvasGrid

from micro_viz.core.theme import PlotTheme
from micro_viz.firm.competition import LinearDemand
from micro_viz.firm.costs import CostFunction
from micro_viz.firm.monopoly import Monopolist
from micro_viz.firm.strategy.discrimination.model import BlockPricing, FirstDegree, ThirdDegree
from micro_viz.visuals.common import FIGURE_DPI, FIGURE_SIZE, MARGIN, Point
from micro_viz.visuals.plane import PANEL, Plane, sample


def _plane(
    prefix: str,
    x_max: float,
    y_max: float,
    *,
    theme: PlotTheme | None,
    labels: Mapping[str, str] | None,
    title: str | None,
    margin: float,
    size: tuple[float, float],
    dpi: int,
) -> Plane:
    return Plane(
        prefix=prefix,
        x_label="Q",
        y_label="p",
        x_max=x_max,
        y_max=y_max,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )


def _demand_line(
    plane: Plane, demand: LinearDemand, key: str = "disc.demand", **fields: object
) -> None:
    plane.line(
        ((0.0, demand.intercept), (demand.quantity_intercept, 0.0)),
        plane.t(key, **fields),
        role="micro.curve.demand",
        at=1.0,
    )


def _mr_line(plane: Plane, demand: LinearDemand, key: str = "disc.mr", **fields: object) -> None:
    plane.line(
        ((0.0, demand.intercept), (demand.quantity_intercept / 2, 0.0)),
        plane.t(key, **fields),
        role="micro.curve.marginal_revenue",
        at=1.0,
    )


def _marginal_cost(plane: Plane, cost: CostFunction, top: float) -> None:
    plane.line(sample(cost.marginal_cost, 0.0, top, 40), plane.t("disc.mc"))


def single_price_canvas(
    demand: LinearDemand,
    cost: CostFunction,
    *,
    groups: bool = False,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """One monopoly price (``MR = MC``): the consumer surplus above it and the surplus left
    uncaptured between demand and MC beyond ``Q^*``; ``groups`` also marks the buyers who pay
    far less than they would and those who are priced out."""
    out = Monopolist(demand, cost).solve()
    top = demand.quantity_intercept
    plane = _plane(
        "disc.single",
        top,
        demand.intercept,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    q, p = out.quantity, out.price
    plane.area(
        ((0.0, demand.intercept), (q, p), (0.0, p)), plane.t("disc.consumer_surplus"), shade="light"
    )
    qc = out.competitive_quantity
    plane.area(
        ((q, p), (qc, out.competitive_price), (q, out.marginal_cost)),
        plane.t("disc.uncaptured"),
        shade="mid",
    )
    _demand_line(plane, demand)
    _mr_line(plane, demand)
    _marginal_cost(plane, cost, top)
    plane.point(
        q,
        p,
        xtext=plane.t("disc.mark.output_star", output="Q"),
        ytext=plane.t("disc.mark.price_index", index="m"),
    )
    plane.dot((q, out.marginal_cost))
    if groups:
        plane.xmark(qc, plane.t("disc.mark.output", output="Q", index="c"))
    return plane.finish()


def first_degree_canvas(
    result: FirstDegree,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Perfect discrimination: price follows demand to ``D = MC``; the profit is the area between
    demand and MC, with the extra gain over the single monopoly price shaded darker."""
    demand = result.demand
    plane = _plane(
        "disc.first",
        demand.quantity_intercept,
        demand.intercept,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    mc = [
        (q, result.cost.marginal_cost(q)) for q, _ in sample(lambda x: x, 0.0, result.quantity, 40)
    ]
    upper = [(q, demand.price(q)) for q, _ in sample(lambda x: x, 0.0, result.quantity, 40)]
    plane.area(upper + list(reversed(mc)), plane.t("disc.profit"), shade="mid")
    single = result.single_price
    plane.area(
        (
            (single.quantity, single.price),
            (result.quantity, demand.price(result.quantity)),
            (single.quantity, single.marginal_cost),
        ),
        None,
        shade="dark",
    )
    _demand_line(plane, demand)
    _mr_line(plane, demand)
    _marginal_cost(plane, result.cost, demand.quantity_intercept)
    plane.point(
        result.quantity,
        demand.price(result.quantity),
        xtext=plane.t("disc.mark.output_star", output="Q"),
    )
    return plane.finish()


def block_pricing_canvas(
    result: BlockPricing,
    *,
    average_cost: bool = False,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Equal blocks each sold at the price of its last buyer: a staircase under demand ending at
    ``D = MC``. ``average_cost`` adds the (declining) ATC of the cost function."""
    demand = result.demand
    plane = _plane(
        "disc.blocks",
        demand.quantity_intercept,
        demand.intercept,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    for block in result.blocks:
        plane.area(
            (
                (block.start, 0.0),
                (block.end, 0.0),
                (block.end, block.price),
                (block.start, block.price),
            ),
            None,
            shade="light",
        )
    stairs: list[Point] = []
    for block in result.blocks:
        stairs.extend(((block.start, block.price), (block.end, block.price)))
    plane.line(stairs, None, role="micro.curve.after")
    for index, block in enumerate(result.blocks, start=1):
        plane.ymark(block.price, plane.t("disc.mark.price_index", index=index))
        plane.guide((0.0, block.price), (block.start, block.price))
    _demand_line(plane, demand)
    _marginal_cost(plane, result.cost, demand.quantity_intercept)
    if average_cost:
        top = result.blocks[-1].end
        plane.line(
            [
                (q, result.cost.total_cost(q) / q)
                for q, _ in sample(lambda x: x, top * 0.15, demand.quantity_intercept, 40)
            ],
            plane.t("disc.atc"),
            role="micro.curve.average",
            at=1.0,
        )
    return plane.finish()


def third_degree_canvas(
    result: ThirdDegree,
    *,
    titles: Sequence[str | None] | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """One panel per market (``D_i``, ``MR_i``, the common level ``MC*``) and a last panel with the
    summed ``MR_T`` meeting MC. A market whose demand starts below ``MC*`` is not served."""
    cells: list[Canvas] = []
    top = max(m.demand.intercept for m in result.markets)
    level = result.marginal_cost
    heading = list(titles) if titles is not None else [None] * (len(result.markets) + 1)
    reach = max(m.demand.quantity_intercept for m in result.markets)
    for index, market in enumerate(result.markets, start=1):
        plane = _plane(
            f"disc.market{index}",
            reach,
            top,
            theme=theme,
            labels=labels,
            title=heading[index - 1],
            margin=margin,
            size=size,
            dpi=dpi,
        )
        _demand_line(plane, market.demand, "disc.demand_index", index=index)
        _mr_line(plane, market.demand, "disc.mr_index", index=index)
        plane.line(((0.0, level), (plane.x_max, level)), plane.t("disc.mc"))
        if market.served:
            plane.point(
                market.quantity,
                market.price,
                xtext=plane.t("disc.mark.output", output="Q", index=index),
                ytext=plane.t("disc.mark.price_index", index=index),
            )
            plane.dot((market.quantity, level))
        cells.append(plane.finish())
    plane = _plane(
        "disc.total",
        sum(m.demand.quantity_intercept for m in result.markets) / 1.6,
        top,
        theme=theme,
        labels=labels,
        title=heading[len(result.markets)],
        margin=margin,
        size=size,
        dpi=dpi,
    )
    summed = [point for point in result.summed_marginal_revenue(top) if point[0] > 0]
    plane.line(summed, plane.t("disc.mr_total"), role="micro.curve.marginal_revenue")
    mc = sample(result.cost.marginal_cost, 0.0, plane.x_max, 40)
    plane.line(mc, plane.t("disc.mc"))
    plane.point(
        result.quantity,
        level,
        xtext=plane.t("disc.mark.output", output="Q", index="T"),
        ytext=plane.t("disc.mark.marginal"),
    )
    cells.append(plane.finish())
    return CanvasGrid([cells])


__all__ = [
    "block_pricing_canvas",
    "first_degree_canvas",
    "single_price_canvas",
    "third_degree_canvas",
]
