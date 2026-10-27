"""mosaickit visual builders for cost minimization, input prices and expansion paths."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import Canvas, CanvasGrid

from micro_viz.core.theme import PlotTheme
from micro_viz.firm.isoquant import (
    Bundle,
    Technology,
    cost_minimizing_bundle,
    expansion_path,
    isocost_segment,
)
from micro_viz.visuals.common import FIGURE_DPI, FIGURE_SIZE, MARGIN, Point
from micro_viz.visuals.plane import PANEL, Plane, sample

_PREFIX = "isocost"


def _plane(
    tech: Technology,
    bounds: Point,
    *,
    theme: PlotTheme | None,
    labels: Mapping[str, str] | None,
    title: str | None,
    margin: float,
    size: tuple[float, float],
    dpi: int,
) -> Plane:
    return Plane(
        prefix=_PREFIX,
        x_label=tech.labor_symbol,
        y_label=tech.capital_symbol,
        x_max=bounds[0],
        y_max=bounds[1],
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )


def _isoquant(
    plane: Plane, tech: Technology, output: float, bounds: Point, name: str, *, thin: bool = False
) -> None:
    points = tech.isoquant(output, bounds)
    if len(points) >= 2:
        (plane.thin if thin else plane.line)(points, name)


def _isocost(
    plane: Plane,
    cost: float,
    wage: float,
    rent: float,
    bounds: Point,
    name: str | None,
    *,
    thin: bool = False,
) -> None:
    first, last = isocost_segment(cost, wage, rent, bounds)
    if thin:
        plane.thin((first, last), name, at=0.0)
    else:
        plane.line((first, last), name, role="micro.curve.average", at=0.0)


def _bundle_marks(
    plane: Plane, tech: Technology, bundle: Bundle, *, after: bool = False, name: str | None = None
) -> None:
    key_x = "isocost.mark.labor_after" if after else "isocost.mark.labor"
    key_y = "isocost.mark.capital_after" if after else "isocost.mark.capital"
    plane.point(
        bundle.labor,
        bundle.capital,
        xtext=plane.t(key_x, symbol=tech.labor_symbol),
        ytext=plane.t(key_y, symbol=tech.capital_symbol),
        name=name,
    )


def cost_minimization_canvas(
    tech: Technology,
    output: float,
    wage: float,
    rent: float,
    bounds: Point,
    *,
    cost_offsets: tuple[float, float] = (0.7, 1.35),
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """The isoquant of ``output`` with the isocost line that touches it at the cheapest bundle,
    and a lower and a higher isocost line (scaled by ``cost_offsets``): the lower one cannot
    reach the output, the higher one costs more than needed."""
    best = cost_minimizing_bundle(tech, output, wage, rent)
    plane = _plane(
        tech, bounds, theme=theme, labels=labels, title=title, margin=margin, size=size, dpi=dpi
    )
    _isoquant(plane, tech, output, bounds, plane.t("isoquant.curve", index=1))
    for index, scale in enumerate((cost_offsets[0], 1.0, cost_offsets[1]), start=1):
        _isocost(plane, best.cost * scale, wage, rent, bounds, plane.t("isocost.line", index=index))
    _bundle_marks(plane, tech, best, name=plane.t("isocost.point_names")[0])
    return plane.finish()


def input_price_change_canvas(
    tech: Technology,
    output: float,
    wage: float,
    rent: float,
    new_wage: float,
    bounds: Point,
    *,
    along: bool = False,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Labour becomes dearer (``new_wage``): the isocost line steepens, its new tangency uses
    less labour and more capital. With ``along`` an arrow runs along the isoquant between the
    two tangencies."""
    before = cost_minimizing_bundle(tech, output, wage, rent)
    after = cost_minimizing_bundle(tech, output, new_wage, rent)
    plane = _plane(
        tech, bounds, theme=theme, labels=labels, title=title, margin=margin, size=size, dpi=dpi
    )
    _isoquant(plane, tech, output, bounds, plane.t("isoquant.curve", index=1))
    _isocost(plane, before.cost, wage, rent, bounds, plane.t("isocost.line", index=1))
    _isocost(
        plane, after.cost, new_wage, rent, bounds, plane.t("isocost.line_after", index=1), thin=True
    )
    _bundle_marks(plane, tech, before, name=plane.t("isocost.point_names")[0])
    _bundle_marks(plane, tech, after, after=True, name=plane.t("isocost.point_names")[1])
    if along:
        plane.arrow((before.labor, before.capital), (after.labor, after.capital))
    return plane.finish()


