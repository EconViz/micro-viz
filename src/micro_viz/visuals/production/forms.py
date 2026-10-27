"""Aligned TP/AP/MP panels for alternative short-run production forms."""

from __future__ import annotations

from collections.abc import Mapping

from mosaickit import (
    CanvasGrid,
    GridLink,
    GridSpacing,
    PointLabelLayer,
    TextLayer,
)

from micro_viz.production import (
    CapacityConstrainedProductionFunction,
    QuadraticProductionFunction,
)
from micro_viz.theme import PlotTheme
from micro_viz.visuals.common import (
    FIGURE_DPI,
    MARGIN,
    Texts,
    resolve_theme,
)
from micro_viz.visuals.plane import PANEL, Plane, sample

SAMPLES = 120
GRID_SPACING = GridSpacing(row_gap=0.18, outer=0.04)
MARK_GAP_PT = 4.0


def _grid(upper: Plane, lower: Plane, link: GridLink) -> CanvasGrid:
    return CanvasGrid(
        [[upper.finish()], [lower.finish()]],
        links=(link,),
        spacing=GRID_SPACING,
    )


def _zero_axis_mark(plane: Plane, value: float, text: str) -> None:
    """Write an input mark directly under the horizontal axis at ``y = 0``."""
    plane.start.layers.append(
        TextLayer(
            (value, 0.0),
            text,
            id=f"micro.{plane.prefix}.mark.input",
            role="axes",
            anchor="top",
            offset=(0.0, -MARK_GAP_PT),
            math=True,
            z_index=8,
        )
    )


def quadratic_production_grid(
    function: QuadraticProductionFunction,
    *,
    titles: tuple[str | None, str | None] = (None, None),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    x_max: float | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """A concave quadratic TP panel above its linear AP and MP panel."""
    selected = resolve_theme(theme)
    texts = Texts(selected, labels)
    end = x_max if x_max is not None else function.zero_output_input
    maximum_input = function.total_product_max_input
    maximum_output = function.total_product(maximum_input)
    upper = Plane(
        prefix="production.quadratic.total",
        x_label=texts("production.forms.axis.input"),
        y_label=texts("production.forms.axis.total"),
        x_max=end,
        y_max=maximum_output,
        title=titles[0],
        theme=selected,
        labels=labels,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    upper.line(
        sample(function.total_product, 0.0, end, SAMPLES),
        texts("production.forms.tp"),
        role="micro.curve.total",
        at=0.9,
    )
    upper.guide((maximum_input, 0.0), (maximum_input, maximum_output))
    upper.point(maximum_input, maximum_output, name=texts("production.forms.point.a"))

    lower = Plane(
        prefix="production.quadratic.products",
        x_label=texts("production.forms.axis.input"),
        y_label=texts("production.forms.axis.products"),
        x_max=end,
        y_max=function.productivity,
        y_range=(-function.productivity * 1.1, function.productivity * 1.1),
        title=titles[1],
        theme=selected,
        labels=labels,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    average = [(0.0, function.productivity)] + sample(
        lambda value: function.average_product(value) or 0.0,
        end / SAMPLES,
        end,
        SAMPLES - 1,
    )
    lower.line(
        average,
        texts("production.forms.ap"),
        role="micro.curve.average",
        at=0.76,
    )
    lower.line(
        sample(function.marginal_product, 0.0, end, SAMPLES),
        texts("production.forms.mp"),
        role="micro.curve.marginal",
        at=0.78,
    )
    lower.dot((0.0, function.productivity))
    lower.point(maximum_input, 0.0)
    _zero_axis_mark(lower, maximum_input, texts("production.forms.mark.input"))
    return _grid(
        upper,
        lower,
        GridLink(
            0,
            (maximum_input, maximum_output),
            1,
            (maximum_input, 0.0),
            role="micro.guide",
        ),
    )


def capacity_production_grid(
    function: CapacityConstrainedProductionFunction,
    *,
    titles: tuple[str | None, str | None] = (None, None),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    x_max: float | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """A capacity-constrained TP panel above its piecewise AP and MP panel."""
    selected = resolve_theme(theme)
    texts = Texts(selected, labels)
    capacity_input = function.capacity_input
    end = x_max if x_max is not None else capacity_input * 2.2
    upper = Plane(
        prefix="production.capacity.total",
        x_label=texts("production.forms.axis.input"),
        y_label=texts("production.forms.axis.total"),
        x_max=end,
        y_max=function.capacity,
        title=titles[0],
        theme=selected,
        labels=labels,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    upper.line(
        ((0.0, 0.0), (capacity_input, function.capacity), (end, function.capacity)),
        texts("production.forms.tp"),
        role="micro.curve.total",
        at=0.92,
    )
    upper.guide((capacity_input, 0.0), (capacity_input, function.capacity))
    upper.point(
        capacity_input,
        function.capacity,
        ytext=texts("production.forms.mark.output"),
        name=texts("production.forms.point.a"),
    )

    lower = Plane(
        prefix="production.capacity.products",
        x_label=texts("production.forms.axis.input"),
        y_label=texts("production.forms.axis.products"),
        x_max=end,
        y_max=function.productivity,
        title=titles[1],
        theme=selected,
        labels=labels,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    average = [(0.0, function.productivity), (capacity_input, function.productivity)]
    average.extend(
        sample(
            lambda value: function.average_product(value) or 0.0,
            capacity_input,
            end,
            SAMPLES,
        )[1:]
    )
    lower.line(
        average,
        texts("production.forms.ap"),
        role="micro.curve.average",
        at=0.72,
    )
    lower.line(
        (
            (0.0, function.productivity),
            (capacity_input, function.productivity),
            (capacity_input, 0.0),
            (end, 0.0),
        ),
        role="micro.curve.marginal",
    )
    lower.start.layers.append(
        PointLabelLayer(
            (capacity_input + 0.72 * (end - capacity_input), 0.0),
            texts("production.forms.mp"),
            id="micro.production.capacity.products.mp.label",
            role="micro.curve.marginal",
            z_index=7,
        )
    )
    lower.dot((capacity_input, function.productivity))
    lower.point(capacity_input, 0.0)
    _zero_axis_mark(lower, capacity_input, texts("production.forms.mark.input"))
    return _grid(
        upper,
        lower,
        GridLink(
            0,
            (capacity_input, function.capacity),
            1,
            (capacity_input, 0.0),
            role="micro.guide",
        ),
    )


__all__ = [
    "capacity_production_grid",
    "quadratic_production_grid",
]
