"""mosaickit visual builders for monopsony, union wage setting and two-sector labour markets."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import Canvas, CanvasGrid

from micro_viz.factors import (
    CapitalAdjustment,
    DerivedDemand,
    FactorError,
    FactorMarket,
    IndustryFactorDemand,
    InputAdjustment,
    LandMarket,
    LinearSupply,
    LinearValue,
    Monopsonist,
    TwoSectorLabor,
    UnionWageSetting,
)
from micro_viz.theme import PlotTheme
from micro_viz.visuals.common import FIGURE_DPI, FIGURE_SIZE, MARGIN, Point, Texts, resolve_theme
from micro_viz.visuals.plane import PANEL, Plane


def segment(intercept: float, slope: float, x_max: float, y_max: float) -> tuple[Point, Point]:
    """The part of ``y = intercept + slope x`` inside ``[0, x_max] x [0, y_max]``."""
    low, high = 0.0, x_max
    if slope > 0:
        low = max(low, -intercept / slope)
        high = min(high, (y_max - intercept) / slope)
    elif slope < 0:
        low = max(low, (y_max - intercept) / slope)
        high = min(high, -intercept / slope)
    return (low, intercept + slope * low), (high, intercept + slope * high)


def _plane(
    prefix: str,
    kind: str,
    x_max: float,
    y_max: float,
    *,
    theme: PlotTheme | None,
    labels: Mapping[str, str] | None,
    title: str | None,
    margin: float,
    size: tuple[float, float],
    dpi: int,
    x_key: str | None = None,
) -> Plane:
    texts = Texts(resolve_theme(theme), labels)
    return Plane(
        prefix=prefix,
        x_label=texts(x_key or f"factors.{kind}.axis.x"),
        y_label=texts(f"factors.{kind}.axis.y"),
        x_max=x_max,
        y_max=y_max,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )


def _extent(model: Monopsonist) -> tuple[float, float]:
    return model.value.quantity_intercept, model.value.intercept


def _monopsony_plane(
    plane: Plane, model: Monopsonist, kind: str, *, competitive_marks: bool = True
) -> None:
    """Value, supply (AE) and ME curves with the monopsony and competitive points marked."""
    x_max, y_max = plane.x_max, plane.start.y_range[1]
    result = model.solve()
    s, v = model.supply, model.value
    plane.line(
        segment(v.intercept, -v.slope, x_max, y_max),
        plane.t(f"factors.{kind}.curve.value"),
        role="micro.curve.demand",
    )
    plane.line(segment(s.intercept, s.slope, x_max, y_max), plane.t(f"factors.{kind}.curve.ae"))
    plane.line(
        segment(s.intercept, 2 * s.slope, x_max, y_max),
        plane.t(f"factors.{kind}.curve.me"),
        role="micro.curve.marginal",
    )
    plane.point(
        result.quantity,
        result.wage,
        xtext=plane.t(f"factors.{kind}.mark.q_star"),
        ytext=plane.t(f"factors.{kind}.mark.p_star"),
    )
    plane.guide((result.quantity, result.wage), (result.quantity, result.marginal_value))
    plane.dot((result.quantity, result.marginal_value))
    if competitive_marks:
        plane.point(
            result.competitive_quantity,
            result.competitive_wage,
            xtext=plane.t(f"factors.{kind}.mark.q_c"),
            ytext=plane.t(f"factors.{kind}.mark.p_c"),
        )


def monopsony_canvas(
    model: Monopsonist,
    *,
    labor: bool = False,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Monopsony: the buyer hires where ``ME = MV`` (``MRP`` for labour) and pays the supply
    price at that quantity, below the competitive quantity and price. ``labor`` switches the
    text to ``L``, ``W`` and ``MRP``."""
    kind = "labor" if labor else "input"
    x_max, y_max = _extent(model)
    plane = _plane(
        "factors.monopsony",
        kind,
        x_max,
        y_max,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    _monopsony_plane(plane, model, kind)
    return plane.finish()


def competitive_pair_canvas(
    value: LinearValue,
    supply: LinearSupply,
    price: float,
    *,
    titles: tuple[str | None, str | None] = (None, None),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """A competitive buyer (flat ``ME = AE`` at ``price`` against ``MV``) beside a competitive
    seller (flat ``MR = AR`` at ``price`` against ``MC``)."""
    x_max, y_max = value.quantity_intercept, value.intercept
    cells = []
    for side, title in zip(("buyer", "seller"), titles, strict=True):
        plane = _plane(
            f"factors.competitive.{side}",
            "input",
            x_max,
            y_max,
            theme=theme,
            labels=labels,
            title=title,
            margin=margin,
            size=size,
            dpi=dpi,
        )
        if side == "buyer":
            plane.line(
                segment(value.intercept, -value.slope, x_max, y_max),
                plane.t("factors.curve.mv"),
                role="micro.curve.demand",
            )
            level, quantity = price, (value.intercept - price) / value.slope
            flat = plane.t("factors.curve.me_ae")
        else:
            plane.line(
                segment(supply.intercept, supply.slope, x_max, y_max), plane.t("factors.curve.mc")
            )
            level, quantity = price, supply.quantity(price)
            flat = plane.t("factors.curve.mr_ar")
        plane.line(((0.0, level), (plane.x_max, level)), flat, role="micro.curve.price")
        plane.point(
            quantity,
            level,
            xtext=plane.t("factors.input.mark.q_star"),
            ytext=plane.t("factors.input.mark.p_star"),
        )
        cells.append(plane.finish())
    return CanvasGrid([cells])


def monopoly_monopsony_pair_canvas(
    model: Monopsonist,
    *,
    titles: tuple[str | None, str | None] = (None, None),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """Monopoly (``AR``, ``MR``, ``MC``) beside monopsony (``MV``, ``ME``, ``AE``) built from
    the same pair of linear curves: the monopolist's demand is the value curve and its cost the
    supply curve."""
    x_max, y_max = _extent(model)
    s, v = model.supply, model.value
    left = _plane(
        "factors.pair.monopoly",
        "input",
        x_max,
        y_max,
        theme=theme,
        labels=labels,
        title=titles[0],
        margin=margin,
        size=size,
        dpi=dpi,
    )
    left.line(
        segment(v.intercept, -v.slope, x_max, y_max),
        left.t("factors.curve.ar"),
        role="micro.curve.demand",
    )
    left.line(
        segment(v.intercept, -2 * v.slope, x_max, y_max),
        left.t("factors.curve.mr"),
        role="micro.curve.marginal_revenue",
    )
    left.line(segment(s.intercept, s.slope, x_max, y_max), left.t("factors.curve.mc"))
    quantity = (v.intercept - s.intercept) / (2 * v.slope + s.slope)
    price = v.value(quantity)
    left.point(
        quantity,
        price,
        xtext=left.t("factors.input.mark.q_star"),
        ytext=left.t("factors.input.mark.p_star"),
    )
    left.guide((quantity, s.wage(quantity)), (quantity, price))
    left.dot((quantity, s.wage(quantity)))
    right = _plane(
        "factors.pair.monopsony",
        "input",
        x_max,
        y_max,
        theme=theme,
        labels=labels,
        title=titles[1],
        margin=margin,
        size=size,
        dpi=dpi,
    )
    _monopsony_plane(right, model, "input", competitive_marks=False)
    return CanvasGrid([[left.finish(), right.finish()]])


def supply_elasticity_canvas(
    value: LinearValue,
    supplies: Sequence[LinearSupply],
    *,
    titles: Sequence[str | None] | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """One monopsony panel per supply curve, on common axes: the flatter (more elastic) the
    supply, the closer ``ME`` lies to ``AE``."""
    heading = list(titles) if titles is not None else [None] * len(supplies)
    cells: list[Canvas] = []
    x_max, y_max = value.quantity_intercept, value.intercept
    for index, supply in enumerate(supplies, start=1):
        plane = _plane(
            f"factors.elasticity.s{index}",
            "input",
            x_max,
            y_max,
            theme=theme,
            labels=labels,
            title=heading[index - 1],
            margin=margin,
            size=size,
            dpi=dpi,
        )
        _monopsony_plane(plane, Monopsonist(supply, value), "input", competitive_marks=False)
        cells.append(plane.finish())
    return CanvasGrid([cells])


def monopsony_dwl_canvas(
    model: Monopsonist,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Monopsony against the competitive outcome: the rectangle ``A`` is the transfer from
    sellers to the buyer and the triangles ``B`` and ``C`` (above and below the competitive
    price) together are the deadweight loss."""
    x_max, y_max = _extent(model)
    plane = _plane(
        "factors.dwl",
        "input",
        x_max,
        y_max,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    r = model.solve()
    q, w, qc, wc, mv = (
        r.quantity,
        r.wage,
        r.competitive_quantity,
        r.competitive_wage,
        r.marginal_value,
    )
    plane.area(
        ((0.0, w), (q, w), (q, wc), (0.0, wc)), plane.t("factors.region.transfer"), shade="mid"
    )
    plane.area(((q, wc), (qc, wc), (q, mv)), plane.t("factors.region.upper"), shade="dark")
    plane.area(((q, w), (qc, wc), (q, wc)), plane.t("factors.region.lower"), shade="light")
    _monopsony_plane(plane, model, "input")
    return plane.finish()


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


def industry_factor_demand_canvas(
    industry: IndustryFactorDemand,
    anchor_wage: float,
    *,
    titles: tuple[str | None, str | None] = (None, None),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """A firm's demand beside the industry's: the dashed-free pair shows the horizontal sum
    of firm demands (thin) and the steeper industry demand through the same anchor."""
    firm = industry.firm
    left = _labour(
        "factors.industry.firm",
        firm.quantity_intercept,
        firm.intercept,
        theme=theme,
        labels=labels,
        title=titles[0],
        margin=margin,
        size=size,
        dpi=dpi,
    )
    left.line(
        segment(firm.intercept, -firm.slope, left.x_max, firm.intercept),
        left.t("factors.labor.curve.firm"),
        role="micro.curve.demand",
    )
    left.point(
        industry.firm_quantity(anchor_wage),
        anchor_wage,
        xtext=left.t("factors.labor.mark.q_firm"),
        ytext=left.t("factors.labor.mark.p_star"),
    )
    reach = industry.summed_quantity(0.0)
    right = _labour(
        "factors.industry.market",
        reach,
        firm.intercept,
        theme=theme,
        labels=labels,
        title=titles[1],
        margin=margin,
        size=size,
        dpi=dpi,
    )
    wages = [firm.intercept * i / 40 for i in range(41)]
    right.thin(
        [(industry.summed_quantity(w), w) for w in wages],
        right.t("factors.labor.curve.sum"),
        at=0.9,
    )
    right.line(
        [(industry.industry_quantity(w, anchor_wage), w) for w in wages],
        right.t("factors.labor.curve.industry"),
        role="micro.curve.demand",
        at=0.15,
    )
    right.point(
        industry.summed_quantity(anchor_wage),
        anchor_wage,
        xtext=right.t("factors.labor.mark.q_industry"),
        ytext=right.t("factors.labor.mark.p_star"),
    )
    return CanvasGrid([[left.finish(), right.finish()]])


def short_long_run_canvas(
    adjustment: InputAdjustment,
    wage_max: float,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Short- and long-run input demand through one point, the long run flatter."""
    plane = _labour(
        "factors.adjustment",
        adjustment.anchor_quantity + adjustment.anchor_wage / adjustment.long_slope,
        wage_max,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    for name, slope in (("short", adjustment.short_slope), ("long", adjustment.long_slope)):
        intercept = adjustment.anchor_wage + slope * adjustment.anchor_quantity
        plane.line(
            segment(intercept, -slope, plane.x_max, wage_max),
            plane.t(f"factors.labor.curve.{name}"),
            role="micro.curve.demand" if name == "short" else "micro.curve.marginal",
        )
    plane.point(
        adjustment.anchor_quantity,
        adjustment.anchor_wage,
        xtext=plane.t("factors.labor.mark.q_star"),
        ytext=plane.t("factors.labor.mark.p_star"),
    )
    return plane.finish()


def market_supply_canvas(
    market: FactorMarket,
    *,
    titles: tuple[str | None, str | None] = (None, None),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """Upward market supply of an input beside the flat supply one firm faces at the market
    wage."""
    quantity, wage = market.equilibrium()
    d, s = market.demand, market.supply
    cells = []
    for side, title in zip(("market", "firm"), titles, strict=True):
        plane = _labour(
            f"factors.supply.{side}",
            d.quantity_intercept,
            d.intercept,
            theme=theme,
            labels=labels,
            title=title,
            margin=margin,
            size=size,
            dpi=dpi,
        )
        if side == "market":
            plane.line(
                segment(d.intercept, -d.slope, plane.x_max, d.intercept),
                plane.t("factors.labor.curve.value"),
                role="micro.curve.demand",
            )
            plane.line(
                segment(s.intercept, s.slope, plane.x_max, d.intercept),
                plane.t("factors.labor.curve.supply"),
            )
            plane.point(
                quantity,
                wage,
                xtext=plane.t("factors.labor.mark.q_star"),
                ytext=plane.t("factors.labor.mark.p_star"),
            )
        else:
            plane.line(
                ((0.0, wage), (plane.x_max, wage)), plane.t("factors.labor.curve.supply_firm")
            )
            plane.ymark(wage, plane.t("factors.labor.mark.p_star"))
        cells.append(plane.finish())
    return CanvasGrid([cells])


def factor_equilibrium_canvas(
    competitive: FactorMarket,
    monopoly: FactorMarket,
    *,
    titles: tuple[str | None, str | None] = (None, None),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """Labour-market equilibrium with a competitive output market (``MRP = VMP``) beside one
    with a monopoly output market (lower MRP: lower wage and employment)."""
    top = max(competitive.demand.intercept, monopoly.demand.intercept)
    reach = max(competitive.demand.quantity_intercept, monopoly.demand.quantity_intercept)
    cells = []
    for side, market, title in zip(
        ("competitive", "monopoly"), (competitive, monopoly), titles, strict=True
    ):
        plane = _labour(
            f"factors.equilibrium.{side}",
            reach,
            top,
            theme=theme,
            labels=labels,
            title=title,
            margin=margin,
            size=size,
            dpi=dpi,
        )
        d, s = market.demand, market.supply
        plane.line(
            segment(d.intercept, -d.slope, plane.x_max, top),
            plane.t("factors.labor.curve.value"),
            role="micro.curve.demand",
        )
        plane.line(
            segment(s.intercept, s.slope, plane.x_max, top), plane.t("factors.labor.curve.supply")
        )
        quantity, wage = market.equilibrium()
        plane.point(
            quantity,
            wage,
            xtext=plane.t("factors.labor.mark.q_star"),
            ytext=plane.t("factors.labor.mark.p_star"),
        )
        cells.append(plane.finish())
    return CanvasGrid([cells])


def economic_rent_canvas(
    market: FactorMarket,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Economic rent: the triangle between the market wage and the supply curve up to
    employment."""
    d, s = market.demand, market.supply
    plane = _labour(
        "factors.rent",
        d.quantity_intercept,
        d.intercept,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    quantity, wage = market.equilibrium()
    plane.area(
        ((0.0, wage), (quantity, wage), (0.0, s.intercept)),
        plane.t("factors.region.rent"),
        shade="mid",
    )
    plane.line(
        segment(d.intercept, -d.slope, plane.x_max, d.intercept),
        plane.t("factors.labor.curve.value"),
        role="micro.curve.demand",
    )
    plane.line(
        segment(s.intercept, s.slope, plane.x_max, d.intercept),
        plane.t("factors.labor.curve.supply"),
    )
    plane.point(
        quantity,
        wage,
        xtext=plane.t("factors.labor.mark.q_star"),
        ytext=plane.t("factors.labor.mark.p_star"),
    )
    return plane.finish()


def land_rent_canvas(
    land: LandMarket,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Vertical land supply at ``supply`` with demand setting the rent ``R*``; the whole rectangle
    under the rent is economic rent."""
    d = land.demand
    plane = _plane(
        "factors.land",
        "land",
        d.quantity_intercept,
        d.intercept,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    rent = land.rent
    plane.area(
        ((0.0, rent), (land.supply, rent), (land.supply, 0.0), (0.0, 0.0)),
        plane.t("factors.region.rent"),
        shade="mid",
    )
    plane.line(
        segment(d.intercept, -d.slope, plane.x_max, d.intercept),
        plane.t("factors.land.curve.demand"),
        role="micro.curve.demand",
    )
    plane.line(
        ((land.supply, 0.0), (land.supply, d.intercept)), plane.t("factors.land.curve.supply")
    )
    plane.point(
        land.supply,
        rent,
        xtext=plane.t("factors.land.mark.q_star"),
        ytext=plane.t("factors.land.mark.p_star"),
    )
    return plane.finish()


__all__ = [
    "capital_adjustment_canvas",
    "competitive_pair_canvas",
    "derived_demand_canvas",
    "economic_rent_canvas",
    "factor_equilibrium_canvas",
    "firm_hiring_canvas",
    "industry_factor_demand_canvas",
    "land_rent_canvas",
    "market_supply_canvas",
    "monopoly_monopsony_pair_canvas",
    "monopsony_canvas",
    "monopsony_dwl_canvas",
    "short_long_run_canvas",
    "supply_elasticity_canvas",
    "two_sector_labor_canvas",
    "union_wage_canvas",
]
