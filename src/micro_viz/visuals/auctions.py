"""mosaickit visual builders for auctions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import Canvas

from micro_viz.auctions import Auction
from micro_viz.theme import PlotTheme
from micro_viz.visuals.common import FIGURE_DPI, FIGURE_SIZE, MARGIN, Texts, resolve_theme
from micro_viz.visuals.plane import Plane


def bid_functions_canvas(
    auctions: Sequence[Auction],
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Bid against value: the 45-degree second-price bid ``b = v`` and, for each auction in
    ``auctions``, the first-price bid ``b = (n - 1) v / n`` below it (the gap is the shading,
    smaller with more bidders)."""
    texts = Texts(resolve_theme(theme), labels)
    top = max(a.max_value for a in auctions)
    plane = Plane(
        prefix="auctions.bids",
        x_label=texts("auctions.axis.value"),
        y_label=texts("auctions.axis.bid"),
        x_max=top,
        y_max=top,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    plane.line(
        ((0.0, 0.0), (top, top)),
        plane.t("auctions.curve.second"),
        role="micro.curve.demand",
        at=0.9,
    )
    for auction in auctions:
        end = auction.max_value
        plane.line(
            ((0.0, 0.0), (end, auction.first_price_bid(end))),
            plane.t("auctions.curve.first", bidders=auction.bidders),
            at=0.9,
        )
    return plane.finish()


def revenue_equivalence_canvas(
    bidders: Sequence[int],
    max_value: float = 1.0,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Expected seller revenue against the number of bidders under both formats: the curves
    coincide (revenue equivalence), rising toward the largest possible value."""
    texts = Texts(resolve_theme(theme), labels)
    ordered = sorted(bidders)
    plane = Plane(
        prefix="auctions.revenue",
        x_label=texts("auctions.axis.bidders"),
        y_label=texts("auctions.axis.revenue"),
        x_max=float(ordered[-1]),
        y_max=max_value,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    first = [(float(n), Auction(n, max_value).expected_revenue_numeric(True)) for n in ordered]
    second = [(float(n), Auction(n, max_value).expected_revenue_numeric(False)) for n in ordered]
    plane.line(first, plane.t("auctions.curve.revenue_first"), at=0.4)
    plane.thin(second, plane.t("auctions.curve.revenue_second"), at=0.9)
    plane.guide((0.0, max_value), (plane.x_max, max_value))
    plane.ymark(max_value, plane.t("auctions.mark.max_value"))
    return plane.finish()


__all__ = ["bid_functions_canvas", "revenue_equivalence_canvas"]
