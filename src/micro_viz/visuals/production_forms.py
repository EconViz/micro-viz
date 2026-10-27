"""Aligned TP/AP/MP panels for alternative short-run production forms."""

from __future__ import annotations

from collections.abc import Mapping

from mosaickit import (
    ArrowPlacement,
    ArrowStyle,
    CanvasGrid,
    GridLink,
    GridSpacing,
    PathLayer,
    PointLabelLayer,
    Stroke,
    TextLayer,
)

from micro_viz.production import (
    CapacityConstrainedProductionFunction,
    QuadraticProductionFunction,
    ShortRunProductionFunction,
)
from micro_viz.theme import PlotTheme
from micro_viz.visuals.axes import axes_layers
from micro_viz.visuals.common import (
    FIGURE_DPI,
    MARGIN,
    Texts,
    curve,
    curve_name,
    dot,
    guide,
    new_canvas,
    nudge_labels,
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


def _products(
    function: ShortRunProductionFunction, end: float
) -> tuple[tuple[tuple[float, float], ...], tuple[tuple[float, float], ...]]:
    xs = [end * index / SAMPLES for index in range(SAMPLES + 1)]
    average = tuple((value, function.average_product(value) or function.linear) for value in xs)
    marginal = tuple((value, function.marginal_product(value)) for value in xs)
    return average, marginal


def _reversed_axes(
    right: float,
    y_range: tuple[float, float],
    *,
    x_label: str,
    y_label: str,
) -> tuple[PathLayer | TextLayer, ...]:
    low, high = y_range
    arrow = Stroke(arrow=ArrowStyle.TRIANGLE)
    return (
        PathLayer(
            ((right, 0.0), (0.0, 0.0)),
            id="axes.x",
            role="axes",
            stroke=arrow,
            arrow_placement=ArrowPlacement.END,
            clip=False,
        ),
        PathLayer(
            ((right, min(0.0, low)), (right, high)),
            id="axes.y",
            role="axes",
            stroke=arrow,
            arrow_placement=ArrowPlacement.END,
            clip=False,
        ),
        TextLayer(
            (0.0, 0.0),
            x_label,
            id="axes.x.label",
            role="axes",
            offset=(-6.0, 0.0),
            anchor="right",
            math=True,
        ),
        TextLayer(
            (right, high),
            y_label,
            id="axes.y.label",
            role="axes",
            offset=(0.0, 6.0),
            anchor="bottom",
            math=True,
        ),
        TextLayer(
            (right, 0.0),
            "0",
            id="axes.origin.label",
            role="axes",
            offset=(7.0, -7.0),
            anchor="left",
        ),
    )


def rational_production_region_grid(
    labor: ShortRunProductionFunction,
    capital: ShortRunProductionFunction,
    *,
    labor_end: float | None = None,
    capital_end: float | None = None,
    titles: tuple[str | None, str | None] = (None, None),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    size: tuple[float, float] = PANEL,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """Labor products above reversed capital products, sharing the rational-region bounds.

    Labor increases from left to right. Capital increases from right to left, so the end of
    stage I for labor aligns with the end of stage II for capital and vice versa. The interval
    between the two dashed lines is therefore the rational production region for both inputs.
    """
    selected = resolve_theme(theme)
    texts = Texts(selected, labels)
    l_ap = labor.average_product_max_input
    l_mp_zero = labor.total_product_max_input
    k_ap = capital.average_product_max_input
    k_mp_zero = capital.total_product_max_input
    if not l_ap < l_mp_zero or not k_ap < k_mp_zero:
        raise ValueError("AP maximum must precede the TP maximum for both inputs.")
    scale = (l_mp_zero - l_ap) / (k_mp_zero - k_ap)
    right = l_mp_zero + scale * k_ap
    labor_stop = labor_end if labor_end is not None else labor.total_product_max_input * 1.16
    capital_stop = (
        capital_end if capital_end is not None else capital.total_product_max_input * 1.16
    )
    if labor_stop <= l_mp_zero or capital_stop <= k_mp_zero:
        raise ValueError("Each input range must extend past its MP = 0 point.")

    labor_average, labor_marginal = _products(labor, labor_stop)
    top_values = [value for _, value in (*labor_average, *labor_marginal)]
    top_range = (min(0.0, min(top_values)) * 1.1, max(top_values) * 1.18)
    top = new_canvas(
        selected,
        x_range=(0.0, right),
        y_range=top_range,
        x_label=texts("production.rational.axis.labor"),
        y_label=texts("production.rational.axis.labor_products"),
        title=titles[0],
        size=size,
        dpi=dpi,
    )
    top_layers = list(
        axes_layers(
            (0.0, right),
            top_range,
            x_label=texts("production.rational.axis.labor"),
            y_label=texts("production.rational.axis.labor_products"),
        )
    )
    top_ap = curve(
        labor_average,
        layer_id="micro.production.rational.labor.ap",
        role="micro.curve.average",
        model=labor,
    )
    top_mp = curve(
        labor_marginal,
        layer_id="micro.production.rational.labor.mp",
        role="micro.curve.marginal",
        model=labor,
    )
    top_layers.extend(
        (
            top_ap,
            curve_name(top_ap, texts("production.rational.ap_l"), at=0.86),
            top_mp,
            curve_name(top_mp, texts("production.rational.mp_l"), at=0.96),
        )
    )
    top_points = (
        (l_ap, labor.marginal_product(l_ap)),
        (l_mp_zero, 0.0),
    )
    for index, point in enumerate(top_points, start=1):
        top_layers.append(
            guide(
                (point[0], top_range[0]),
                (point[0], top_range[1]),
                layer_id=f"micro.production.rational.labor.boundary.{index}",
            )
        )
        top_layers.append(dot(point, layer_id=f"micro.production.rational.labor.point.{index}"))
    stage_y = top_range[1]
    stages = ("increasing", "diminishing", "negative")
    stage_positions = (l_ap / 2, (l_ap + l_mp_zero) / 2, (l_mp_zero + right) / 2)
    for index, (kind, x) in enumerate(zip(stages, stage_positions, strict=True), start=1):
        top_layers.append(
            TextLayer(
                (x, stage_y),
                texts(f"production.region.{kind}.short"),
                id=f"micro.production.rational.stage.{index}",
                role="micro.annotation",
                anchor="bottom",
                offset=(0.0, 4.0),
            )
        )
    top.extend(nudge_labels(top_layers, selected.label_nudges))

    capital_average, capital_marginal = _products(capital, capital_stop)

    def reverse(points: tuple[tuple[float, float], ...]) -> tuple[tuple[float, float], ...]:
        return tuple((right - scale * value, product) for value, product in points)

    bottom_average = reverse(capital_average)
    bottom_marginal = reverse(capital_marginal)
    bottom_values = [value for _, value in (*bottom_average, *bottom_marginal)]
    bottom_range = (min(0.0, min(bottom_values)) * 1.1, max(bottom_values) * 1.18)
    bottom = new_canvas(
        selected,
        x_range=(0.0, right),
        y_range=bottom_range,
        x_label=texts("production.rational.axis.capital"),
        y_label=texts("production.rational.axis.capital_products"),
        title=titles[1],
        size=size,
        dpi=dpi,
    )
    bottom_layers: list[PathLayer | PointLabelLayer | TextLayer] = list(
        _reversed_axes(
            right,
            bottom_range,
            x_label=texts("production.rational.axis.capital"),
            y_label=texts("production.rational.axis.capital_products"),
        )
    )
    bottom_ap = curve(
        bottom_average,
        layer_id="micro.production.rational.capital.ap",
        role="micro.curve.average",
        model=capital,
    )
    bottom_mp = curve(
        bottom_marginal,
        layer_id="micro.production.rational.capital.mp",
        role="micro.curve.marginal",
        model=capital,
    )
    bottom_layers.extend((bottom_ap, bottom_mp))
    bottom_layers.extend(
        (
            PointLabelLayer(
                bottom_average[-1],
                texts("production.rational.ap_k"),
                id="micro.production.rational.capital.ap.label",
                role="micro.curve.average",
                z_index=7,
            ),
            PointLabelLayer(
                bottom_marginal[-1],
                texts("production.rational.mp_k"),
                id="micro.production.rational.capital.mp.label",
                role="micro.curve.marginal",
                z_index=7,
            ),
        )
    )
    bottom_points = (
        (l_mp_zero, capital.marginal_product(k_ap)),
        (l_ap, 0.0),
    )
    for index, point in enumerate(bottom_points, start=1):
        bottom_layers.append(
            guide(
                (point[0], bottom_range[0]),
                (point[0], bottom_range[1]),
                layer_id=f"micro.production.rational.capital.boundary.{index}",
            )
        )
        bottom_layers.append(
            dot(point, layer_id=f"micro.production.rational.capital.point.{index}")
        )
    bottom.extend(nudge_labels(bottom_layers, selected.label_nudges))
    return CanvasGrid(
        [[top], [bottom]],
        links=(
            GridLink(0, (l_ap, top_range[0]), 1, (l_ap, bottom_range[1]), role="micro.guide"),
            GridLink(
                0,
                (l_mp_zero, top_range[0]),
                1,
                (l_mp_zero, bottom_range[1]),
                role="micro.guide",
            ),
        ),
        spacing=GridSpacing(row_gap=0.08, outer=0.04),
    )


__all__ = [
    "capacity_production_grid",
    "quadratic_production_grid",
    "rational_production_region_grid",
]
