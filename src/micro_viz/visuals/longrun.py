"""mosaickit visual builders for long-run costs and long-run competition."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import Canvas

from micro_viz.longrun import PlantFamily
from micro_viz.theme import PlotTheme
from micro_viz.visuals.common import FIGURE_DPI, FIGURE_SIZE, MARGIN
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


__all__ = ["lac_lmc_canvas", "plant_family_canvas"]
