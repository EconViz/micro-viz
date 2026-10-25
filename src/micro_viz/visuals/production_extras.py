"""mosaickit visual builders for learning, scope, technical progress and production frontiers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import Canvas

from micro_viz.production.extras import (
    LearningAverageCost,
    LearningCurve,
    ProductionFrontier,
    ProductTransformation,
    TechnologyShift,
    grid,
)
from micro_viz.theme import PlotTheme
from micro_viz.visuals.common import FIGURE_DPI, FIGURE_SIZE, MARGIN, Texts, resolve_theme
from micro_viz.visuals.plane import Plane

STEPS = 60
"""Points per sampled curve."""


def _plane(
    prefix: str,
    x_key: str,
    y_key: str,
    x_max: float,
    y_max: float,
    *,
    theme: PlotTheme | None,
    labels: Mapping[str, str] | None,
    title: str | None,
    margin: float,
    size: tuple[float, float],
    dpi: int,
) -> Plane:
    texts = Texts(resolve_theme(theme), labels)
    return Plane(
        prefix=prefix,
        x_label=texts(x_key),
        y_label=texts(y_key),
        x_max=x_max,
        y_max=y_max,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )


def learning_curve_canvas(
    learning: LearningCurve,
    cumulative_max: float,
    cumulative_min: float = 1.0,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Input per unit of output against cumulative output: it falls toward the floor ``A``."""
    points = learning.curve(cumulative_min, cumulative_max, STEPS)
    plane = _plane(
        "production.learning",
        "production.learning.axis.x",
        "production.learning.axis.y",
        cumulative_max,
        points[0][1],
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    plane.line(points, plane.t("production.learning.curve"), at=0.6)
    if learning.floor > 0:
        plane.guide((0.0, learning.floor), (cumulative_max, learning.floor))
        plane.ymark(learning.floor, plane.t("production.learning.floor"))
    return plane.finish()


def scale_vs_learning_canvas(
    cost: LearningAverageCost,
    learning: float,
    start: float,
    stop: float,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Two average-cost curves: moving from ``A`` to ``B`` along ``AC_1`` is a gain from scale;
    the vertical shift from ``B`` onto ``AC_2`` (``C``) is learning."""
    reach = 2 * cost.minimum_output
    top = cost.cost(0.0)
    plane = _plane(
        "production.scale",
        "production.scale.axis.x",
        "production.scale.axis.y",
        reach,
        top,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    for index, factor in ((1, 0.0), (2, learning)):
        points = [(q, cost.cost(q, factor)) for q in grid(0.0, reach, STEPS)]
        if index == 1:
            plane.line(
                points, plane.t("production.scale.ac", index=index), role="micro.curve.average"
            )
        else:
            plane.thin(points, plane.t("production.scale.ac", index=index))
    a = (start, cost.cost(start))
    b = (stop, cost.cost(stop))
    plane.point(
        *a, xtext=plane.t("production.scale.q", index=1), name=plane.t("production.scale.a")
    )
    plane.point(
        *b, xtext=plane.t("production.scale.q", index=2), name=plane.t("production.scale.b")
    )
    c = (stop, cost.cost(stop, learning))
    plane.point(*c, name=plane.t("production.scale.c"))
    plane.arrow(b, c)
    return plane.finish()


def product_transformation_canvas(
    curve: ProductTransformation,
    *,
    reference: bool = True,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """The product transformation curve ``PT``; ``reference`` adds the straight line joining the
    two maxima (no gains from joint production) so the outward bow reads as economies of scope."""
    plane = _plane(
        "production.transformation",
        "production.transformation.axis.x",
        "production.transformation.axis.y",
        curve.max_1,
        curve.max_2,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    plane.line(curve.curve(STEPS), plane.t("production.transformation.curve"), at=0.7)
    if reference:
        plane.thin(
            ((0.0, curve.max_2), (curve.max_1, 0.0)),
            plane.t("production.transformation.reference"),
            at=0.75,
        )
    plane.xmark(curve.max_1, plane.t("production.transformation.max", index=1))
    plane.ymark(curve.max_2, plane.t("production.transformation.max", index=2))
    return plane.finish()


def technology_shift_canvas(
    shift: TechnologyShift,
    input_max: float,
    arrow_input: float | None = None,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Total-product curves shifted upward by better technology; the base curve is thick, the
    others thin and solid. ``arrow_input`` draws a vertical arrow from the base curve."""
    top = shift.total_product(len(shift.factors) - 1, input_max)
    plane = _plane(
        "production.technology",
        "production.technology.axis.x",
        "production.technology.axis.y",
        input_max,
        top,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    for index in range(len(shift.factors)):
        points = [(x, shift.total_product(index, x)) for x in grid(0.0, input_max, STEPS)]
        name = plane.t("production.technology.tp", index=index + 1)
        if index == 0:
            plane.line(points, name, role="micro.curve.total")
        else:
            plane.thin(points, name)
    if arrow_input is not None:
        plane.arrow(
            (arrow_input, shift.total_product(0, arrow_input)),
            (arrow_input, shift.total_product(1, arrow_input)),
        )
    return plane.finish()


def production_frontier_canvas(
    frontier: ProductionFrontier,
    input_max: float,
    names: Sequence[str] | None = None,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Production frontier with diminishing returns; interior points lie strictly below it
    (inefficient use of inputs). ``names`` labels the points in order."""
    plane = _plane(
        "production.frontier",
        "production.frontier.axis.x",
        "production.frontier.axis.y",
        input_max,
        frontier.output(input_max),
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    plane.line(
        [(x, frontier.output(x)) for x in grid(0.0, input_max, STEPS) if x > 0],
        plane.t("production.frontier.curve"),
        role="micro.curve.total",
        at=0.8,
    )
    for index, (labor, output) in enumerate(frontier.points()):
        name = names[index] if names and index < len(names) else None
        plane.point(labor, output, name=name)
    return plane.finish()


__all__ = [
    "learning_curve_canvas",
    "product_transformation_canvas",
    "production_frontier_canvas",
    "scale_vs_learning_canvas",
    "technology_shift_canvas",
]
