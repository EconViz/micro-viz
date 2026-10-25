"""mosaickit visual builders for duopoly models."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import Canvas

from micro_viz.oligopoly import (
    DifferentiatedDuopoly,
    Duopoly,
    bertrand,
    collusive_total,
    competitive_total,
    cournot,
    split,
    stackelberg,
)
from micro_viz.theme import PlotTheme
from micro_viz.visuals.common import FIGURE_DPI, FIGURE_SIZE, MARGIN, Texts, resolve_theme
from micro_viz.visuals.plane import Plane, linear

STEPS = 40
"""Points per sampled reaction curve."""


def residual_demand_canvas(
    duopoly: Duopoly,
    guesses: Sequence[float],
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Firm 1's residual demand ``D1(q2)`` and ``MR1(q2)`` for each guess of the rival's output,
    with its marginal cost. Each guess shifts both curves left by ``q2``."""
    plane = Plane(
        prefix="oligopoly.residual",
        x_label=_text(theme, labels, "oligopoly.axis.q1"),
        y_label="p",
        x_max=duopoly.intercept / duopoly.slope,
        y_max=duopoly.intercept,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    for guess in guesses:
        d_intercept, d_slope = duopoly.residual_demand(guess)
        m_intercept, m_slope = duopoly.residual_marginal_revenue(guess)
        d_reach = d_intercept / d_slope
        plane.line(
            linear(d_intercept, -d_slope, d_reach),
            plane.t("oligopoly.curve.demand", guess=guess),
            role="micro.curve.demand",
        )
        plane.thin(
            linear(m_intercept, -m_slope, m_intercept / m_slope),
            plane.t("oligopoly.curve.mr", guess=guess),
        )
    plane.line(
        ((0.0, duopoly.cost_1), (plane.x_max, duopoly.cost_1)), plane.t("oligopoly.curve.mc")
    )
    return plane.finish()


def reaction_curves_canvas(
    duopoly: Duopoly,
    *,
    competitive: bool = False,
    collusive: bool = False,
    leader: int | None = None,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Reaction curves ``R1`` and ``R2`` in ``(Q1, Q2)`` space meeting at the Cournot-Nash point
    ``N``. ``competitive`` and ``collusive`` add the constant-total-output lines and their
    symmetric points ``C`` and ``M``; ``leader`` adds the Stackelberg point ``S``."""
    reach = max(duopoly.reach_1, duopoly.reach_2)
    plane = Plane(
        prefix="oligopoly.reaction",
        x_label=_text(theme, labels, "oligopoly.axis.q1"),
        y_label=_text(theme, labels, "oligopoly.axis.q2"),
        x_max=reach,
        y_max=reach,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    # R1: q1 = BR1(q2); R2: q2 = BR2(q1).
    top_2 = (duopoly.intercept - duopoly.cost_1) / duopoly.slope
    r1 = [(duopoly.best_response_1(top_2 * i / STEPS), top_2 * i / STEPS) for i in range(STEPS + 1)]
    top_1 = (duopoly.intercept - duopoly.cost_2) / duopoly.slope
    r2 = [(top_1 * i / STEPS, duopoly.best_response_2(top_1 * i / STEPS)) for i in range(STEPS + 1)]
    plane.line(r1, plane.t("oligopoly.curve.r1"), role="micro.curve.demand")
    plane.line(r2, plane.t("oligopoly.curve.r2"), role="micro.curve.marginal")
    nash = cournot(duopoly)
    plane.point(
        nash.q1,
        nash.q2,
        xtext=plane.t("oligopoly.mark.q1", point="N"),
        ytext=plane.t("oligopoly.mark.q2", point="N"),
        name=plane.t("oligopoly.point.cournot"),
    )
    if competitive:
        total = competitive_total(duopoly)
        plane.thin(((total, 0.0), (0.0, total)))
        q1, q2 = split(total)
        plane.point(q1, q2, name=plane.t("oligopoly.point.competitive"))
    if collusive:
        total = collusive_total(duopoly)
        plane.thin(((total, 0.0), (0.0, total)), plane.t("oligopoly.curve.collusion"), at=0.65)
        q1, q2 = split(total)
        plane.point(q1, q2, name=plane.t("oligopoly.point.collusive"))
    if leader is not None:
        lead = stackelberg(duopoly, leader)
        plane.point(lead.q1, lead.q2, name=plane.t("oligopoly.point.stackelberg"))
    return plane.finish()


def price_reaction_canvas(
    duopoly: DifferentiatedDuopoly,
    *,
    collusive: bool = True,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Upward-sloping price reaction curves ``R1`` and ``R2`` in ``(p1, p2)`` space, the Nash
    prices ``N`` and (optionally) the joint-profit-maximising prices ``M``."""
    result = bertrand(duopoly)
    top = max(result.nash[0], result.nash[1], result.collusive[0], result.collusive[1]) * 1.25
    plane = Plane(
        prefix="oligopoly.price",
        x_label=_text(theme, labels, "oligopoly.axis.p1"),
        y_label=_text(theme, labels, "oligopoly.axis.p2"),
        x_max=top,
        y_max=top,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    # R1 gives p1 for each p2 (a curve with p2 on the vertical axis); R2 gives p2 for each p1.
    r1 = [(duopoly.best_price_1(top * i / STEPS), top * i / STEPS) for i in range(STEPS + 1)]
    r2 = [(top * i / STEPS, duopoly.best_price_2(top * i / STEPS)) for i in range(STEPS + 1)]
    plane.line(r1, plane.t("oligopoly.curve.r1"), role="micro.curve.demand", at=0.9)
    plane.line(r2, plane.t("oligopoly.curve.r2"), role="micro.curve.marginal")
    plane.point(
        *result.nash,
        xtext=plane.t("oligopoly.mark.p1", point="N"),
        ytext=plane.t("oligopoly.mark.p2", point="N"),
        name=plane.t("oligopoly.point.cournot"),
    )
    if collusive:
        plane.point(
            *result.collusive,
            xtext=plane.t("oligopoly.mark.p1", point="M"),
            ytext=plane.t("oligopoly.mark.p2", point="M"),
            name=plane.t("oligopoly.point.collusive"),
        )
    return plane.finish()


def _text(theme: PlotTheme | None, labels: Mapping[str, str] | None, key: str) -> str:
    return Texts(resolve_theme(theme), labels)(key)


__all__ = ["price_reaction_canvas", "reaction_curves_canvas", "residual_demand_canvas"]
