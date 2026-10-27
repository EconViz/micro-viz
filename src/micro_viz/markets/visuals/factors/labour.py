"""Union wage setting, two-sector labour and firm hiring."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import Canvas, CanvasGrid

from micro_viz.core.theme import PlotTheme
from micro_viz.markets.factors import (
    CapitalAdjustment,
    DerivedDemand,
    FactorError,
    FactorMarket,
    TwoSectorLabor,
    UnionWageSetting,
)
from micro_viz.markets.visuals.factors._base import _plane, segment
from micro_viz.visuals.common import FIGURE_DPI, FIGURE_SIZE, MARGIN
from micro_viz.visuals.plane import PANEL, Plane


def union_wage_canvas(
    setting: UnionWageSetting,
    wage: float | None = None,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """A union picks a point on the firm's labour demand: employment ``L``, the wage-bill
    rectangle and the rent above members' supply price."""
    d, s = setting.demand, setting.supply
    x_max, y_max = d.quantity_intercept, d.intercept
    plane = _plane(
        "factors.union",
        "labor",
        x_max,
        y_max,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    out = setting.solve(wage)
    n, w = out.employment, out.wage
    plane.area(
        ((0.0, w), (n, w), (n, s.wage(n)), (0.0, s.wage(0.0))),
        plane.t("factors.region.rent"),
        shade="dark",
    )
    plane.area(
        ((0.0, 0.0), (n, 0.0), (n, s.wage(n)), (0.0, s.wage(0.0))),
        plane.t("factors.region.cost"),
        shade="light",
    )
    plane.line(
        segment(d.intercept, -d.slope, x_max, y_max),
        plane.t("factors.labor.curve.value"),
        role="micro.curve.demand",
    )
    plane.line(segment(s.intercept, s.slope, x_max, y_max), plane.t("factors.labor.curve.supply"))
    plane.point(
        n,
        w,
        xtext=plane.t("factors.labor.mark.q_star"),
        ytext=plane.t("factors.labor.mark.p_union"),
    )
    return plane.finish()


def two_sector_labor_canvas(
    model: TwoSectorLabor,
    union_wage: float,
    *,
    titles: tuple[str | None, str | None] = (None, None),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """Two sectors: a union wage above the competitive wage ``W_c`` cuts employment in sector 1,
    the displaced workers crowd into sector 2 and lower its wage."""
    out = model.solve(union_wage)
    top = max(model.demand_1.intercept, model.demand_2.intercept)
    reach = max(model.demand_1.quantity_intercept, model.demand_2.quantity_intercept)
    cells = []
    for index, (demand, title) in enumerate(
        zip((model.demand_1, model.demand_2), titles, strict=True), start=1
    ):
        plane = _plane(
            f"factors.sector{index}",
            "labor",
            reach,
            top,
            theme=theme,
            labels=labels,
            title=title,
            margin=margin,
            size=size,
            dpi=dpi,
            x_key=f"factors.labor.axis.x{index}",
        )
        plane.line(
            segment(demand.intercept, -demand.slope, reach, top),
            plane.t("factors.labor.curve.value_index", index=index),
            role="micro.curve.demand",
        )
        plane.guide((0.0, out.competitive_wage), (plane.x_max, out.competitive_wage))
        plane.ymark(out.competitive_wage, plane.t("factors.labor.mark.p_c"))
        if index == 1:
            employment, wage = out.employment_1, out.union_wage
            plane.xmark(out.competitive_employment_1, plane.t("factors.labor.mark.n_c", index=1))
        else:
            employment, wage = out.employment_2, out.wage_2
            plane.xmark(out.competitive_employment_2, plane.t("factors.labor.mark.n_c", index=2))
        plane.point(
            employment,
            wage,
            xtext=plane.t("factors.labor.mark.n_new", index=index),
            ytext=plane.t("factors.labor.mark.w_new", index=index),
        )
        cells.append(plane.finish())
    return CanvasGrid([cells])


def _labour(
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
    return _plane(
        prefix,
        "labor",
        x_max,
        y_max,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )


def derived_demand_canvas(
    derived: DerivedDemand,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """``VMP`` (competitive output market) above ``MRP`` (monopoly output market): both are the
    marginal product valued at the price, the monopolist's marginal revenue being lower."""
    vmp = derived.value_of_marginal_product
    mrp = derived.demand
    plane = _labour(
        "factors.derived",
        vmp.quantity_intercept,
        vmp.intercept,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    plane.line(
        segment(vmp.intercept, -vmp.slope, plane.x_max, vmp.intercept),
        plane.t("factors.labor.curve.vmp"),
        role="micro.curve.demand",
        at=0.12,
    )
    plane.line(
        segment(mrp.intercept, -mrp.slope, plane.x_max, vmp.intercept),
        plane.t("factors.labor.curve.value"),
        role="micro.curve.marginal_revenue",
        at=0.12,
    )
    return plane.finish()


def firm_hiring_canvas(
    market: FactorMarket,
    wage: float,
    lower_wage: float | None = None,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """A firm facing the flat supply ``W*`` hires where ``MRP = W*``. With ``lower_wage`` the
    flat supply shifts down (a thin solid line) and hiring moves along the MRP curve."""
    d = market.demand
    plane = _labour(
        "factors.hiring",
        d.quantity_intercept,
        d.intercept,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    plane.line(
        segment(d.intercept, -d.slope, plane.x_max, d.intercept),
        plane.t("factors.labor.curve.value"),
        role="micro.curve.demand",
    )
    plane.line(((0.0, wage), (plane.x_max, wage)), plane.t("factors.labor.curve.supply"))
    quantity = market.firm_hiring(wage)
    plane.point(
        quantity,
        wage,
        xtext=plane.t("factors.labor.mark.q_star"),
        ytext=plane.t("factors.labor.mark.p_star"),
    )
    if lower_wage is not None:
        plane.thin(
            ((0.0, lower_wage), (plane.x_max, lower_wage)),
            plane.t("factors.labor.curve.supply_new"),
        )
        plane.point(
            market.firm_hiring(lower_wage),
            lower_wage,
            xtext=plane.t("factors.labor.mark.q_new"),
            ytext=plane.t("factors.labor.mark.p_new"),
        )
        plane.arrow((quantity, wage), (quantity, lower_wage))
    return plane.finish()


def capital_adjustment_canvas(
    adjustment: CapitalAdjustment,
    wages: Sequence[float],
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """MRP curves for increasing capital with one hiring point per curve at the matching entry of
    ``wages`` (a falling wage prompts the firm to add capital), joined by the demand locus."""
    if len(wages) != len(adjustment.levels):
        raise FactorError("Need one wage per capital level.")
    top = adjustment.curve(len(adjustment.levels) - 1)
    plane = _labour(
        "factors.capital",
        top.quantity_intercept,
        top.intercept,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    points = []
    for index in range(len(adjustment.levels)):
        curve = adjustment.curve(index)
        plane.line(
            segment(curve.intercept, -curve.slope, plane.x_max, top.intercept),
            plane.t("factors.labor.curve.mrp_k", index=index + 1),
            role="micro.curve.demand" if index == 0 else "micro.curve.after",
        )
        points.append((adjustment.hiring(index, wages[index]), wages[index]))
    plane.line(points, plane.t("factors.labor.curve.locus"), role="micro.curve.marginal")
    for point in points:
        plane.dot(point)
    return plane.finish()
