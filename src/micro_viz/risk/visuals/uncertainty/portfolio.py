"""Risk-return choice and mean-variance frontier figures."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import Canvas

from micro_viz.core.theme import PlotTheme
from micro_viz.risk.uncertainty import (
    MeanVarianceInvestor,
    RiskReturnLine,
    TwoAssetFrontier,
)
from micro_viz.risk.visuals.uncertainty._base import STEPS
from micro_viz.visuals.common import FIGURE_DPI, FIGURE_SIZE, MARGIN, Texts, resolve_theme
from micro_viz.visuals.plane import Plane


def risk_return_choice_canvas(
    line: RiskReturnLine,
    investors: Sequence[MeanVarianceInvestor],
    level: float,
    sd_max: float,
    market_sd: float | None = None,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """The risk-return line with each investor's indifference curve tangent to it. With
    ``market_sd`` the market portfolio ``M`` is marked and the part beyond it (borrowing to hold
    more risk) is a thin solid segment."""
    texts = Texts(resolve_theme(theme), labels)
    choices = [line.choice(investor) for investor in investors]
    top = max(
        [line.mean(sd_max)]
        + [
            investor.indifference_mean(investor.utility(mean, sd), sd_max)
            for investor, (sd, mean) in zip(investors, choices, strict=True)
        ]
    )
    plane = Plane(
        prefix="uncertainty.choice",
        x_label=texts("uncertainty.axis.sd"),
        y_label=texts("uncertainty.axis.mean"),
        x_max=sd_max,
        y_max=top,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    end = sd_max if market_sd is None else market_sd
    plane.line(((0.0, line.risk_free), (end, line.mean(end))), plane.t("uncertainty.curve.line"))
    if market_sd is not None and market_sd < sd_max:
        plane.thin(((market_sd, line.mean(market_sd)), (sd_max, line.mean(sd_max))))
        plane.point(
            market_sd,
            line.mean(market_sd),
            xtext=plane.t("uncertainty.mark.market_sd"),
            name=plane.t("uncertainty.mark.market"),
        )
    for index, (investor, (sd, mean)) in enumerate(zip(investors, choices, strict=True), start=1):
        utility = investor.utility(mean, sd)
        plane.line(
            [
                (sd_max * i / STEPS, investor.indifference_mean(utility, sd_max * i / STEPS))
                for i in range(STEPS + 1)
            ],
            plane.t("uncertainty.curve.indifference_index", index=index),
            role="micro.curve.demand",
            at=0.9,
        )
        plane.point(
            sd,
            mean,
            xtext=plane.t("uncertainty.mark.choice_sd", index=index),
            ytext=plane.t("uncertainty.mark.choice_mean", index=index),
        )
    plane.ymark(line.risk_free, plane.t("uncertainty.mark.risk_free"))
    return plane.finish()


def mean_variance_frontier_canvas(
    frontier: TwoAssetFrontier,
    weights: tuple[float, float] = (-0.4, 1.4),
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """The frontier of portfolios of two assets in the standard-deviation-mean plane: the
    efficient part above the minimum-variance portfolio ``G`` is thick, the inefficient part
    thin and solid."""
    texts = Texts(resolve_theme(theme), labels)
    weight_g = frontier.minimum_variance_weight
    sd_g, mean_g = frontier.minimum_variance()
    upper_is_asset_1 = frontier.mean_1 > frontier.mean_2
    efficient = (
        (min(weight_g, weights[1]), weights[1])
        if upper_is_asset_1
        else (weights[0], max(weight_g, weights[0]))
    )
    inefficient = (weights[0], weight_g) if upper_is_asset_1 else (weight_g, weights[1])
    all_points = frontier.curve(*weights)
    plane = Plane(
        prefix="uncertainty.frontier",
        x_label=texts("uncertainty.axis.sd"),
        y_label=texts("uncertainty.axis.mean"),
        x_max=max(p[0] for p in all_points),
        y_max=max(p[1] for p in all_points),
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
        y_range=(min(p[1] for p in all_points) * 0.85, max(p[1] for p in all_points) * 1.05),
    )
    plane.thin(frontier.curve(*inefficient), plane.t("uncertainty.curve.inefficient"), at=0.8)
    plane.line(frontier.curve(*efficient), plane.t("uncertainty.curve.frontier"), at=0.95)
    plane.point(sd_g, mean_g, name=plane.t("uncertainty.mark.minimum_variance"))
    plane.point(frontier.sd_1, frontier.mean_1, name=plane.t("uncertainty.mark.asset", index=1))
    plane.point(frontier.sd_2, frontier.mean_2, name=plane.t("uncertainty.mark.asset", index=2))
    return plane.finish()
