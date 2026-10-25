"""mosaickit visual builders for two-part tariffs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import Canvas

from micro_viz.pricing import BuyerType, TariffOutcome, evaluate_tariff
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


__all__ = ["tariff_profit_canvas", "two_part_tariff_canvas"]
