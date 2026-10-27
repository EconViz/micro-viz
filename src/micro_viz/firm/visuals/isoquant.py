"""mosaickit visual builders for isoquants, MRTS and returns to scale."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import Canvas, CanvasGrid, PointLabelLayer

from micro_viz.core.theme import PlotTheme
from micro_viz.firm.isoquant import FixedProportions, Technology, ray_points
from micro_viz.firm.visuals.competition import PANEL_SIZE, _finish, _Start, _start
from micro_viz.visuals.common import (
    FIGURE_DPI,
    FIGURE_SIZE,
    MARGIN,
    Point,
    axis_mark,
    curve,
    curve_name,
    dot,
    drop_line,
    guide,
    pad_range,
)

_PREFIX = "micro.isoquant"
_Y_TEXT = "isoquant.axis.capital"


def _begin(
    tech: Technology,
    bounds: Point,
    *,
    theme: PlotTheme | None,
    labels: Mapping[str, str] | None,
    x_label: str | None,
    y_label: str | None,
    margin: float,
    title: str | None,
    size: tuple[float, float],
    dpi: int,
) -> _Start:
    return _start(
        theme=theme,
        labels=labels,
        x_symbol=tech.labor_symbol,
        x_label=x_label,
        y_label=y_label if y_label is not None else tech.capital_symbol,
        y_text_id=_Y_TEXT,
        x_max=bounds[0] * (1 + margin),
        y_range=pad_range(0.0, bounds[1], margin),
        title=title,
        size=size,
        dpi=dpi,
    )


def _isoquants(
    start: _Start,
    tech: Technology,
    outputs: Sequence[float],
    bounds: Point,
    *,
    names: Sequence[str] | None = None,
    samples: int = 121,
    along: float = 1.0,
    named: bool = True,
) -> None:
    for index, output in enumerate(outputs, start=1):
        points = tech.isoquant(output, bounds, samples)
        if len(points) < 2:
            continue
        path = curve(
            points, layer_id=f"{_PREFIX}.q.{index}", role="micro.curve.marginal", model=tech
        )
        text = names[index - 1] if names is not None else start.texts("isoquant.curve", index=index)
        start.layers.append(path)
        if named:
            start.layers.append(curve_name(path, text, at=along))


def isoquant_map_canvas(
    tech: Technology,
    outputs: Sequence[float],
    bounds: Point,
    *,
    ray: bool = False,
    level_names: Sequence[str] | None = None,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    x_label: str | None = None,
    y_label: str | None = None,
    margin: float = MARGIN,
    samples: int = 121,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Isoquants of the given ``outputs`` inside the box ``bounds = (L_max, K_max)``.

    The curves are named ``Q_1, Q_2, ...`` (or ``level_names``). With ``ray`` and a
    fixed-proportions technology a dashed ray from the origin passes through the kinks.
    """
    start = _begin(
        tech,
        bounds,
        theme=theme,
        labels=labels,
        x_label=x_label,
        y_label=y_label,
        margin=margin,
        title=title,
        size=size,
        dpi=dpi,
    )
    _isoquants(start, tech, outputs, bounds, names=level_names, samples=samples)
    if ray and isinstance(tech, FixedProportions):
        begin, end = ray_points(tech.ray_slope, bounds)
        start.layers.append(guide(begin, end, layer_id=f"{_PREFIX}.ray"))
        for index, output in enumerate(outputs, start=1):
            corner = tech.corner(output)
            if corner[0] <= bounds[0] and corner[1] <= bounds[1]:
                start.layers.append(dot(corner, layer_id=f"{_PREFIX}.kink.{index}"))
    return _finish(start)