def technical_change_canvas(
    before: Technology,
    after: Technology,
    output: float,
    wage: float,
    rent: float,
    bounds: Point,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Technical change: the isoquant of the same ``output`` moves inward (thin ``Q'``) and the
    cheapest bundle falls onto a lower isocost line."""
    first = cost_minimizing_bundle(before, output, wage, rent)
    second = cost_minimizing_bundle(after, output, wage, rent)
    plane = _plane(
        before, bounds, theme=theme, labels=labels, title=title, margin=margin, size=size, dpi=dpi
    )
    _isoquant(plane, before, output, bounds, plane.t("isoquant.curve", index=1))
    _isoquant(plane, after, output, bounds, plane.t("isocost.isoquant_after"), thin=True)
    _isocost(plane, first.cost, wage, rent, bounds, plane.t("isocost.line", index=1))
    _isocost(
        plane, second.cost, wage, rent, bounds, plane.t("isocost.line_after", index=1), thin=True
    )
    _bundle_marks(plane, before, first, name=plane.t("isocost.point_names")[0])
    _bundle_marks(plane, before, second, after=True, name=plane.t("isocost.point_names")[1])
    return plane.finish()


def expansion_path_canvas(
    tech: Technology,
    outputs: Sequence[float],
    wage: float,
    rent: float,
    bounds: Point,
    *,
    titles: tuple[str | None, str | None] = (None, None),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """Above: isoquants with tangent isocost lines and the expansion path through the tangencies;
    below: the long-run total cost ``C`` plotted against output ``Q``."""
    path = expansion_path(tech, tuple(outputs), wage, rent)
    top = _plane(
        tech, bounds, theme=theme, labels=labels, title=titles[0], margin=margin, size=size, dpi=dpi
    )
    for index, (output, bundle) in enumerate(zip(outputs, path, strict=True), start=1):
        _isoquant(top, tech, output, bounds, top.t("isoquant.curve", index=index))
        _isocost(top, bundle.cost, wage, rent, bounds, top.t("isocost.line", index=index))
        top.dot((bundle.labor, bundle.capital))
    top.line(
        [(b.labor, b.capital) for b in path], top.t("isocost.expansion"), role="micro.curve.after"
    )
    ceiling = max(b.cost for b in path)
    bottom = Plane(
        prefix=_PREFIX + ".ltc",
        x_label="Q",
        y_label=top.t("isocost.axis.cost"),
        x_max=max(outputs),
        y_max=ceiling,
        theme=theme,
        labels=labels,
        title=titles[1],
        margin=margin,
        size=size,
        dpi=dpi,
    )
    low = min(outputs) * 0.2
    bottom.line(
        [(0.0, 0.0)]
        + sample(lambda q: cost_minimizing_bundle(tech, q, wage, rent).cost, low, max(outputs), 40),
        bottom.t("isocost.ltc"),
    )
    for index, (output, bundle) in enumerate(zip(outputs, path, strict=True), start=1):
        bottom.point(
            output,
            bundle.cost,
            xtext=bottom.t("longrun.mark.quantity_index", index=index),
            ytext=bottom.t("isocost.line", index=index),
        )
    return CanvasGrid([[top.finish()], [bottom.finish()]])


def fixed_capital_canvas(
    tech: Technology,
    outputs: Sequence[float],
    capital: float,
    wage: float,
    rent: float,
    bounds: Point,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """With capital fixed at ``K_0`` output can only grow along the horizontal line; the
    long-run expansion path through the tangencies is cheaper beyond the design output."""
    plane = _plane(
        tech, bounds, theme=theme, labels=labels, title=title, margin=margin, size=size, dpi=dpi
    )
    path = expansion_path(tech, tuple(outputs), wage, rent)
    for index, output in enumerate(outputs, start=1):
        _isoquant(plane, tech, output, bounds, plane.t("isoquant.curve", index=index))
    plane.thin(((0.0, capital), (plane.x_max, capital)))
    plane.ymark(capital, plane.t("isocost.fixed_capital", symbol=tech.capital_symbol))
    plane.line(
        [(b.labor, b.capital) for b in path], plane.t("isocost.expansion"), role="micro.curve.after"
    )
    for output in outputs:
        labor = tech.labor_for(output, capital)
        if labor is not None and labor <= bounds[0]:
            plane.dot((labor, capital))
    for bundle in path:
        plane.dot((bundle.labor, bundle.capital))
    return plane.finish()


__all__ = [
    "cost_minimization_canvas",
    "expansion_path_canvas",
    "fixed_capital_canvas",
    "input_price_change_canvas",
    "technical_change_canvas",
]
