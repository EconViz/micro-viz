"""mosaickit figure builder for the advertising decision."""

from __future__ import annotations

from collections.abc import Mapping

from mosaickit import Canvas

from micro_viz.core.theme import PlotTheme
from micro_viz.firm.strategy.advertising.model import AdvertisingDecision
from micro_viz.visuals.common import FIGURE_DPI, FIGURE_SIZE, MARGIN
from micro_viz.visuals.plane import Plane

STEPS = 60
"""Points per sampled average-cost curve."""


def advertising_effect_canvas(
    decision: AdvertisingDecision,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """``AR`` shifts out to ``AR'`` and average cost up to ``AC'``; the rectangles show profit
    before (lighter) and after (darker). Changed curves are thin and solid."""
    base, new = decision.baseline, decision.advertised
    before, after = decision.before(), decision.after()
    plane = Plane(
        prefix="advertising",
        x_label="Q",
        y_label="p",
        x_max=new.quantity_intercept,
        y_max=new.intercept,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    mc = decision.marginal_cost
    if before.profit > 0:
        plane.area(
            (
                (0.0, before.price),
                (before.quantity, before.price),
                (before.quantity, before.average_cost),
                (0.0, before.average_cost),
            ),
            plane.t("advertising.profit_before"),
            shade="light",
        )
    if after.profit > 0:
        plane.area(
            (
                (0.0, after.price),
                (after.quantity, after.price),
                (after.quantity, after.average_cost),
                (0.0, after.average_cost),
            ),
            plane.t("advertising.profit_after"),
            shade="mid",
        )
    plane.line(
        ((0.0, base.intercept), (base.quantity_intercept, 0.0)),
        plane.t("advertising.ar"),
        role="micro.curve.demand",
    )
    plane.thin(((0.0, new.intercept), (new.quantity_intercept, 0.0)), plane.t("advertising.ar_new"))
    plane.thin(
        ((0.0, base.intercept), (base.quantity_intercept / 2, 0.0)),
        plane.t("advertising.mr"),
    )
    plane.thin(
        ((0.0, new.intercept), (new.quantity_intercept / 2, 0.0)), plane.t("advertising.mr_new")
    )
    plane.line(((0.0, mc), (plane.x_max, mc)), plane.t("advertising.mc"))
    floor = max(before.quantity, after.quantity) / 6 or 1.0
    reach = plane.x_max
    for advertised in (False, True):
        points = [
            (q, decision.average_cost(q, advertised))
            for q in (floor + (reach - floor) * i / STEPS for i in range(STEPS + 1))
        ]
        if advertised:
            plane.thin(points, plane.t("advertising.ac_new"), at=0.95)
        else:
            plane.line(points, plane.t("advertising.ac"), role="micro.curve.average", at=0.95)
    plane.point(
        before.quantity,
        before.price,
        xtext=plane.t("advertising.mark.quantity", index=0),
        ytext=plane.t("advertising.mark.price", index=0),
    )
    plane.point(
        after.quantity,
        after.price,
        xtext=plane.t("advertising.mark.quantity", index=1),
        ytext=plane.t("advertising.mark.price", index=1),
    )
    return plane.finish()


__all__ = ["advertising_effect_canvas"]
