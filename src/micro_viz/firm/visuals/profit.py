"""Linked total-revenue, total-cost and profit diagrams."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from mosaickit import Canvas, CanvasGrid, GridLink, GridSpacing, Layer, TextLayer

from micro_viz.core.theme import PlotTheme
from micro_viz.firm.competition import LinearDemand
from micro_viz.firm.costs import CostFunction
from micro_viz.visuals.axes import axes_layers
from micro_viz.visuals.common import (
    FIGURE_DPI,
    curve,
    curve_name,
    dot,
    new_canvas,
    nudge_labels,
    resolve_theme,
)

PANEL_SIZE = (6.0, 4.3)


def _roots(function: Callable[[float], float], high: float, samples: int) -> tuple[float, ...]:
    grid = tuple(high * index / (samples - 1) for index in range(samples))
    roots: list[float] = []
    for low, upper in zip(grid, grid[1:], strict=False):
        at_low, at_upper = function(low), function(upper)
        if at_low == 0:
            roots.append(low)
        elif at_low * at_upper < 0:
            left, right = low, upper
            for _ in range(80):
                middle = (left + right) / 2
                if function(left) * function(middle) <= 0:
                    right = middle
                else:
                    left = middle
            roots.append((left + right) / 2)
    if function(high) == 0:
        roots.append(high)
    return tuple(roots)


def _panel(
    theme: PlotTheme,
    *,
    x_range: tuple[float, float],
    y_range: tuple[float, float],
    x_label: str,
    y_label: str,
    title: str | None,
    size: tuple[float, float],
    dpi: int,
    layers: list[Layer],
) -> Canvas:
    canvas = new_canvas(
        theme,
        x_range=x_range,
        y_range=y_range,
        x_label=x_label,
        y_label=y_label,
        title=title,
        size=size,
        dpi=dpi,
    )
    canvas.extend(
        nudge_labels(
            [*axes_layers(x_range, y_range, x_label=x_label, y_label=y_label), *layers],
            theme.label_nudges,
        )
    )
    return canvas


def _profit_grid(
    cost: CostFunction,
    revenue: Callable[[float], float],
    marginal_revenue: Callable[[float], float],
    *,
    output_max: float,
    title: str | None,
    theme: PlotTheme | None,
    samples: int,
    size: tuple[float, float],
    dpi: int,
    prefix: str,
) -> CanvasGrid:
    if output_max <= 0 or samples < 3:
        raise ValueError("output_max must be positive and samples must be at least 3")
    selected = resolve_theme(theme)
    quantities = tuple(output_max * index / (samples - 1) for index in range(samples))
    revenues = tuple((q, revenue(q)) for q in quantities)
    costs = tuple((q, cost.total_cost(q)) for q in quantities)
    stationary = _roots(lambda q: marginal_revenue(q) - cost.marginal_cost(q), output_max, samples)
    break_even = _roots(lambda q: revenue(q) - cost.total_cost(q), output_max, samples)
    best = max(stationary or (0.0,), key=lambda q: revenue(q) - cost.total_cost(q))
    profit_end = min(
        output_max,
        max(break_even) + output_max * 0.03 if break_even else best + output_max * 0.22,
    )
    profit_samples = max(3, round(samples * profit_end / output_max))
    profit_quantities = tuple(
        profit_end * index / (profit_samples - 1) for index in range(profit_samples)
    )
    profits = tuple((q, revenue(q) - cost.total_cost(q)) for q in profit_quantities)
    x_range = (0.0, output_max * 1.08)
    total_top = max(value for _, value in (*revenues, *costs))
    profit_low = min(0.0, *(value for _, value in profits))
    profit_high = max(0.0, *(value for _, value in profits))
    profit_span = max(profit_high - profit_low, 1.0)
    top_range = (0.0, total_top * 1.15)
    bottom_range = (profit_low - profit_span * 0.12, profit_high + profit_span * 0.18)

    tr = curve(revenues, layer_id=f"{prefix}.tr", role="micro.curve.total")
    tc = curve(costs, layer_id=f"{prefix}.tc", role="micro.curve.total")
    pi = curve(profits, layer_id=f"{prefix}.profit", role="micro.curve.total")
    top_layers: list[Layer] = [
        tr,
        curve_name(tr, "$TR$", at=0.92),
        tc,
        curve_name(tc, "$TC$", at=0.92),
    ]
    bottom_layers: list[Layer] = [pi, curve_name(pi, "$\\pi$", at=0.94)]
    links: list[GridLink] = []

    for index, quantity in enumerate(stationary, start=1):
        at_revenue = revenue(quantity)
        at_cost = cost.total_cost(quantity)
        at_profit = at_revenue - at_cost
        label = "$Q^*$" if abs(quantity - best) < 1e-7 else f"$Q_{index + 1}$"
        reach = output_max * 0.1
        slope = marginal_revenue(quantity)
        left = max(0.0, quantity - reach)
        right = min(output_max, quantity + reach)
        top_layers.extend(
            (
                curve(
                    (
                        (left, at_revenue + slope * (left - quantity)),
                        (right, at_revenue + slope * (right - quantity)),
                    ),
                    layer_id=f"{prefix}.tangent.tr.{index}",
                    role="micro.curve.after",
                ),
                curve(
                    (
                        (left, at_cost + slope * (left - quantity)),
                        (right, at_cost + slope * (right - quantity)),
                    ),
                    layer_id=f"{prefix}.tangent.tc.{index}",
                    role="micro.curve.after",
                ),
                dot((quantity, at_revenue), layer_id=f"{prefix}.point.tr.{index}"),
                dot((quantity, at_cost), layer_id=f"{prefix}.point.tc.{index}"),
            )
        )
        top_layers.append(
            TextLayer(
                (quantity, 0.0),
                label,
                id=f"{prefix}.mark.stationary.{index}",
                role="axes",
                offset=(6.0, -5.0),
                anchor="top-left",
                math=True,
                z_index=8,
            )
        )
        bottom_layers.extend(
            (
                dot((quantity, at_profit), layer_id=f"{prefix}.point.profit.{index}"),
                curve(
                    (
                        (max(0.0, quantity - output_max * 0.09), at_profit),
                        (min(output_max, quantity + output_max * 0.09), at_profit),
                    ),
                    layer_id=f"{prefix}.tangent.profit.{index}",
                    role="micro.curve.after",
                ),
            )
        )
        links.append(
            GridLink(
                0,
                (quantity, max(at_revenue, at_cost)),
                1,
                (quantity, at_profit),
                role="micro.guide",
            )
        )

    for index, quantity in enumerate(break_even):
        if any(abs(quantity - point) < 1e-7 for point in stationary):
            continue
        at_total = revenue(quantity)
        top_layers.append(
            TextLayer(
                (quantity, 0.0),
                f"$Q_{index}$",
                id=f"{prefix}.mark.break_even.{index}",
                role="axes",
                offset=(6.0, -5.0),
                anchor="top-left",
                math=True,
                z_index=8,
            )
        )
        links.append(GridLink(0, (quantity, at_total), 1, (quantity, 0.0), role="micro.guide"))

    top = _panel(
        selected,
        x_range=x_range,
        y_range=top_range,
        x_label="$Q$",
        y_label="$TR,TC$",
        title=title,
        size=size,
        dpi=dpi,
        layers=top_layers,
    )
    bottom = _panel(
        selected,
        x_range=x_range,
        y_range=bottom_range,
        x_label="$Q$",
        y_label="$\\pi$",
        title=None,
        size=(size[0], size[1] * 0.45),
        dpi=dpi,
        layers=bottom_layers,
    )
    return CanvasGrid(
        [[top], [bottom]],
        links=links,
        spacing=GridSpacing(row_gap=0.11, outer=0.03),
    )


def competitive_profit_grid(
    cost: CostFunction,
    price: float,
    *,
    output_max: float,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    samples: int = 181,
    size: tuple[float, float] = PANEL_SIZE,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """Perfect competition: linear TR and the matching profit curve ``π = TR - TC``."""
    del labels
    if price <= 0:
        raise ValueError("price must be positive")
    return _profit_grid(
        cost,
        lambda q: price * q,
        lambda q: price,
        output_max=output_max,
        title=title,
        theme=theme,
        samples=samples,
        size=size,
        dpi=dpi,
        prefix="micro.profit.competitive",
    )


def monopoly_profit_grid(
    demand: LinearDemand,
    cost: CostFunction,
    *,
    output_max: float | None = None,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    samples: int = 181,
    size: tuple[float, float] = PANEL_SIZE,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """Monopoly: hump-shaped TR and the matching profit curve ``π = TR - TC``."""
    del labels
    reach = demand.quantity_intercept
    maximum = output_max if output_max is not None else reach
    if maximum > reach:
        raise ValueError("output_max cannot exceed the demand quantity intercept")
    return _profit_grid(
        cost,
        lambda q: demand.price(q) * q,
        lambda q: demand.intercept - 2 * demand.slope * q,
        output_max=maximum,
        title=title,
        theme=theme,
        samples=samples,
        size=size,
        dpi=dpi,
        prefix="micro.profit.monopoly",
    )


__all__ = ["competitive_profit_grid", "monopoly_profit_grid"]
