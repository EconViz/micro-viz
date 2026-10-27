"""mosaickit figure builder for the exhaustible-resource price path."""

from __future__ import annotations

from collections.abc import Mapping

from mosaickit import CanvasGrid

from micro_viz.core.theme import PlotTheme
from micro_viz.markets.capital.model import ExhaustibleResourcePath
from micro_viz.visuals.common import FIGURE_DPI, MARGIN, Texts, resolve_theme
from micro_viz.visuals.plane import PANEL, Plane

STEPS = 60
"""Points per sampled curve."""


def resource_price_path_canvas(
    path: ExhaustibleResourcePath,
    *,
    titles: tuple[str | None, str | None] = (None, None),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """Left, the price path ``p(t)`` rising from ``p_0`` to the choke price at ``T`` above the
    marginal extraction cost ``c``; right, the matching static view: demand ``D`` with the
    quantities extracted at the start and at ``T / 2``, moving up the demand curve."""
    texts = Texts(resolve_theme(theme), labels)
    horizon = path.exhaustion_time
    start = path.initial_price
    left = Plane(
        prefix="capital.path",
        x_label=texts("capital.axis.time"),
        y_label="p",
        x_max=horizon,
        y_max=path.choke_price,
        theme=theme,
        labels=labels,
        title=titles[0],
        margin=margin,
        size=size,
        dpi=dpi,
    )
    left.line(
        [(horizon * i / STEPS, path.price(horizon * i / STEPS)) for i in range(STEPS + 1)],
        left.t("capital.curve.price"),
    )
    left.line(
        ((0.0, path.extraction_cost), (left.x_max, path.extraction_cost)),
        left.t("capital.curve.cost"),
        role="micro.curve.marginal",
    )
    left.ymark(start, left.t("capital.mark.initial_price"))
    left.xmark(horizon, left.t("capital.mark.horizon"))
    left.ymark(path.choke_price, left.t("capital.mark.choke"))
    reach = path.demand_intercept
    right = Plane(
        prefix="capital.demand",
        x_label=texts("capital.axis.quantity"),
        y_label="p",
        x_max=reach,
        y_max=path.choke_price,
        theme=theme,
        labels=labels,
        title=titles[1],
        margin=margin,
        size=size,
        dpi=dpi,
    )
    right.line(
        ((0.0, path.choke_price), (reach, 0.0)),
        right.t("capital.curve.demand"),
        role="micro.curve.demand",
    )
    right.line(
        ((0.0, path.extraction_cost), (right.x_max, path.extraction_cost)),
        right.t("capital.curve.cost"),
        role="micro.curve.marginal",
    )
    for index, moment in enumerate((0.0, horizon / 2), start=1):
        right.point(
            path.quantity(moment),
            path.price(moment),
            xtext=right.t("capital.mark.quantity", index=index),
            ytext=right.t("capital.mark.price", index=index),
        )
    return CanvasGrid([[left.finish(), right.finish()]])


__all__ = ["resource_price_path_canvas"]
