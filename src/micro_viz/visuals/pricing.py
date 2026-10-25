"""mosaickit visual builders for two-part tariffs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import Canvas

from micro_viz.pricing import (
    BuyerType,
    IntertemporalPricing,
    PeakLoadPricing,
    TariffOutcome,
    evaluate_tariff,
)
from micro_viz.theme import PlotTheme
from micro_viz.visuals.common import FIGURE_DPI, FIGURE_SIZE, MARGIN, Point
from micro_viz.visuals.plane import Plane


def two_part_tariff_canvas(
    buyers: Sequence[BuyerType],
    outcome: TariffOutcome,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Demand of each buyer type, the constant ``MC`` and the usage fee ``p^*``. The entry fee is
    the shaded consumer-surplus triangle of the buyer with the least surplus served; when the
    usage fee is above MC the rectangle ``(p^* - MC) Q`` is the sales profit."""
    top = max(b.demand.intercept for b in buyers)
    reach = max(b.demand.quantity_intercept for b in buyers)
    plane = Plane(
        prefix="pricing",
        x_label="Q",
        y_label="p",
        x_max=reach,
        y_max=top,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    served = [b for b in buyers if b.surplus(outcome.usage_fee) >= outcome.entry_fee - 1e-9]
    marginal = min(served, key=lambda b: b.surplus(outcome.usage_fee))
    p, mc = outcome.usage_fee, outcome.marginal_cost
    q = marginal.quantity(p)
    plane.area(
        ((0.0, marginal.demand.intercept), (q, p), (0.0, p)),
        plane.t("pricing.entry_fee"),
        shade="light",
    )
    if p > mc + 1e-9:
        plane.area(((0.0, p), (q, p), (q, mc), (0.0, mc)), plane.t("pricing.sales"), shade="mid")
    for index, buyer in enumerate(buyers, start=1):
        plane.line(
            ((0.0, buyer.demand.intercept), (buyer.demand.quantity_intercept, 0.0)),
            plane.t("pricing.demand_index", index=index),
            role="micro.curve.demand",
        )
    plane.line(((0.0, mc), (plane.x_max, mc)), plane.t("pricing.mc"))
    plane.point(
        q,
        p,
        xtext=plane.t("pricing.mark.quantity", output="Q", index=1),
        ytext=plane.t("pricing.mark.usage"),
    )
    if p > mc + 1e-9:
        plane.ymark(mc, plane.t("pricing.mark.marginal_cost"))
    return plane.finish()


def tariff_profit_canvas(
    buyers: Sequence[BuyerType],
    marginal_cost: float,
    usage_fee: float,
    fee_max: float,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Profit from entry fees, from sales and in total against the entry fee ``T`` at a fixed
    usage fee: it steps down each time a buyer type is priced out."""
    thresholds = sorted({b.surplus(usage_fee) for b in buyers if b.surplus(usage_fee) > 0})
    edges = [0.0, *[t for t in thresholds if t < fee_max], fee_max]
    series: dict[str, list[Point]] = {"entry": [], "sales": [], "total": []}
    for low, high in zip(edges, edges[1:], strict=False):
        middle = evaluate_tariff(buyers, marginal_cost, usage_fee, (low + high) / 2)
        for fee in (low, high):
            series["entry"].append((fee, middle.entrants * fee))
            series["sales"].append((fee, middle.sales_profit))
            series["total"].append((fee, middle.entrants * fee + middle.sales_profit))
    ceiling = max(y for pts in series.values() for _, y in pts)
    plane = Plane(
        prefix="pricing.profit",
        x_label=_text(theme, labels, "pricing.axis.fee"),
        y_label=_text(theme, labels, "pricing.axis.profit"),
        x_max=fee_max,
        y_max=ceiling,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    plane.line(series["entry"], plane.t("pricing.curve.entry"), role="micro.curve.demand", at=0.3)
    plane.line(series["sales"], plane.t("pricing.curve.sales"), role="micro.curve.average", at=0.05)
    plane.line(series["total"], plane.t("pricing.curve.total"), at=0.5)
    for index, fee in enumerate((t for t in thresholds if t < fee_max), start=1):
        plane.guide((fee, 0.0), (fee, ceiling))
        plane.xmark(fee, plane.t("pricing.mark.fee_index", index=index))
    return plane.finish()


def _text(theme: PlotTheme | None, labels: Mapping[str, str] | None, key: str) -> str:
    from micro_viz.visuals.common import Texts, resolve_theme

    return Texts(resolve_theme(theme), labels)(key)


def intertemporal_pricing_canvas(
    pricing: IntertemporalPricing,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Two demands and their marginal revenues against a constant ``MC``: the high price is
    charged to the early group, the lower price to the later one."""
    outcome = pricing.solve()
    plane = Plane(
        prefix="pricing.intertemporal",
        x_label="Q",
        y_label="p",
        x_max=pricing.first.quantity_intercept,
        y_max=pricing.first.intercept,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    for index, demand in enumerate((pricing.first, pricing.second), start=1):
        plane.line(
            ((0.0, demand.intercept), (demand.quantity_intercept, 0.0)),
            plane.t("pricing.curve.demand_index", index=index),
            role="micro.curve.demand",
        )
        plane.thin(
            ((0.0, demand.intercept), (demand.quantity_intercept / 2, 0.0)),
            plane.t("pricing.curve.mr_index", index=index),
        )
    mc = pricing.marginal_cost
    plane.line(((0.0, mc), (plane.x_max, mc)), plane.t("pricing.mc"))
    plane.point(
        outcome.first_quantity,
        outcome.first_price,
        xtext=plane.t("pricing.mark.quantity", output="Q", index=1),
        ytext=plane.t("pricing.mark.price_index", index=1),
    )
    plane.point(
        outcome.second_quantity,
        outcome.second_price,
        xtext=plane.t("pricing.mark.quantity", output="Q", index=2),
        ytext=plane.t("pricing.mark.price_index", index=2),
    )
    plane.dot((outcome.first_quantity, mc))
    plane.dot((outcome.second_quantity, mc))
    return plane.finish()


def peak_load_canvas(
    pricing: PeakLoadPricing,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Peak and off-peak demands with their marginal revenues; running cost ``MC`` for both
    periods and ``MC + MC_K`` (the capacity cost) for the peak."""
    outcome = pricing.solve()
    plane = Plane(
        prefix="pricing.peak",
        x_label="Q",
        y_label="p",
        x_max=max(pricing.peak.quantity_intercept, pricing.off_peak.quantity_intercept),
        y_max=max(pricing.peak.intercept, pricing.off_peak.intercept),
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    for key, demand in (("peak", pricing.peak), ("off", pricing.off_peak)):
        plane.line(
            ((0.0, demand.intercept), (demand.quantity_intercept, 0.0)),
            plane.t(f"pricing.curve.demand_{key}"),
            role="micro.curve.demand",
        )
        plane.thin(
            ((0.0, demand.intercept), (demand.quantity_intercept / 2, 0.0)),
            plane.t(f"pricing.curve.mr_{key}"),
        )
    mc, k = pricing.marginal_cost, pricing.capacity_cost
    plane.line(((0.0, mc), (plane.x_max, mc)), plane.t("pricing.mc"))
    if k > 0:
        plane.thin(((0.0, mc + k), (plane.x_max, mc + k)), plane.t("pricing.curve.mc_capacity"))
    plane.point(
        outcome.peak_quantity,
        outcome.peak_price,
        xtext=plane.t("pricing.mark.quantity_peak"),
        ytext=plane.t("pricing.mark.price_peak"),
    )
    plane.point(
        outcome.off_peak_quantity,
        outcome.off_peak_price,
        xtext=None if outcome.shared_capacity else plane.t("pricing.mark.quantity_off"),
        ytext=plane.t("pricing.mark.price_off"),
    )
    plane.dot((outcome.peak_quantity, mc + k))
    plane.dot((outcome.off_peak_quantity, mc))
    return plane.finish()


__all__ = [
    "intertemporal_pricing_canvas",
    "peak_load_canvas",
    "tariff_profit_canvas",
    "two_part_tariff_canvas",
]
