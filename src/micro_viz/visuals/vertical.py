"""mosaickit figure builders for vertical chains."""

from __future__ import annotations

from collections.abc import Mapping

from mosaickit import Canvas

from micro_viz.theme import PlotTheme
from micro_viz.vertical.model import VerticalChain, transfer_pricing
from micro_viz.visuals.common import FIGURE_DPI, FIGURE_SIZE, MARGIN
from micro_viz.visuals.plane import Plane


def _plane(
    chain: VerticalChain,
    prefix: str,
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
        x_max=chain.demand.quantity_intercept,
        y_max=chain.demand.intercept,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )


def _upstream_cost(plane: Plane, chain: VerticalChain, key: str = "vertical.mc_u") -> None:
    top = plane.start.y_range[1]
    end = plane.x_max
    if chain.upstream_slope > 0:
        end = min(end, (top - chain.upstream_intercept) / chain.upstream_slope)
    plane.line(
        (
            (0.0, chain.upstream_intercept),
            (end, chain.upstream_marginal_cost(end)),
        ),
        plane.t(key),
        role="micro.curve.marginal",
    )


def _nmr(plane: Plane, chain: VerticalChain) -> None:
    start = chain.demand.intercept - chain.downstream_cost
    plane.line(
        ((0.0, start), (start / (2 * chain.demand.slope), 0.0)),
        plane.t("vertical.nmr"),
        role="micro.curve.marginal_revenue",
    )


def double_marginalization_canvas(
    chain: VerticalChain,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Two stacked monopolies: ``D`` (final demand), ``NMR`` (the upstream firm's demand), the
    upstream marginal revenue ``MR_u`` and ``MC_u``. Quantity ``Q_s`` is set where ``MR_u = MC_u``;
    the transfer price ``W_s`` is read on ``NMR`` and the final price ``p_s`` on ``D``."""
    outcome = chain.stacked()
    plane = _plane(chain, "vertical.stacked", theme, labels, title, margin, size, dpi)
    demand = chain.demand
    plane.line(
        ((0.0, demand.intercept), (demand.quantity_intercept, 0.0)),
        plane.t("vertical.demand"),
        role="micro.curve.demand",
    )
    _nmr(plane, chain)
    top = demand.intercept - chain.downstream_cost
    plane.thin(
        ((0.0, top), (top / (4 * demand.slope), 0.0)),
        plane.t("vertical.mr_u"),
    )
    _upstream_cost(plane, chain)
    q = outcome.quantity
    plane.point(
        q,
        outcome.final_price,
        xtext=plane.t("vertical.mark.quantity_stacked"),
        ytext=plane.t("vertical.mark.price_stacked"),
    )
    plane.point(q, outcome.transfer_price, ytext=plane.t("vertical.mark.transfer_stacked"))
    plane.dot((q, chain.upstream_marginal_cost(q)))
    return plane.finish()


def integrated_firm_canvas(
    chain: VerticalChain,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """An integrated firm sets ``NMR = MC_u``: output ``Q_i`` exceeds the stacked output ``Q_s``
    (drawn as a mark) and the final price ``p_i`` is lower."""
    outcome = chain.integrated()
    stacked = chain.stacked()
    plane = _plane(chain, "vertical.integrated", theme, labels, title, margin, size, dpi)
    demand = chain.demand
    plane.line(
        ((0.0, demand.intercept), (demand.quantity_intercept, 0.0)),
        plane.t("vertical.demand"),
        role="micro.curve.demand",
    )
    _nmr(plane, chain)
    _upstream_cost(plane, chain)
    q = outcome.quantity
    plane.point(
        q,
        outcome.final_price,
        xtext=plane.t("vertical.mark.quantity_integrated"),
        ytext=plane.t("vertical.mark.price_integrated"),
    )
    plane.dot((q, chain.net_marginal_revenue(q)))
    plane.guide((q, chain.net_marginal_revenue(q)), (q, outcome.final_price))
    plane.xmark(stacked.quantity, plane.t("vertical.mark.quantity_stacked"))
    return plane.finish()


def transfer_price_outside_market_canvas(
    chain: VerticalChain,
    market_price: float,
    *,
    kinked: bool = True,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """With an outside market at ``P_m`` the firm's effective marginal cost is ``MC_u`` up to the
    quantity ``Q_u`` where it meets ``P_m`` and flat at ``P_m`` beyond (``kinked``); without it,
    the figure shows the optimal transfer price ``P_m`` with downstream use ``Q_d`` and the
    surplus ``Q_u - Q_d`` sold outside."""
    result = transfer_pricing(chain, market_price)
    plane = _plane(chain, "vertical.transfer", theme, labels, title, margin, size, dpi)
    demand = chain.demand
    plane.line(
        ((0.0, demand.intercept), (demand.quantity_intercept, 0.0)),
        plane.t("vertical.demand"),
        role="micro.curve.demand",
    )
    _nmr(plane, chain)
    if kinked:
        plane.line(
            (
                (0.0, chain.upstream_intercept),
                (result.upstream_quantity, market_price),
                (plane.x_max, market_price),
            ),
            plane.t("vertical.mc_kinked"),
            role="micro.curve.marginal",
        )
        q = result.downstream_quantity
        plane.point(
            q,
            demand.intercept - demand.slope * q,
            xtext=plane.t("vertical.mark.quantity_downstream"),
            ytext=plane.t("vertical.mark.price_final"),
        )
        plane.dot((q, market_price))
        plane.guide((q, market_price), (q, demand.intercept - demand.slope * q))
        plane.ymark(market_price, plane.t("vertical.mark.market_price"))
    else:
        _upstream_cost(plane, chain)
        plane.line(
            ((0.0, market_price), (plane.x_max, market_price)),
            plane.t("vertical.market"),
            role="micro.curve.price",
        )
        plane.point(
            result.downstream_quantity,
            market_price,
            xtext=plane.t("vertical.mark.quantity_downstream"),
            ytext=plane.t("vertical.mark.market_price"),
        )
        plane.xmark(result.upstream_quantity, plane.t("vertical.mark.quantity_upstream"))
        plane.dot((result.upstream_quantity, market_price))
    return plane.finish()


__all__ = [
    "double_marginalization_canvas",
    "integrated_firm_canvas",
    "transfer_price_outside_market_canvas",
]
