"""MosaicKit visual builders for short-run production analysis."""

from __future__ import annotations

from collections.abc import Iterable

from mosaickit import (
    ArrowPlacement,
    AxisSpec,
    Canvas,
    CanvasSpec,
    FillLayer,
    PathLayer,
    TextLayer,
    build_axes,
)

from micro_viz.config import default_theme
from micro_viz.production import ProductionAnalysis
from micro_viz.theme import PlotTheme

Point = tuple[float, float]


def _y_range(values: Iterable[float]) -> tuple[float, float]:
    values = tuple(values)
    low = min(0.0, *values)
    high = max(0.0, *values)
    span = high - low
    if span == 0:
        return (-0.5, 0.5)
    padding = span * 0.1
    return (low - padding if low < 0 else 0.0, high + padding)


def _canvas(
    result: ProductionAnalysis,
    *,
    y_range: tuple[float, float],
    y_label: str,
    title: str | None,
    theme: PlotTheme | None,
) -> Canvas:
    selected = theme or default_theme()
    x_max = result.input_range[1]
    spec = CanvasSpec(
        x_range=(0.0, x_max),
        y_range=y_range,
        width=6.0,
        height=5.0,
        dpi=150,
        x_label=result.production_function.input_symbol,
        y_label=y_label,
        title=title,
    )
    canvas = Canvas(spec=spec, config=selected.mosaickit_config())
    canvas.extend(
        build_axes(
            AxisSpec(
                (0.0, x_max),
                arrow=ArrowPlacement.END,
                label=result.production_function.input_symbol,
            ),
            AxisSpec(y_range, arrow=ArrowPlacement.END, label=y_label),
        )
    )
    return canvas


def _region_layers(
    result: ProductionAnalysis, y_range: tuple[float, float]
) -> tuple[FillLayer, ...]:
    low, high = y_range
    return tuple(
        FillLayer(
            (
                (region.start_input, low),
                (region.end_input, low),
                (region.end_input, high),
                (region.start_input, high),
            ),
            id=f"micro.production.region.{region.kind.value}",
            role=f"micro.production.region.{region.kind.value}",
            model=region,
            z_index=-5,
        )
        for region in result.regions
    )


def _curve_layers(
    points: tuple[Point, ...],
    *,
    layer_id: str,
    role: str,
    label: str,
    model: object,
) -> tuple[PathLayer | TextLayer, ...]:
    curve = PathLayer(points, id=layer_id, role=role, model=model, legend=label, z_index=2)
    label_index = round((len(points) - 1) * 0.9)
    text = TextLayer(
        points[label_index],
        label,
        id=f"{layer_id}.label",
        role=role,
        anchor="left",
        offset=(5.0, 0.0),
        model=model,
        z_index=3,
    )
    return (curve, text)


def total_product_canvas(
    result: ProductionAnalysis,
    *,
    title: str | None = "Total product",
    theme: PlotTheme | None = None,
) -> Canvas:
    """Build a TP diagram with increasing, diminishing, and negative-return regions."""
    points = tuple((point.variable_input, point.total_product) for point in result.points)
    y_range = _y_range(value for _, value in points)
    canvas = _canvas(
        result,
        y_range=y_range,
        y_label=result.production_function.output_symbol,
        title=title,
        theme=theme,
    )
    canvas.extend(_region_layers(result, y_range))
    canvas.extend(
        _curve_layers(
            points,
            layer_id="micro.production.tp",
            role="micro.production.total",
            label="TP",
            model=result,
        )
    )
    return canvas


def average_marginal_product_canvas(
    result: ProductionAnalysis,
    *,
    title: str | None = "Average and marginal product",
    theme: PlotTheme | None = None,
) -> Canvas:
    """Build a shared AP/MP diagram with the three marginal-return regions."""
    average = tuple(
        (point.variable_input, point.average_product)
        for point in result.points
        if point.average_product is not None
    )
    marginal = tuple((point.variable_input, point.marginal_product) for point in result.points)
    y_range = _y_range((*[value for _, value in average], *[value for _, value in marginal]))
    canvas = _canvas(
        result,
        y_range=y_range,
        y_label="Product",
        title=title,
        theme=theme,
    )
    canvas.extend(_region_layers(result, y_range))
    canvas.extend(
        _curve_layers(
            average,
            layer_id="micro.production.ap",
            role="micro.production.average",
            label="AP",
            model=result,
        )
    )
    canvas.extend(
        _curve_layers(
            marginal,
            layer_id="micro.production.mp",
            role="micro.production.marginal",
            label="MP",
            model=result,
        )
    )
    return canvas


__all__ = ["average_marginal_product_canvas", "total_product_canvas"]
