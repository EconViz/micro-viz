"""The aligned labor/capital view of the rational production region."""

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

from micro_viz.production import ShortRunProductionFunction
from micro_viz.theme import PlotTheme
from micro_viz.visuals.axes import axes_layers
from micro_viz.visuals.common import (
    FIGURE_DPI,
    Texts,
    curve,
    curve_name,
    dot,
    guide,
    new_canvas,
    nudge_labels,
    resolve_theme,
)
from micro_viz.visuals.plane import PANEL

SAMPLES = 120


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
    """Labor products above reversed capital products, sharing rational-region bounds."""
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
    stages = ("increasing", "diminishing", "negative")
    stage_positions = (l_ap / 2, (l_ap + l_mp_zero) / 2, (l_mp_zero + right) / 2)
    for index, (kind, x) in enumerate(zip(stages, stage_positions, strict=True), start=1):
        top_layers.append(
            TextLayer(
                (x, top_range[1]),
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


__all__ = ["rational_production_region_grid"]
