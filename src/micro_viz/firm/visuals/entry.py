"""mosaickit figure builders for long-run competition."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from mosaickit import Canvas, CanvasGrid

from micro_viz.core.theme import PlotTheme
from micro_viz.firm.competition import LinearDemand, solve_competitive_firm
from micro_viz.firm.costs import CostAnalysis, CubicCost, analyze_costs
from micro_viz.firm.entry.model import IndustryEntry
from micro_viz.firm.longrun import LongRunError, PlantFamily
from micro_viz.visuals.common import FIGURE_DPI, FIGURE_SIZE, MARGIN
from micro_viz.visuals.plane import PANEL, Plane, sample

_COMMON = ("theme", "labels", "margin", "dpi")


@dataclass(frozen=True, slots=True)
class _Style:
    """Settings shared by every panel of one figure."""

    theme: PlotTheme | None
    labels: Mapping[str, str] | None
    margin: float
    size: tuple[float, float]
    dpi: int

    def plane(self, prefix: str, x_max: float, y_max: float, title: str | None) -> Plane:
        return Plane(
            prefix=prefix,
            x_label="Q",
            y_label="p",
            x_max=x_max,
            y_max=y_max,
            theme=self.theme,
            labels=self.labels,
            title=title,
            margin=self.margin,
            size=self.size,
            dpi=self.dpi,
        )


def _firm_curves(
    plane: Plane, analysis: CostAnalysis, *, thin: bool = False, index: int | None = None
) -> None:
    """MC and ATC of a firm; ``thin`` draws them as changed curves named with ``index``."""
    cost = analysis.cost
    low, high = analysis.output_range
    marginal = sample(cost.marginal_cost, low, high)
    average = sample(lambda q: cost.total_cost(q) / q, low, high)
    if index is not None:
        mc_name = plane.t("longrun.mc_index", index=index)
        atc_name = plane.t("longrun.atc_index", index=index)
    else:
        mc_name, atc_name = plane.t("longrun.mc"), plane.t("longrun.atc")
    if thin:
        plane.thin(marginal, mc_name)
        plane.thin(average, atc_name, at=0.0)
    else:
        plane.line(marginal, mc_name)
        plane.line(average, atc_name, role="micro.curve.average", at=0.0)


def _price(plane: Plane, price: float) -> None:
    plane.line(
        ((0.0, price), (plane.x_max, price)), plane.t("longrun.price"), role="micro.curve.price"
    )


def _demand(plane: Plane, demand: LinearDemand, index: int) -> None:
    points = [(0.0, demand.intercept), (demand.quantity_intercept, 0.0)]
    name = plane.t("longrun.demand_index", index=index)
    if index == 1:
        plane.line(points, name, role="micro.curve.demand")
    else:
        plane.line(points, name, role="micro.curve.after.demand")


def _supply(plane: Plane, industry: IndustryEntry, firms: float, index: int, top: float) -> None:
    points = list(industry.curve(firms, top))
    name = plane.t("longrun.supply_index", index=index)
    (plane.line if index == 1 else plane.thin)(points, name)


def _profit_rectangle(plane: Plane, cost: CubicCost, price: float, name: str, key: str) -> float:
    output = solve_competitive_firm(cost, price).output
    average = cost.total_cost(output) / output
    plane.area(((0.0, price), (output, price), (output, average), (0.0, average)), plane.t(key))
    return output


def long_run_firm_canvas(
    family: PlantFamily,
    price: float,
    output_max: float,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    samples: int = 60,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """LAC, LMC and the price line: the firm produces where ``price = LMC`` with the plant whose
    SAC touches LAC there, and the profit is the rectangle between price and LAC."""
    quantity = family.output_at_lmc(price)
    plant = family.best_plant(quantity)
    average = family.lac(quantity)
    low = output_max * 0.12
    lac = sample(family.lac, low, output_max, samples)
    top = max(price, max(y for _, y in lac)) * 1.05
    plane = _Style(theme, labels, margin, size, dpi).plane("longrun", output_max, top, title)
    plane.area(
        ((0.0, price), (quantity, price), (quantity, average), (0.0, average)),
        plane.t("longrun.profit"),
    )
    plane.line(lac, plane.t("longrun.lac"), role="micro.curve.average", at=0.0)
    plane.line(
        [(q, y) for q, y in sample(family.lmc, low, output_max, samples) if y <= top],
        plane.t("longrun.lmc"),
    )
    span = (plant * 0.5, min(output_max, plant * 1.6))
    plane.thin(
        [
            (q, family.sac(plant, q))
            for q, _ in sample(lambda x: x, *span, samples)
            if family.sac(plant, q) <= top
        ],
        plane.t("longrun.sac"),
        at=0.0,
    )
    plane.thin(
        [
            (q, family.smc(plant, q))
            for q, _ in sample(lambda x: x, *span, samples)
            if family.smc(plant, q) <= top
        ],
        plane.t("longrun.smc"),
    )
    _price(plane, price)
    plane.point(
        quantity,
        price,
        xtext=plane.t("plane.star", symbol="Q"),
        ytext=plane.t("longrun.mark.price_index", index=1),
    )
    plane.guide((0.0, average), (quantity, average))
    plane.ymark(average, plane.t("longrun.mark.price_index", index=0))
    return plane.finish()


def entry_canvas(
    industry: IndustryEntry,
    firms: float,
    analysis: CostAnalysis,
    *,
    titles: tuple[str | None, str | None] = (None, None),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """Profit draws entry: the firm (profit rectangle) beside the industry, where more firms
    shift supply right until the price has fallen to the lowest ATC."""
    start = industry.equilibrium(firms)
    final = industry.long_run_firms()
    end = industry.equilibrium(final)
    top = industry.demand.intercept
    common = _Style(theme, labels, margin, size, dpi)
    firm = common.plane("entry.firm", analysis.output_range[1], top, titles[0])
    _profit_rectangle(firm, industry.cost, start.price, "", "longrun.profit")
    _firm_curves(firm, analysis)
    _price(firm, start.price)
    firm.point(
        start.firm_output,
        start.price,
        xtext=firm.t("plane.star", symbol="Q"),
        ytext=firm.t("longrun.mark.price_index", index=1),
    )
    firm.thin(((0.0, end.price), (firm.x_max, end.price)))
    firm.ymark(end.price, firm.t("longrun.mark.price_index", index=2))
    market = common.plane("entry.industry", industry.demand.quantity_intercept, top, titles[1])
    _demand(market, industry.demand, 1)
    _supply(market, industry, firms, 1, top)
    _supply(market, industry, final, 2, top)
    for index, point in enumerate((start, end), start=1):
        market.point(
            point.quantity,
            point.price,
            xtext=market.t("longrun.mark.quantity_index", index=index),
            ytext=market.t("longrun.mark.price_index", index=index),
        )
    return CanvasGrid([[firm.finish(), market.finish()]])


def rent_canvas(
    industry: IndustryEntry,
    advantaged: CubicCost,
    analysis: CostAnalysis,
    advantaged_analysis: CostAnalysis,
    *,
    titles: tuple[str | None, str | None, str | None] = (None, None, None),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """Zero profit for the marginal firm, and a rent rectangle for a firm with lower costs
    (a scarce advantage), beside the long-run industry."""
    price = industry.long_run_price
    firms = industry.long_run_firms()
    top = industry.demand.intercept
    common = _Style(theme, labels, margin, size, dpi)
    cells: list[Canvas] = []
    for number, (cost, view) in enumerate(
        ((industry.cost, analysis), (advantaged, advantaged_analysis))
    ):
        plane = common.plane(f"rent.firm{number}", view.output_range[1], top, titles[number])
        output = solve_competitive_firm(cost, price).output
        if number == 1:
            _profit_rectangle(plane, advantaged, price, "", "longrun.rent")
        _firm_curves(plane, view)
        _price(plane, price)
        plane.point(
            output,
            price,
            xtext=plane.t("plane.star", symbol="Q"),
            ytext=plane.t("longrun.mark.price_index", index=1),
        )
        cells.append(plane.finish())
    market = common.plane("rent.industry", industry.demand.quantity_intercept, top, titles[2])
    point = industry.equilibrium(firms)
    _demand(market, industry.demand, 1)
    _supply(market, industry, firms, 1, top)
    market.point(
        point.quantity,
        point.price,
        xtext=market.t("longrun.mark.quantity_index", index=1),
        ytext=market.t("longrun.mark.price_index", index=1),
    )
    cells.append(market.finish())
    return CanvasGrid([cells])


def _long_run_pair(
    industry: IndustryEntry,
    demand: LinearDemand,
    cost_shift: float,
    analysis: CostAnalysis,
    titles: tuple[str | None, str | None],
    common: _Style,
    prefix: str,
) -> CanvasGrid:
    """Firm and industry after demand rises to ``demand``; each unit of extra industry output
    raises every firm's costs by ``cost_shift`` (zero gives a constant-cost industry)."""
    p_old = industry.long_run_price
    q_old = industry.demand.quantity(p_old)
    shift = 0.0
    if cost_shift > 0:
        low, high = 0.0, demand.intercept
        for _ in range(80):
            middle = (low + high) / 2
            if middle < cost_shift * (demand.quantity(p_old + middle) - q_old):
                low = middle
            else:
                high = middle
        shift = (low + high) / 2
    new_cost = industry.cost.with_unit_tax(shift) if shift > 0 else industry.cost
    new_industry = IndustryEntry(demand, new_cost)
    firms_old = industry.long_run_firms()
    firms_new = new_industry.long_run_firms()
    p_new = new_industry.long_run_price
    top = max(demand.intercept, industry.demand.intercept)
    firm = common.plane(f"{prefix}.firm", analysis.output_range[1], top, titles[0])
    _firm_curves(firm, analysis)
    _price(firm, p_old)
    q_firm = solve_competitive_firm(industry.cost, p_old).output
    firm.point(
        q_firm,
        p_old,
        xtext=firm.t("plane.star", symbol="Q"),
        ytext=firm.t("longrun.mark.price_index", index=1),
    )
    if shift > 0:
        _firm_curves(
            firm, analyze_costs(new_cost, output_range=analysis.output_range), thin=True, index=2
        )
        firm.thin(((0.0, p_new), (firm.x_max, p_new)))
        firm.ymark(p_new, firm.t("longrun.mark.price_index", index=2))
    market = common.plane(f"{prefix}.industry", demand.quantity_intercept, top, titles[1])
    _demand(market, industry.demand, 1)
    _demand(market, demand, 2)
    _supply(market, industry, firms_old, 1, top)
    _supply(market, new_industry, firms_new, 2, top)
    names = market.t("longrun.point_names")
    short = industry.equilibrium(firms_old, demand)
    q_new = demand.quantity(p_new)
    points = ((q_old, p_old), (short.quantity, short.price), (q_new, p_new))
    for letter, (x, y) in zip(names, points, strict=False):
        market.point(x, y, name=letter)
    market.ymark(p_old, market.t("longrun.mark.price_index", index=1))
    market.guide((0.0, p_old), (q_old, p_old))
    if shift > 0:
        market.ymark(p_new, market.t("longrun.mark.price_index", index=2))
        market.guide((0.0, p_new), (q_new, p_new))
    market.line(
        ((q_old, p_old), (q_new, p_new)) if shift > 0 else ((q_old, p_old), (market.x_max, p_old)),
        market.t("longrun.lrs"),
        role="micro.curve.price",
    )
    return CanvasGrid([[firm.finish(), market.finish()]])


