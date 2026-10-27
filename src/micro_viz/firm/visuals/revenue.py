"""Linked total-, average- and marginal-revenue diagrams."""

from __future__ import annotations

from collections.abc import Mapping

from mosaickit import (
    ArrowLayer,
    Canvas,
    CanvasGrid,
    GridLink,
    GridSpacing,
    Layer,
    PointLabelLayer,
)

from micro_viz.core.theme import PlotTheme
from micro_viz.firm.competition import LinearDemand
from micro_viz.visuals.axes import axes_layers
from micro_viz.visuals.common import (
    FIGURE_DPI,
    axis_mark,
    curve,
    curve_name,
    dot,
    guide,
    new_canvas,
    nudge_labels,
    resolve_theme,
)

PANEL_SIZE = (6.0, 4.3)


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


def competitive_revenue_grid(
    price: float,
    *,
    output_max: float = 10.0,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    size: tuple[float, float] = PANEL_SIZE,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """Perfect competition: linear total revenue above horizontal ``p = AR = MR``."""
    return competitive_revenue_shift_grid(
        price,
        None,
        output_max=output_max,
        title=title,
        theme=theme,
        labels=labels,
        size=size,
        dpi=dpi,
    )


def competitive_revenue_shift_grid(
    price: float,
    new_price: float | None,
    *,
    output_max: float = 10.0,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    size: tuple[float, float] = PANEL_SIZE,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """Perfect-competition revenue; optionally show a price rise and the matching TR rotation."""
    if price <= 0 or output_max <= 0:
        raise ValueError("price and output_max must be positive")
    if new_price is not None and new_price <= price:
        raise ValueError("new_price must be greater than price")
    del labels
    selected = resolve_theme(theme)
    high_price = new_price if new_price is not None else price
    x_range = (0.0, output_max * 1.08)
    top_range = (0.0, high_price * output_max * 1.16)
    bottom_range = (0.0, high_price * 1.4)

    prices = (price,) if new_price is None else (price, new_price)
    top_layers: list[Layer] = []
    bottom_layers: list[Layer] = []
    for index, value in enumerate(prices):
        suffix = "" if index == 0 else ".after"
        role = "micro.curve.total" if index == 0 else "micro.curve.after"
        total = curve(
            ((0.0, 0.0), (output_max, value * output_max)),
            layer_id=f"micro.revenue.competitive.tr{suffix}",
            role=role,
        )
        level = curve(
            ((0.0, value), (output_max, value)),
            layer_id=f"micro.revenue.competitive.unit{suffix}",
            role=role,
        )
        price_symbol = "p" if index == 0 else "p_1"
        top_layers.extend(
            (
                total,
                curve_name(total, f"$TR={price_symbol}Q$", at=1.0),
            )
        )
        bottom_layers.extend(
            (
                level,
                curve_name(level, f"${price_symbol}=AR=MR$", at=1.0),
                axis_mark(
                    "y",
                    value,
                    f"${price_symbol}$",
                    layer_id=f"micro.revenue.competitive.mark.price{suffix}",
                ),
            )
        )
    if new_price is not None:
        q_arrow = output_max * 0.7
        top_layers.append(
            ArrowLayer(
                (q_arrow, price * q_arrow),
                (q_arrow, new_price * q_arrow),
                id="micro.revenue.competitive.shift.tr",
                role="micro.arrow",
                z_index=6,
            )
        )
        bottom_layers.append(
            ArrowLayer(
                (q_arrow, price),
                (q_arrow, new_price),
                id="micro.revenue.competitive.shift.unit",
                role="micro.arrow",
                z_index=6,
            )
        )

    top = _panel(
        selected,
        x_range=x_range,
        y_range=top_range,
        x_label="$Q$",
        y_label="$TR$",
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
        y_label="$p$",
        title=None,
        size=size,
        dpi=dpi,
        layers=bottom_layers,
    )
    return CanvasGrid([[top], [bottom]], spacing=GridSpacing(row_gap=0.11, outer=0.03))


def monopoly_revenue_grid(
    demand: LinearDemand,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    samples: int = 121,
    size: tuple[float, float] = PANEL_SIZE,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """Total revenue above the corresponding linear ``AR`` and ``MR`` curves."""
    del labels
    if samples < 3:
        raise ValueError("samples must be at least 3")
    selected = resolve_theme(theme)
    reach = demand.quantity_intercept
    quantities = tuple(reach * index / (samples - 1) for index in range(samples))
    revenue = tuple((q, demand.price(q) * q) for q in quantities)
    ar = ((0.0, demand.intercept), (reach, 0.0))
    mr = ((0.0, demand.intercept), (reach / 2.0, 0.0))
    q_a = reach / 2.0
    marked = (("B", reach * 0.16), ("C", reach * 0.32), ("A", q_a))
    tr_max = demand.price(q_a) * q_a
    x_range = (0.0, reach * 1.1)
    top_range = (0.0, tr_max * 1.28)
    bottom_range = (0.0, demand.intercept * 1.14)

    tr_curve = curve(
        revenue,
        layer_id="micro.revenue.monopoly.tr",
        role="micro.curve.total",
        model=demand,
    )
    ar_curve = curve(
        ar,
        layer_id="micro.revenue.monopoly.ar",
        role="micro.curve.total",
        model=demand,
    )
    mr_curve = curve(
        mr,
        layer_id="micro.revenue.monopoly.mr",
        role="micro.curve.marginal",
        model=demand,
    )
    top_layers: list[Layer] = [
        tr_curve,
        curve_name(tr_curve, "$TR=p(Q)Q$", at=0.7),
        guide((0.0, tr_max), (q_a, tr_max), layer_id="micro.revenue.monopoly.guide.maximum"),
        dot((reach, 0.0), layer_id="micro.revenue.monopoly.point.intercept"),
    ]
    bottom_layers: list[Layer] = [
        ar_curve,
        curve_name(ar_curve, "$p(Q)=AR$", at=0.72),
        mr_curve,
        curve_name(mr_curve, "$MR$", at=0.92),
        dot((reach, 0.0), layer_id="micro.revenue.monopoly.ar.intercept"),
        dot((reach / 2.0, 0.0), layer_id="micro.revenue.monopoly.mr.intercept"),
        axis_mark("x", reach, "$a/b$", layer_id="micro.revenue.monopoly.mark.ar"),
        axis_mark("x", reach / 2.0, "$a/(2b)$", layer_id="micro.revenue.monopoly.mark.mr"),
    ]
    links: list[GridLink] = []
    for index, (name, quantity) in enumerate(marked, start=1):
        total = demand.price(quantity) * quantity
        price = demand.price(quantity)
        top_layers.extend(
            (
                dot((quantity, total), layer_id=f"micro.revenue.monopoly.tr.point.{index}"),
                PointLabelLayer(
                    (quantity, total),
                    name,
                    id=f"micro.revenue.monopoly.tr.point.{index}.label",
                    role="micro.point",
                    z_index=7,
                ),
            )
        )
        bottom_layers.extend(
            (
                dot((quantity, price), layer_id=f"micro.revenue.monopoly.ar.point.{index}"),
                PointLabelLayer(
                    (quantity, price),
                    name,
                    id=f"micro.revenue.monopoly.ar.point.{index}.label",
                    role="micro.point",
                    z_index=7,
                ),
                guide(
                    (0.0, price),
                    (quantity, price),
                    layer_id=f"micro.revenue.monopoly.guide.price.{index}",
                ),
            )
        )
        links.append(GridLink(0, (quantity, total), 1, (quantity, price), role="micro.guide"))
    links.append(GridLink(0, (reach, 0.0), 1, (reach, 0.0), role="micro.guide"))

    top = _panel(
        selected,
        x_range=x_range,
        y_range=top_range,
        x_label="$Q$",
        y_label="$TR$",
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
        y_label="$p$",
        title=None,
        size=size,
        dpi=dpi,
        layers=bottom_layers,
    )
    return CanvasGrid(
        [[top], [bottom]],
        links=links,
        spacing=GridSpacing(row_gap=0.11, outer=0.03),
    )


__all__ = [
    "competitive_revenue_grid",
    "competitive_revenue_shift_grid",
    "monopoly_revenue_grid",
]
