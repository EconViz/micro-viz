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
    "risk_attitude_canvas",
    "risk_premium_canvas",
    "risk_return_choice_canvas",
    "utility_of_income_canvas",
]
