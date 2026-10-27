"""Monopsony and its welfare loss."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import Canvas, CanvasGrid

from micro_viz.core.theme import PlotTheme
from micro_viz.markets.factors import (
    LinearSupply,
    LinearValue,
    Monopsonist,
)
from micro_viz.markets.visuals.factors._base import _extent, _monopsony_plane, _plane, segment
from micro_viz.visuals.common import FIGURE_DPI, FIGURE_SIZE, MARGIN
from micro_viz.visuals.plane import PANEL


def monopsony_canvas(
    model: Monopsonist,
    *,
    labor: bool = False,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Monopsony: the buyer hires where ``ME = MV`` (``MRP`` for labour) and pays the supply
    price at that quantity, below the competitive quantity and price. ``labor`` switches the
    text to ``L``, ``W`` and ``MRP``."""
    kind = "labor" if labor else "input"
    x_max, y_max = _extent(model)
    plane = _plane(
        "factors.monopsony",
        kind,
        x_max,
        y_max,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    _monopsony_plane(plane, model, kind)
    return plane.finish()


def competitive_pair_canvas(
    value: LinearValue,
    supply: LinearSupply,
    price: float,
    *,
    titles: tuple[str | None, str | None] = (None, None),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """A competitive buyer (flat ``ME = AE`` at ``price`` against ``MV``) beside a competitive
    seller (flat ``MR = AR`` at ``price`` against ``MC``)."""
    x_max, y_max = value.quantity_intercept, value.intercept
    cells = []
    for side, title in zip(("buyer", "seller"), titles, strict=True):
        plane = _plane(
            f"factors.competitive.{side}",
            "input",
            x_max,
            y_max,
            theme=theme,
            labels=labels,
            title=title,
            margin=margin,
            size=size,
            dpi=dpi,
        )
        if side == "buyer":
            plane.line(
                segment(value.intercept, -value.slope, x_max, y_max),
                plane.t("factors.curve.mv"),
                role="micro.curve.demand",
            )
            level, quantity = price, (value.intercept - price) / value.slope
            flat = plane.t("factors.curve.me_ae")
        else:
            plane.line(
                segment(supply.intercept, supply.slope, x_max, y_max), plane.t("factors.curve.mc")
            )
            level, quantity = price, supply.quantity(price)
            flat = plane.t("factors.curve.mr_ar")
        plane.line(((0.0, level), (plane.x_max, level)), flat, role="micro.curve.price")
        plane.point(
            quantity,
            level,
            xtext=plane.t("factors.input.mark.q_star"),
            ytext=plane.t("factors.input.mark.p_star"),
        )
        cells.append(plane.finish())
    return CanvasGrid([cells])


def monopoly_monopsony_pair_canvas(
    model: Monopsonist,
    *,
    titles: tuple[str | None, str | None] = (None, None),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """Monopoly (``AR``, ``MR``, ``MC``) beside monopsony (``MV``, ``ME``, ``AE``) built from
    the same pair of linear curves: the monopolist's demand is the value curve and its cost the
    supply curve."""
    x_max, y_max = _extent(model)
    s, v = model.supply, model.value
    left = _plane(
        "factors.pair.monopoly",
        "input",
        x_max,
        y_max,
        theme=theme,
        labels=labels,
        title=titles[0],
        margin=margin,
        size=size,
        dpi=dpi,
    )
    left.line(
        segment(v.intercept, -v.slope, x_max, y_max),
        left.t("factors.curve.ar"),
        role="micro.curve.demand",
    )
    left.line(
        segment(v.intercept, -2 * v.slope, x_max, y_max),
        left.t("factors.curve.mr"),
        role="micro.curve.marginal_revenue",
    )
    left.line(segment(s.intercept, s.slope, x_max, y_max), left.t("factors.curve.mc"))
    quantity = (v.intercept - s.intercept) / (2 * v.slope + s.slope)
    price = v.value(quantity)
    left.point(
        quantity,
        price,
        xtext=left.t("factors.input.mark.q_star"),
        ytext=left.t("factors.input.mark.p_star"),
    )
    left.guide((quantity, s.wage(quantity)), (quantity, price))
    left.dot((quantity, s.wage(quantity)))
    right = _plane(
        "factors.pair.monopsony",
        "input",
        x_max,
        y_max,
        theme=theme,
        labels=labels,
        title=titles[1],
        margin=margin,
        size=size,
        dpi=dpi,
    )
    _monopsony_plane(right, model, "input", competitive_marks=False)
    return CanvasGrid([[left.finish(), right.finish()]])


def supply_elasticity_canvas(
    value: LinearValue,
    supplies: Sequence[LinearSupply],
    *,
    titles: Sequence[str | None] | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """One monopsony panel per supply curve, on common axes: the flatter (more elastic) the
    supply, the closer ``ME`` lies to ``AE``."""
    heading = list(titles) if titles is not None else [None] * len(supplies)
    cells: list[Canvas] = []
    x_max, y_max = value.quantity_intercept, value.intercept
    for index, supply in enumerate(supplies, start=1):
        plane = _plane(
            f"factors.elasticity.s{index}",
            "input",
            x_max,
            y_max,
            theme=theme,
            labels=labels,
            title=heading[index - 1],
            margin=margin,
            size=size,
            dpi=dpi,
        )
        _monopsony_plane(plane, Monopsonist(supply, value), "input", competitive_marks=False)
        cells.append(plane.finish())
    return CanvasGrid([cells])


def monopsony_dwl_canvas(
    model: Monopsonist,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Monopsony against the competitive outcome: the rectangle ``A`` is the transfer from
    sellers to the buyer and the triangles ``B`` and ``C`` (above and below the competitive
    price) together are the deadweight loss."""
    x_max, y_max = _extent(model)
    plane = _plane(
        "factors.dwl",
        "input",
        x_max,
        y_max,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    r = model.solve()
    q, w, qc, wc, mv = (
        r.quantity,
        r.wage,
        r.competitive_quantity,
        r.competitive_wage,
        r.marginal_value,
    )
    plane.area(
        ((0.0, w), (q, w), (q, wc), (0.0, wc)), plane.t("factors.region.transfer"), shade="mid"
    )
    plane.area(((q, wc), (qc, wc), (q, mv)), plane.t("factors.region.upper"), shade="dark")
    plane.area(((q, w), (qc, wc), (q, wc)), plane.t("factors.region.lower"), shade="light")
    _monopsony_plane(plane, model, "input")
    return plane.finish()
