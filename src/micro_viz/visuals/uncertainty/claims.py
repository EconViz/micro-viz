"""State-claims and stochastic-dominance figures."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import Canvas

from micro_viz.theme import PlotTheme
from micro_viz.uncertainty import (
    StateClaims,
    UncertaintyError,
    UniformLottery,
    cdf_crossing,
)
from micro_viz.visuals.common import FIGURE_DPI, FIGURE_SIZE, MARGIN, Texts, resolve_theme
from micro_viz.visuals.plane import Plane
from micro_viz.visuals.uncertainty._base import STEPS


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
