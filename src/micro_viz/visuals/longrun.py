"""mosaickit visual builders for long-run costs and long-run competition."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import Canvas

from micro_viz.longrun import EnvelopeFigure, PlantFamily
from micro_viz.theme import PlotTheme
from micro_viz.visuals.common import FIGURE_DPI, FIGURE_SIZE, MARGIN, Texts, resolve_theme
from micro_viz.visuals.plane import Plane, sample

Sizes = tuple[float, ...]


def _plane(
    prefix: str,
    x_max: float,
    y_max: float,
    *,
    theme: PlotTheme | None,
    labels: Mapping[str, str] | None,
    title: str | None,
    margin: float,
    size: tuple[float, float],
    dpi: int,
    output: str = "Q",
) -> Plane:
    probe = Plane(
        prefix=prefix,
        x_label=output,
        y_label="p",
        x_max=x_max,
        y_max=y_max,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    return probe


def lac_lmc_canvas(
    family: PlantFamily,
    output_max: float,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    samples: int = 60,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """U-shaped LAC with LMC cutting it at its lowest point ``C_min`` (output ``Q_e``)."""
    low = output_max * 0.12
    lac = sample(family.lac, low, output_max, samples)
    lmc = sample(family.lmc, low, output_max, samples)
    top = max(y for _, y in lac + lmc)
    plane = _plane(
        "longrun",
        output_max,
        top,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    plane.line(lac, plane.t("longrun.lac"), role="micro.curve.average", at=0.0)
    plane.line(lmc, plane.t("longrun.lmc"))
    e = family.efficient_scale
    plane.point(
        e,
        family.minimum_cost,
        xtext=plane.t("longrun.mark.efficient", output="Q"),
        ytext=plane.t("longrun.mark.min_cost"),
    )
    return plane.finish()


def plant_family_canvas(
    family: PlantFamily,
    sizes: Sizes,
    output_max: float,
    *,
    smc_for: int | Sequence[int] | None = None,
    drops: bool = True,
    smc_reach: float = 0.3,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    samples: int = 60,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """SAC curves of the plants in ``sizes`` touching LAC, with LAC and LMC.

    Each SAC runs across the output axis up to the height of the plot, so neighbouring curves
    cross. ``smc_for`` (an index, or several, into ``sizes``) also draws those plants' SMC,
    which cross LMC at the tangency (a piece reaching ``smc_reach`` of the plant size either
    side of it); ``drops`` marks each tangency output ``Q_i`` on the axis.
    """
    low = output_max * 0.12
    chosen = (smc_for,) if isinstance(smc_for, int) else tuple(smc_for or ())
    lac = sample(family.lac, low, output_max, samples)
    lmc = sample(family.lmc, low, output_max, samples)
    ceiling = max(y for _, y in lac)
    plane = _plane(
        "longrun",
        output_max,
        ceiling * 1.5,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    plane.line(lac, plane.t("longrun.lac"), role="micro.curve.average", at=0.0)
    plane.line([p for p in lmc if p[1] <= ceiling * 1.45], plane.t("longrun.lmc"))
    for index, plant in enumerate(sizes, start=1):
        points = [
            (q, family.sac(plant, q))
            for q, _ in sample(lambda x: x, low, output_max, samples)
            if family.sac(plant, q) <= ceiling * 1.4
        ]
        plane.thin(points, plane.t("longrun.sac_index", index=index))
        touch = family.tangent_output(plant)
        plane.dot((touch, family.sac(plant, touch)))
        if drops:
            plane.guide((touch, 0.0), (touch, family.sac(plant, touch)))
            plane.xmark(touch, plane.t("longrun.mark.output_index", output="Q", index=index))
        if index - 1 in chosen:
            marginal = [
                (q, family.smc(plant, q))
                for q, _ in sample(
                    lambda x: x, touch * (1 - smc_reach), touch * (1 + smc_reach), samples
                )
                if family.smc(plant, q) <= ceiling * 1.45
            ]
            plane.thin(marginal, plane.t("longrun.smc_index", index=index), at=0.0)
    return plane.finish()


ENVELOPE_SIZE = (10.0, 4.2)
"""Default size in inches of the envelope figure: about 2.4 times wider than tall."""


def envelope_figure_canvas(
    figure: EnvelopeFigure,
    x_max: float,
    ceiling: float,
    *,
    smc_reach: float = 0.1,
    label_at: float = 0.9,
    lmc_start: float = 0.12,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = 0.04,
    samples: int = 120,
    size: tuple[float, float] = ENVELOPE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """LAC enveloping SAC1 to SAC3 as in a textbook figure of long-run cost.

    Wide axes ``0..x_max`` by ``0..ceiling``; LAC and LMC are the main curves, each SAC a
    thinner U, each SMC a short dashed piece reaching ``smc_reach * x_max`` either side of its
    SAC's lowest point (which it passes through), and LMC starts at ``lmc_start * x_max``.
    The SAC names sit at ``label_at`` along each curve
    (1 is its right end).
    Points mark the tangencies, the lowest points and A and B (the dashed levels
    ``figure.upper_cost`` and ``figure.left_cost``); dashed drops from the points at ``Q_0``
    to ``Q_3`` reach the output axis.
    """
    texts = Texts(resolve_theme(theme), labels)
    plane = Plane(
        prefix="longrun.figure",
        x_label="Q",
        y_label=texts("cost.axis.unit"),
        x_max=x_max,
        y_max=ceiling,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    plane.line(
        sample(figure.lac, 0.0, x_max, samples), plane.t("longrun.lac"), role="micro.curve.average"
    )
    plane.line(
        sample(figure.lmc, x_max * lmc_start, x_max, samples), plane.t("longrun.lmc"), at=0.0
    )
    for index in (1, 2, 3):
        plane.thin(
            sample(lambda q, i=index: figure.sac(i, q), 0.0, x_max, samples),
            plane.t("longrun.sac_index", index=index),
            at=label_at,
        )
    for index in (1, 2, 3):
        centre = figure.minimum_point(index)[0]
        plane.line(
            sample(
                lambda q, i=index: figure.smc(i, q),
                centre - smc_reach * x_max,
                centre + smc_reach * x_max,
                samples,
            ),
            plane.t("longrun.smc_index", index=index),
            role="micro.curve.fixed",
        )
    q0, q3 = figure.left_tangent, figure.right_tangent
    q1, q2 = figure.right_output, figure.minimum_output
    level_b, level_a = figure.left_cost, figure.upper_cost
    plane.guide((0.0, level_a), (q1, level_a))
    plane.guide((0.0, level_b), (q1, level_b))
    plane.ymark(level_a, plane.t("longrun.mark.level_a"))
    plane.ymark(level_b, plane.t("longrun.mark.level_b"))
    drops = (
        (q0, level_b),
        (q1, level_a),
        (q2, figure.minimum_cost),
        (q3, figure.lac(q3)),
    )
    for index, (x, y) in enumerate(drops):
        plane.guide((x, 0.0), (x, y))
        plane.xmark(x, plane.t("longrun.mark.output_index", output="Q", index=index))
    for point in (
        (q0, level_b),
        figure.minimum_point(1),
        (q1, level_b),
        (q1, level_a),
        (q2, figure.minimum_cost),
        figure.minimum_point(3),
        (q3, figure.lac(q3)),
    ):
        plane.dot(point)
    plane.point(q1, level_a, name=plane.t("longrun.point.a"), marker=False)
    plane.point(q1, level_b, name=plane.t("longrun.point.b"), marker=False)
    return plane.finish()


__all__ = ["envelope_figure_canvas", "lac_lmc_canvas", "plant_family_canvas"]
