"""The piecewise cost figure."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import Canvas, Layer

from micro_viz.core.theme import PlotTheme
from micro_viz.firm.costs import CostAnalysis, PiecewiseCost
from micro_viz.firm.costs.visuals._base import _UNIT_STYLE, _setup, _unit_points
from micro_viz.visuals.axes import axes_layers
from micro_viz.visuals.common import (
    FIGURE_DPI,
    FIGURE_SIZE,
    MARGIN,
    Range,
    axis_mark,
    curve,
    curve_name,
    dot,
    drop_covered_guides,
    drop_line,
    guide,
    nudge_labels,
    pad_range,
)


def piecewise_cost_canvas(
    analysis: CostAnalysis,
    *,
    prices: Sequence[float] = (),
    average: bool = True,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    x_label: str | None = None,
    y_label: str | None = None,
    x_max: float | None = None,
    y_range: Range | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Stepped or kinked marginal cost with its capacity and price bands.

    MC is drawn with its jumps; ``average`` adds AVC. A dashed vertical line marks the capacity.
    Each price in ``prices`` is a dashed horizontal line with a dot at the output the firm
    chooses at that price (where the price meets MC, or the last output before a jump that
    lies above it) and axis marks for the price and the output.
    """
    cost = analysis.cost
    if not isinstance(cost, PiecewiseCost):
        raise TypeError("piecewise_cost_canvas needs a PiecewiseCost")
    series = {}
    if average:
        series["avc"] = _unit_points(analysis, "avc")
    series["mc"] = _unit_points(analysis, "mc")  # drawn last: MC lies over AVC where they meet
    top = max(max(value for _, value in points) for points in series.values())
    top = max([top, *prices])
    low = min(min(value for _, value in points) for points in series.values())
    vertical = y_range or pad_range(min(0.0, low) if low < 0 else 0.0, top, margin)
    canvas, selected, texts, x_axis, horizontal, vertical_label = _setup(
        analysis,
        theme=theme,
        labels=labels,
        x_label=x_label,
        y_label=y_label,
        y_text_id="cost.axis.unit",
        x_max=x_max,
        y_range=vertical,
        title=title,
        size=size,
        dpi=dpi,
        margin=margin,
    )
    symbol = cost.output_symbol
    layers: list[Layer] = list(
        axes_layers(x_axis, vertical, x_label=horizontal, y_label=vertical_label)
    )
    for name, points in series.items():
        role, key, along = _UNIT_STYLE[name]
        path = curve(points, layer_id=f"micro.cost.{name}", role=role, model=analysis)
        layers.extend((path, curve_name(path, texts(key), at=along)))
    floor = vertical[0]
    layers.append(
        drop_line(cost.capacity, vertical[1], layer_id="micro.cost.guide.capacity", floor=floor)
    )
    layers.append(
        axis_mark(
            "x",
            cost.capacity,
            texts("cost.mark.capacity", output=symbol),
            layer_id="micro.cost.mark.capacity",
        )
    )
    for index, price in enumerate(prices, start=1):
        quantity = cost.output_at_price(price)
        layers.append(
            guide((0.0, price), (x_axis[1], price), layer_id=f"micro.cost.guide.price.{index}")
        )
        layers.append(
            axis_mark(
                "y",
                price,
                texts("cost.mark.price", index=index),
                layer_id=f"micro.cost.mark.price.{index}",
            )
        )
        if quantity > 0:
            layers.append(
                drop_line(quantity, price, layer_id=f"micro.cost.guide.output.{index}", floor=floor)
            )
            layers.append(dot((quantity, price), layer_id=f"micro.cost.point.output.{index}"))
        if 0 < quantity < cost.capacity:
            layers.append(
                axis_mark(
                    "x",
                    quantity,
                    texts("cost.mark.price_output", output=symbol, index=index),
                    layer_id=f"micro.cost.mark.output.{index}",
                )
            )
    canvas.extend(nudge_labels(drop_covered_guides(layers), selected.label_nudges))
    return canvas
