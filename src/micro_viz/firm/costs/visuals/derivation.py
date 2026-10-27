"""Four linked panels deriving total variable cost from a production function."""

from __future__ import annotations

from collections.abc import Mapping

from mosaickit import (
    ArrowPlacement,
    ArrowStyle,
    Canvas,
    CanvasGrid,
    GridLink,
    GridSpacing,
    Layer,
    PathLayer,
    PointLabelLayer,
    Stroke,
    TextLayer,
)

from micro_viz.core.theme import PlotTheme
from micro_viz.firm.production import ShortRunProductionFunction
from micro_viz.visuals.axes import axes_layers
from micro_viz.visuals.common import (
    FIGURE_DPI,
    Point,
    curve,
    dot,
    new_canvas,
    nudge_labels,
    resolve_theme,
)

PANEL_SIZE = (5.0, 5.0)


def _panel(
    theme: PlotTheme,
    *,
    x_range: tuple[float, float],
    y_range: tuple[float, float],
    x_label: str,
    y_label: str,
    layers: list[Layer],
    title: str | None,
    size: tuple[float, float],
    dpi: int,
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
    all_layers = [*axes_layers(x_range, y_range, x_label=x_label, y_label=y_label), *layers]
    canvas.extend(nudge_labels(all_layers, theme.label_nudges))
    return canvas


def variable_cost_derivation_grid(
    production: ShortRunProductionFunction,
    wage: float,
    labor_levels: tuple[float, float],
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    samples: int = 121,
    size: tuple[float, float] = PANEL_SIZE,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """Derive ``TVC(Q)`` from ``TVC=wL`` and ``Q=F(L,K_0)`` in four linked panels."""
    del labels
    selected = resolve_theme(theme)
    l0, l1 = labor_levels
    if not 0 < l0 < l1 <= production.total_product_max_input:
        raise ValueError("labor_levels must increase inside the rising part of total product")
    if wage <= 0 or samples < 2:
        raise ValueError("wage must be positive and samples must be at least 2")

    peak_labor = production.total_product_max_input
    labor_max = peak_labor * 1.12
    labor = tuple(labor_max * i / (samples - 1) for i in range(samples))
    products = tuple(production.total_product(value) for value in labor)
    rising_labor = tuple(peak_labor * i / (samples - 1) for i in range(samples))
    rising_products = tuple(production.total_product(value) for value in rising_labor)
    rising_costs = tuple(wage * value for value in rising_labor)
    q0, q1 = production.total_product(l0), production.total_product(l1)
    c0, c1 = wage * l0, wage * l1
    l_range = (0.0, labor_max * 1.08)
    q_max = production.total_product(peak_labor) * 1.16
    q_range = (0.0, q_max)
    c_range = (0.0, wage * peak_labor * 1.12)

    def marks(prefix: str, points: tuple[Point, Point]) -> list[Layer]:
        return [
            dot(point, layer_id=f"micro.cost.derivation.{prefix}.point.{i}")
            for i, point in enumerate(points)
        ]

    labor_cost_end = min(labor_max, l1 * 1.36)
    labor_cost = curve(
        ((0.0, 0.0), (labor_cost_end, wage * labor_cost_end)),
        layer_id="micro.cost.derivation.labor_cost",
        role="micro.curve.marginal",
    )
    p0 = (l0, c0)
    p1 = (l1, c1)
    top_left = _panel(
        selected,
        x_range=l_range,
        y_range=c_range,
        x_label="$L$",
        y_label="$TVC$",
        title=title,
        size=size,
        dpi=dpi,
        layers=[
            labor_cost,
            TextLayer(
                (labor_cost_end, wage * labor_cost_end),
                "$TVC=w\\times L$",
                id="micro.cost.derivation.labor_cost.label",
                role="micro.curve.marginal",
                offset=(8.0, 8.0),
                anchor="bottom-left",
                math=True,
            ),
            *marks("labor_cost", (p0, p1)),
            PointLabelLayer(
                (l_range[1] * 0.91, c0),
                "$TVC_0$",
                id="micro.cost.derivation.mark.c0",
                role="micro.annotation",
            ),
            PointLabelLayer(
                (l_range[1] * 0.91, c1),
                "$TVC_1$",
                id="micro.cost.derivation.mark.c1",
                role="micro.annotation",
            ),
            TextLayer(
                (l0, 0.0),
                "$L_0$",
                id="micro.cost.derivation.mark.l0",
                role="axes",
                offset=(5.0, -6.0),
                anchor="top-left",
                math=True,
            ),
            TextLayer(
                (l1, 0.0),
                "$L_1$",
                id="micro.cost.derivation.mark.l1",
                role="axes",
                offset=(5.0, -6.0),
                anchor="top-left",
                math=True,
            ),
        ],
    )

    production_curve = curve(
        tuple(zip(labor, products, strict=True)),
        layer_id="micro.cost.derivation.production",
        role="micro.curve.marginal",
        model=production,
    )
    bottom_left = _panel(
        selected,
        x_range=l_range,
        y_range=q_range,
        x_label="$L$",
        y_label="$Q$",
        title=None,
        size=size,
        dpi=dpi,
        layers=[
            production_curve,
            TextLayer(
                (peak_labor, production.total_product(peak_labor)),
                "$Q=F(L,K_0)$",
                id="micro.cost.derivation.production.label",
                role="micro.curve.marginal",
                offset=(0.0, 10.0),
                anchor="bottom",
                math=True,
            ),
            *marks("production", ((l0, q0), (l1, q1))),
        ],
    )

    output_cost = curve(
        tuple(zip(rising_products, rising_costs, strict=True)),
        layer_id="micro.cost.derivation.output_cost",
        role="micro.curve.marginal",
    )
    top_right = _panel(
        selected,
        x_range=q_range,
        y_range=c_range,
        x_label="$Q$",
        y_label="$TVC$",
        title=None,
        size=size,
        dpi=dpi,
        layers=[
            output_cost,
            PointLabelLayer(
                (rising_products[-1], rising_costs[-1]),
                "$TVC$",
                id="micro.cost.derivation.output_cost.label",
                role="micro.curve.marginal",
            ),
            *marks("output_cost", ((q0, c0), (q1, c1))),
            TextLayer(
                (q0, 0.0),
                "$Q_0$",
                id="micro.cost.derivation.mark.q0",
                role="axes",
                offset=(5.0, -6.0),
                anchor="top-left",
                math=True,
            ),
            TextLayer(
                (q1, 0.0),
                "$Q_1$",
                id="micro.cost.derivation.mark.q1",
                role="axes",
                offset=(5.0, -6.0),
                anchor="top-left",
                math=True,
            ),
        ],
    )

    diagonal_end = q_max * 0.84
    diagonal = PathLayer(
        ((0.0, 0.0), (diagonal_end, diagonal_end)),
        Stroke(
            color=selected.colors["marginal"],
            width=selected.arrow_width,
            arrow=ArrowStyle.TRIANGLE,
        ),
        arrow_placement=ArrowPlacement.END,
        id="micro.cost.derivation.diagonal",
        role="micro.curve.marginal",
        z_index=2,
    )
    bottom_right = _panel(
        selected,
        x_range=q_range,
        y_range=q_range,
        x_label="$Q$",
        y_label="$Q$",
        title=None,
        size=size,
        dpi=dpi,
        layers=[
            diagonal,
            *marks("diagonal", ((q0, q0), (q1, q1))),
        ],
    )

    links: list[GridLink] = []
    for labor_value, output, cost in ((l0, q0, c0), (l1, q1, c1)):
        links.extend(
            (
                GridLink(0, (labor_value, cost), 1, (output, cost), role="micro.guide"),
                GridLink(0, (labor_value, cost), 2, (labor_value, output), role="micro.guide"),
                GridLink(1, (output, cost), 3, (output, output), role="micro.guide"),
                GridLink(2, (labor_value, output), 3, (output, output), role="micro.guide"),
            )
        )
    return CanvasGrid(
        [[top_left, top_right], [bottom_left, bottom_right]],
        links=links,
        spacing=GridSpacing(column_gap=0.14, row_gap=0.1, outer=0.03),
    )


def product_cost_derivation_grid(
    production: ShortRunProductionFunction,
    wage: float,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    samples: int = 161,
    size: tuple[float, float] = PANEL_SIZE,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """Link TP/AP/MP to AVC/SMC through a 45-degree output-transfer panel."""
    del labels
    if wage <= 0 or samples < 3:
        raise ValueError("wage must be positive and samples must be at least 3")
    selected = resolve_theme(theme)
    l1 = production.inflection_input
    l2 = production.average_product_max_input
    l3 = production.total_product_max_input
    labor_max = l3 * 1.12
    labor = tuple(labor_max * i / (samples - 1) for i in range(samples))
    tp = tuple((value, production.total_product(value)) for value in labor)
    ap = tuple(
        (value, product)
        for value in labor[1:]
        if (product := production.average_product(value)) is not None
    )
    mp = tuple((value, production.marginal_product(value)) for value in labor)
    product_top = max(y for _, y in (*ap, *mp))
    product_range = (-0.28 * product_top, 1.18 * product_top)
    q_max = production.total_product(l3) * 1.14
    q_range = (0.0, q_max)
    l_range = (0.0, labor_max * 1.05)
    q1, q2 = production.total_product(l1), production.total_product(l2)
    mp_label_point = min(mp, key=lambda point: abs(point[0] - l3 * 1.04))

    cost_labor = tuple(
        l1 * 0.22 + (l2 + 0.58 * (l3 - l2) - l1 * 0.22) * i / (samples - 1) for i in range(samples)
    )
    smc = tuple(
        (production.total_product(value), wage / production.marginal_product(value))
        for value in cost_labor
    )
    avc = tuple(
        (production.total_product(value), wage / average)
        for value in cost_labor
        if (average := production.average_product(value)) is not None
    )
    cost_top = max(y for _, y in (*smc, *avc)) * 1.08
    cost_range = (0.0, cost_top)

    top_left = _panel(
        selected,
        x_range=l_range,
        y_range=product_range,
        x_label="$L$",
        y_label="$MP_L, AP_L$",
        title=title,
        size=size,
        dpi=dpi,
        layers=[
            PathLayer(mp, id="micro.cost.product.mp", role="micro.curve.marginal", z_index=2),
            PathLayer(ap, id="micro.cost.product.ap", role="micro.curve.average", z_index=2),
            PointLabelLayer(
                mp_label_point,
                "$MP_L$",
                id="micro.cost.product.mp.label",
                role="micro.curve.marginal",
                z_index=7,
            ),
            PointLabelLayer(
                ap[-1],
                "$AP_L$",
                id="micro.cost.product.ap.label",
                role="micro.curve.average",
                z_index=7,
            ),
            dot((l1, production.marginal_product(l1)), layer_id="micro.cost.product.mp.maximum"),
            dot((l2, production.marginal_product(l2)), layer_id="micro.cost.product.ap.maximum"),
            dot((l3, 0.0), layer_id="micro.cost.product.mp.zero"),
        ],
    )
    bottom_left = _panel(
        selected,
        x_range=l_range,
        y_range=q_range,
        x_label="$L$",
        y_label="$TP_L$",
        title=None,
        size=size,
        dpi=dpi,
        layers=[
            PathLayer(
                (
                    (0.0, 0.0),
                    (l1 * 1.55, q1 * 1.55),
                ),
                Stroke(
                    color=selected.colors["marginal"],
                    width=selected.guide_width,
                    arrow=ArrowStyle.TRIANGLE,
                ),
                arrow_placement=ArrowPlacement.END,
                id="micro.cost.product.tp.tangent",
                role="micro.curve.marginal",
                z_index=1,
            ),
            PathLayer(tp, id="micro.cost.product.tp", role="micro.curve.total", z_index=2),
            PointLabelLayer(
                tp[-1],
                "$TP_L$",
                id="micro.cost.product.tp.label",
                role="micro.curve.total",
                z_index=7,
            ),
            dot((l1, q1), layer_id="micro.cost.product.tp.point.1"),
            dot((l2, q2), layer_id="micro.cost.product.tp.point.2"),
            dot((l3, production.total_product(l3)), layer_id="micro.cost.product.tp.maximum"),
        ],
    )
    top_right = _panel(
        selected,
        x_range=q_range,
        y_range=cost_range,
        x_label="$Q$",
        y_label="$P$",
        title=None,
        size=size,
        dpi=dpi,
        layers=[
            PathLayer(
                smc,
                id="micro.cost.product.smc",
                role="micro.curve.marginal",
                z_index=2,
            ),
            PathLayer(
                avc,
                id="micro.cost.product.avc",
                role="micro.curve.average",
                z_index=2,
            ),
            PointLabelLayer(
                smc[-1],
                "$SMC$",
                id="micro.cost.product.smc.label",
                role="micro.curve.marginal",
                z_index=7,
            ),
            PointLabelLayer(
                avc[-1],
                "$AVC$",
                id="micro.cost.product.avc.label",
                role="micro.curve.average",
                z_index=7,
            ),
            dot(
                (q1, wage / production.marginal_product(l1)),
                layer_id="micro.cost.product.smc.minimum",
            ),
            dot(
                (q2, wage / production.marginal_product(l2)), layer_id="micro.cost.product.smc.avc"
            ),
        ],
    )
    diagonal_end = q_max * 0.84
    bottom_right = _panel(
        selected,
        x_range=q_range,
        y_range=q_range,
        x_label="$Q$",
        y_label="$Q$",
        title=None,
        size=size,
        dpi=dpi,
        layers=[
            PathLayer(
                ((0.0, 0.0), (diagonal_end, diagonal_end)),
                Stroke(
                    color=selected.colors["marginal"],
                    width=selected.arrow_width,
                    arrow=ArrowStyle.TRIANGLE,
                ),
                arrow_placement=ArrowPlacement.END,
                id="micro.cost.product.diagonal",
                role="micro.curve.marginal",
                z_index=2,
            ),
            dot((q1, q1), layer_id="micro.cost.product.diagonal.point.1"),
            dot((q2, q2), layer_id="micro.cost.product.diagonal.point.2"),
            TextLayer(
                (diagonal_end, diagonal_end),
                "$45^\\circ$",
                id="micro.cost.product.diagonal.label",
                role="micro.curve.marginal",
                offset=(7.0, 7.0),
                anchor="bottom-left",
                math=True,
                z_index=7,
            ),
        ],
    )
    links: list[GridLink] = []
    for labor_value in (l1, l2, l3):
        links.append(
            GridLink(
                0,
                (labor_value, production.marginal_product(labor_value)),
                2,
                (labor_value, production.total_product(labor_value)),
                role="micro.guide",
            )
        )
    for output, labor_value in ((q1, l1), (q2, l2)):
        links.extend(
            (
                GridLink(
                    1,
                    (output, wage / production.marginal_product(labor_value)),
                    3,
                    (output, output),
                    role="micro.guide",
                ),
                GridLink(2, (labor_value, output), 3, (output, output), role="micro.guide"),
            )
        )
    return CanvasGrid(
        [[top_left, top_right], [bottom_left, bottom_right]],
        links=links,
        spacing=GridSpacing(column_gap=0.14, row_gap=0.1, outer=0.03),
    )


__all__ = ["product_cost_derivation_grid", "variable_cost_derivation_grid"]