def mrts_steps_canvas(
    tech: Technology,
    output: float,
    labors: Sequence[float],
    bounds: Point,
    *,
    delta_labels: bool = False,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    x_label: str | None = None,
    y_label: str | None = None,
    margin: float = MARGIN,
    samples: int = 121,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """One isoquant with points at the given ``labors``; between neighbours the chord and the
    right triangle of ``ΔK`` and ``ΔL`` whose ratio is the (average) MRTS, flatter step by step."""
    start = _begin(
        tech,
        bounds,
        theme=theme,
        labels=labels,
        x_label=x_label,
        y_label=y_label,
        margin=margin,
        title=title,
        size=size,
        dpi=dpi,
    )
    _isoquants(start, tech, (output,), bounds, samples=samples, named=False)
    points: list[Point] = []
    for labor in labors:
        capital = tech.capital_for(output, labor)
        if capital is None:
            raise ValueError("every labor must lie on the isoquant")
        points.append((labor, capital))
    names = start.texts("isoquant.point_names")
    for index, point in enumerate(points):
        start.layers.append(dot(point, layer_id=f"{_PREFIX}.point.{index + 1}"))
        start.layers.append(
            PointLabelLayer(
                point, names[index], id=f"{_PREFIX}.point.{index + 1}.label", role="micro.point"
            )
        )
        start.layers.append(
            drop_line(point[0], point[1], layer_id=f"{_PREFIX}.guide.labor.{index + 1}")
        )
        start.layers.append(
            axis_mark(
                "x",
                point[0],
                start.texts("isoquant.mark.labor", symbol=tech.labor_symbol, index=index + 1),
                layer_id=f"{_PREFIX}.mark.labor.{index + 1}",
            )
        )
        start.layers.append(
            guide((0.0, point[1]), point, layer_id=f"{_PREFIX}.guide.capital.{index + 1}")
        )
        start.layers.append(
            axis_mark(
                "y",
                point[1],
                start.texts("isoquant.mark.capital", symbol=tech.capital_symbol, index=index + 1),
                layer_id=f"{_PREFIX}.mark.capital.{index + 1}",
            )
        )
    for index, (first, second) in enumerate(zip(points, points[1:], strict=False), start=1):
        corner = (first[0], second[1])
        start.layers.append(
            curve(
                (first, second),
                layer_id=f"{_PREFIX}.chord.{index}",
                role="micro.curve.after",
            )
        )
        start.layers.append(guide(first, corner, layer_id=f"{_PREFIX}.leg.capital.{index}"))
        start.layers.append(guide(corner, second, layer_id=f"{_PREFIX}.leg.labor.{index}"))
        if delta_labels:
            start.layers.append(
                PointLabelLayer(
                    ((first[0] + corner[0]) / 2, (first[1] + corner[1]) / 2),
                    start.texts("isoquant.delta_capital", symbol=tech.capital_symbol),
                    id=f"{_PREFIX}.delta.capital.{index}",
                    role="micro.annotation",
                )
            )
            start.layers.append(
                PointLabelLayer(
                    ((corner[0] + second[0]) / 2, (corner[1] + second[1]) / 2),
                    start.texts("isoquant.delta_labor", symbol=tech.labor_symbol),
                    id=f"{_PREFIX}.delta.labor.{index}",
                    role="micro.annotation",
                )
            )
    return _finish(start)


def returns_to_scale_grid(
    technologies: Sequence[Technology],
    outputs: Sequence[Sequence[float]],
    bounds: Point,
    direction: Point,
    *,
    titles: Sequence[str | None] | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL_SIZE,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """One panel per technology: isoquants of the listed outputs cut by a ray with direction
    ``(L, K)``; they are evenly spaced under constant returns and closer under increasing."""
    cells: list[Canvas] = []
    heading = list(titles) if titles is not None else [None] * len(technologies)
    slope = direction[1] / direction[0]
    for tech, levels, name in zip(technologies, outputs, heading, strict=True):
        start = _begin(
            tech,
            bounds,
            theme=theme,
            labels=labels,
            x_label=None,
            y_label=None,
            margin=margin,
            title=name,
            size=size,
            dpi=dpi,
        )
        begin, end = ray_points(slope, bounds)
        start.layers.append(guide(begin, end, layer_id=f"{_PREFIX}.ray"))
        _isoquants(
            start,
            tech,
            levels,
            bounds,
            names=[start.texts("isoquant.level", value=f"{value:g}") for value in levels],
            along=0.0,
        )
        for index, output in enumerate(levels, start=1):
            factor = tech.scale_for(output, direction[0], direction[1])
            start.layers.append(
                dot(
                    (direction[0] * factor, direction[1] * factor),
                    layer_id=f"{_PREFIX}.cut.{index}",
                )
            )
        cells.append(_finish(start))
    return CanvasGrid([cells])


__all__ = ["isoquant_map_canvas", "mrts_steps_canvas", "returns_to_scale_grid"]
