"""Industry factor demand, factor equilibrium, economic rent and land rent."""

from __future__ import annotations

from collections.abc import Mapping

from mosaickit import Canvas, CanvasGrid

from micro_viz.core.theme import PlotTheme
from micro_viz.markets.factors import (
    FactorMarket,
    IndustryFactorDemand,
    InputAdjustment,
    LandMarket,
)
from micro_viz.markets.visuals.factors._base import _plane, segment
from micro_viz.markets.visuals.factors.labour import _labour
from micro_viz.visuals.common import FIGURE_DPI, FIGURE_SIZE, MARGIN
from micro_viz.visuals.plane import PANEL


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
