"""Shared segment and monopsony plane helpers of the factor-market figures."""

from __future__ import annotations

from collections.abc import Mapping

from micro_viz.factors import (
    Monopsonist,
)
from micro_viz.theme import PlotTheme
from micro_viz.visuals.common import Point, Texts, resolve_theme
from micro_viz.visuals.plane import Plane


def segment(intercept: float, slope: float, x_max: float, y_max: float) -> tuple[Point, Point]:
    """The part of ``y = intercept + slope x`` inside ``[0, x_max] x [0, y_max]``."""
    low, high = 0.0, x_max
    if slope > 0:
        low = max(low, -intercept / slope)
        high = min(high, (y_max - intercept) / slope)
    elif slope < 0:
        low = max(low, (y_max - intercept) / slope)
        high = min(high, -intercept / slope)
    return (low, intercept + slope * low), (high, intercept + slope * high)


def _plane(
    prefix: str,
    kind: str,
    x_max: float,
    y_max: float,
    *,
    theme: PlotTheme | None,
    labels: Mapping[str, str] | None,
    title: str | None,
    margin: float,
    size: tuple[float, float],
    dpi: int,
    x_key: str | None = None,
) -> Plane:
    texts = Texts(resolve_theme(theme), labels)
    return Plane(
        prefix=prefix,
        x_label=texts(x_key or f"factors.{kind}.axis.x"),
        y_label=texts(f"factors.{kind}.axis.y"),
        x_max=x_max,
        y_max=y_max,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )


def _extent(model: Monopsonist) -> tuple[float, float]:
    return model.value.quantity_intercept, model.value.intercept


def _monopsony_plane(
    plane: Plane, model: Monopsonist, kind: str, *, competitive_marks: bool = True
) -> None:
    """Value, supply (AE) and ME curves with the monopsony and competitive points marked."""
    x_max, y_max = plane.x_max, plane.start.y_range[1]
    result = model.solve()
    s, v = model.supply, model.value
    plane.line(
        segment(v.intercept, -v.slope, x_max, y_max),
        plane.t(f"factors.{kind}.curve.value"),
        role="micro.curve.demand",
    )
    plane.line(segment(s.intercept, s.slope, x_max, y_max), plane.t(f"factors.{kind}.curve.ae"))
    plane.line(
        segment(s.intercept, 2 * s.slope, x_max, y_max),
        plane.t(f"factors.{kind}.curve.me"),
        role="micro.curve.marginal",
    )
    plane.point(
        result.quantity,
        result.wage,
        xtext=plane.t(f"factors.{kind}.mark.q_star"),
        ytext=plane.t(f"factors.{kind}.mark.p_star"),
    )
    plane.guide((result.quantity, result.wage), (result.quantity, result.marginal_value))
    plane.dot((result.quantity, result.marginal_value))
    if competitive_marks:
        plane.point(
            result.competitive_quantity,
            result.competitive_wage,
            xtext=plane.t(f"factors.{kind}.mark.q_c"),
            ytext=plane.t(f"factors.{kind}.mark.p_c"),
        )