def constant_cost_canvas(
    industry: IndustryEntry,
    demand: LinearDemand,
    analysis: CostAnalysis,
    *,
    titles: tuple[str | None, str | None] = (None, None),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """Constant-cost industry: demand rises, price jumps then returns to the same lowest ATC;
    the long-run supply curve LRS is horizontal."""
    common = _Style(theme, labels, margin, size, dpi)
    return _long_run_pair(industry, demand, 0.0, analysis, titles, common, "constant")


def increasing_cost_canvas(
    industry: IndustryEntry,
    demand: LinearDemand,
    cost_shift: float,
    analysis: CostAnalysis,
    *,
    titles: tuple[str | None, str | None] = (None, None),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """Increasing-cost industry: entry raises input prices by ``cost_shift`` per unit of extra
    industry output, so every firm's cost curves rise and LRS slopes up."""
    if cost_shift <= 0:
        raise LongRunError("cost_shift must be positive for an increasing-cost industry.")
    common = _Style(theme, labels, margin, size, dpi)
    return _long_run_pair(industry, demand, cost_shift, analysis, titles, common, "increasing")


__all__ = [
    "constant_cost_canvas",
    "entry_canvas",
    "increasing_cost_canvas",
    "long_run_firm_canvas",
    "rent_canvas",
]
