"""mosaickit visual builders for choice under uncertainty."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import Canvas, CanvasGrid

from micro_viz.theme import PlotTheme
from micro_viz.uncertainty import (
    Gamble,
    IncomeUtility,
    MeanVarianceInvestor,
    RiskReturnLine,
    StateClaims,
    TwoAssetFrontier,
    UncertaintyError,
    UniformLottery,
    cdf_crossing,
)
from micro_viz.visuals.common import FIGURE_DPI, FIGURE_SIZE, MARGIN, Texts, resolve_theme
from micro_viz.visuals.plane import PANEL, Plane

STEPS = 60
"""Points per sampled curve."""


def _utility_plane(
    prefix: str,
    gamble: Gamble,
    utility: IncomeUtility,
    *,
    theme: PlotTheme | None,
    labels: Mapping[str, str] | None,
    title: str | None,
    margin: float,
    size: tuple[float, float],
    dpi: int,
) -> Plane:
    texts = Texts(resolve_theme(theme), labels)
    top = max(utility.utility(gamble.high), utility.utility(gamble.low)) * 1.05
    reach = gamble.high * 1.15
    plane = Plane(
        prefix=prefix,
        x_label=texts("uncertainty.axis.income"),
        y_label=texts("uncertainty.axis.utility"),
        x_max=reach,
        y_max=top,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    points = [(reach * i / STEPS, utility.utility(reach * i / STEPS)) for i in range(STEPS + 1)]
    plane.line(points, plane.t("uncertainty.curve.utility"), role="micro.curve.demand")
    return plane


def utility_of_income_canvas(
    gamble: Gamble,
    utilities: Sequence[IncomeUtility],
    *,
    titles: Sequence[str | None] | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = (4.2, 4.2),
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """One small panel per utility function: ``u(I)``, the chord between the two outcomes and the
    expected utility on it above expected income."""
    heading = list(titles) if titles is not None else [None] * len(utilities)
    cells = []
    for index, utility in enumerate(utilities, start=1):
        plane = _utility_plane(
            f"uncertainty.utility{index}",
            gamble,
            utility,
            theme=theme,
            labels=labels,
            title=heading[index - 1],
            margin=margin,
            size=size,
            dpi=dpi,
        )
        low, high = gamble.chord(utility)
        plane.thin((low, high), None)
        plane.dot(low)
        plane.dot(high)
        plane.xmark(gamble.low, plane.t("uncertainty.mark.low"))
        plane.xmark(gamble.high, plane.t("uncertainty.mark.high"))
        expected = gamble.expected_income
        plane.guide((expected, 0.0), (expected, gamble.expected_utility(utility)))
        plane.dot((expected, gamble.expected_utility(utility)))
        plane.xmark(expected, plane.t("uncertainty.mark.expected"))
        cells.append(plane.finish())
    return CanvasGrid([cells])


def risk_premium_canvas(
    gamble: Gamble,
    utility: IncomeUtility,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Concave ``u`` with the chord: the certainty equivalent ``CE`` has the utility ``EU`` of the
    gamble and the risk premium is the gap between ``E(I)`` and ``CE`` at that height."""
    plane = _utility_plane(
        "uncertainty.premium",
        gamble,
        utility,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    low, high = gamble.chord(utility)
    plane.thin((low, high), None)
    plane.dot(low)
    plane.dot(high)
    plane.xmark(gamble.low, plane.t("uncertainty.mark.low"))
    plane.xmark(gamble.high, plane.t("uncertainty.mark.high"))
    expected = gamble.expected_income
    level = gamble.expected_utility(utility)
    equivalent = gamble.certainty_equivalent(utility)
    plane.guide((expected, 0.0), (expected, level))
    plane.guide((0.0, level), (expected, level))
    plane.dot((expected, level))
    plane.dot((equivalent, level))
    plane.xmark(expected, plane.t("uncertainty.mark.expected"))
    plane.xmark(equivalent, plane.t("uncertainty.mark.equivalent"))
    plane.ymark(level, plane.t("uncertainty.mark.expected_utility"))
    plane.guide((equivalent, 0.0), (equivalent, level))
    plane.point(
        (equivalent + expected) / 2, level, name=plane.t("uncertainty.mark.premium"), marker=False
    )
    return plane.finish()


def risk_attitude_canvas(
    investors: Sequence[MeanVarianceInvestor],
    level: float,
    sd_max: float,
    *,
    titles: Sequence[str | None] | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """One panel of indifference curves per investor in the standard-deviation-income plane: the
    more risk averse, the steeper the curves."""
    heading = list(titles) if titles is not None else [None] * len(investors)
    texts = Texts(resolve_theme(theme), labels)
    top = max(inv.indifference_mean(level, sd_max) for inv in investors) * 1.05
    cells = []
    for index, investor in enumerate(investors, start=1):
        plane = Plane(
            prefix=f"uncertainty.attitude{index}",
            x_label=texts("uncertainty.axis.sd"),
            y_label=texts("uncertainty.axis.mean"),
            x_max=sd_max,
            y_max=top,
            theme=theme,
            labels=labels,
            title=heading[index - 1],
            margin=margin,
            size=size,
            dpi=dpi,
        )
        for rank, shift in enumerate((0.0, 0.25, 0.5), start=1):
            base = level * (1 + shift)
            plane.line(
                [
                    (sd_max * i / STEPS, investor.indifference_mean(base, sd_max * i / STEPS))
                    for i in range(STEPS + 1)
                ],
                plane.t("uncertainty.curve.indifference", index=rank),
                role="micro.curve.demand" if rank == 1 else "micro.curve.after",
            )
        cells.append(plane.finish())
    return CanvasGrid([cells])


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


__all__ = [
    "mean_variance_frontier_canvas",
    "risk_attitude_canvas",
    "risk_premium_canvas",
    "risk_return_choice_canvas",
    "state_claims_canvas",
    "stochastic_dominance_canvas",
    "utility_of_income_canvas",
]


def state_claims_canvas(
    claims: StateClaims,
    premium_rates: Sequence[float],
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """State-contingent claims: the 45-degree certainty line, the endowment ``E``, one budget line
    per premium rate (the first thick; a fair rate leads to full insurance on the certainty
    line, an unfair one to partial insurance) and the indifference curve through each choice."""
    texts = Texts(resolve_theme(theme), labels)
    reach = claims.good * 1.1
    plane = Plane(
        prefix="uncertainty.state",
        x_label=texts("uncertainty.axis.c1"),
        y_label=texts("uncertainty.axis.c2"),
        x_max=reach,
        y_max=reach,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    plane.line(((0.0, 0.0), (reach, reach)), plane.t("uncertainty.curve.certainty"), at=0.9)
    for index, rate in enumerate(premium_rates):
        end = min(reach, claims.wealth(rate) / (1 - rate))
        points = [
            (end * i / STEPS, claims.budget_c2(end * i / STEPS, rate)) for i in range(STEPS + 1)
        ]
        points = [p for p in points if 0 <= p[1] <= reach * 1.05]
        name = plane.t("uncertainty.curve.budget", index=index + 1)
        if index == 0:
            plane.line(points, name, role="micro.curve.marginal", at=0.0)
        else:
            plane.thin(points, name, at=0.0)
        c1, c2 = claims.choice(rate)
        level = claims.utility(c1, c2)
        curve = [
            (x, claims.indifference_c2(x, level))
            for x in (reach * (i + 1) / STEPS for i in range(STEPS))
        ]
        curve = [p for p in curve if p[1] == p[1] and p[1] <= reach * 1.05]
        plane.line(
            curve,
            plane.t("uncertainty.curve.indifference", index=index + 1),
            role="micro.curve.demand",
            at=1.0,
        )
        plane.point(c1, c2, name=plane.t("uncertainty.mark.choice", index=index + 1))
    plane.point(
        claims.good,
        claims.bad,
        xtext=plane.t("uncertainty.mark.good"),
        ytext=plane.t("uncertainty.mark.bad"),
        name=plane.t("uncertainty.mark.endowment"),
    )
    return plane.finish()


def stochastic_dominance_canvas(
    first: UniformLottery,
    second: UniformLottery,
    kind: str = "first",
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """The CDFs ``F_A`` and ``F_B`` of two lotteries. ``kind="first"`` shows ``F_A`` lying
    everywhere below ``F_B`` (A first-order dominates B); ``kind="second"`` shades the two
    areas enclosed where the CDFs cross, the larger one lying under the dominated lottery's
    CDF."""
    if kind not in {"first", "second"}:
        raise UncertaintyError("kind must be 'first' or 'second'.")
    texts = Texts(resolve_theme(theme), labels)
    low, high = min(first.low, second.low), max(first.high, second.high)
    plane = Plane(
        prefix=f"uncertainty.dominance.{kind}",
        x_label=texts("uncertainty.axis.income"),
        y_label=texts("uncertainty.axis.cdf"),
        x_max=high,
        y_max=1.0,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    xs = [low + (high - low) * i / STEPS for i in range(STEPS + 1)]
    if kind == "second":
        cross = cdf_crossing(first, second)
        if cross is not None:
            left = [x for x in xs if x <= cross] + [cross]
            right = [cross] + [x for x in xs if x >= cross]
            for xs_part, shade, key in (
                (left, "light", "uncertainty.region.a"),
                (right, "mid", "uncertainty.region.b"),
            ):
                upper = [(x, max(first.cdf(x), second.cdf(x))) for x in xs_part]
                lower = [(x, min(first.cdf(x), second.cdf(x))) for x in reversed(xs_part)]
                plane.area(tuple(upper + lower), plane.t(key), shade=shade)
    plane.line(
        [(x, first.cdf(x)) for x in xs],
        plane.t("uncertainty.curve.cdf", name="A"),
        role="micro.curve.demand",
        at=0.6,
    )
    plane.line(
        [(x, second.cdf(x)) for x in xs],
        plane.t("uncertainty.curve.cdf", name="B"),
        role="micro.curve.marginal",
        at=0.4,
    )
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
