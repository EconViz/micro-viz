"""Shared demand, cost and mark helpers of the monopoly figures."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import (
    RegionLabelLayer,
)

from micro_viz.costs import CostAnalysis
from micro_viz.demand import Demand, DemandLike
from micro_viz.theme import PlotTheme
from micro_viz.visuals.common import (
    Point,
    Range,
    axis_mark,
    curve,
    curve_name,
    drop_line,
    guide,
    pad_range,
)
from micro_viz.visuals.competition import (
    _level_mark,
    _Start,
    _start,
)
from micro_viz.visuals.costs import _unit_points

_PREFIX = "micro.monopoly"


CURVE_SAMPLES = 81
"""Points drawn along a demand curve that is not a straight line."""


def _spread(reach: float) -> list[float]:
    return [reach * i / (CURVE_SAMPLES - 1) for i in range(CURVE_SAMPLES)]


def _demand_points(demand: DemandLike) -> tuple[Point, ...]:
    if isinstance(demand, Demand):
        return tuple((q, max(0.0, demand.price(q))) for q in _spread(demand.quantity_intercept))
    return ((0.0, demand.intercept), (demand.quantity_intercept, 0.0))


def _mr_points(demand: DemandLike) -> tuple[Point, ...]:
    if isinstance(demand, Demand):
        points = [(q, demand.marginal_revenue(q)) for q in _spread(demand.quantity_intercept)]
        return tuple(point for point in points if point[1] >= 0) or tuple(points[:2])
    return ((0.0, demand.intercept), (demand.quantity_intercept / 2, 0.0))


def _begin(
    demand: DemandLike,
    analysis: CostAnalysis | None,
    *,
    theme: PlotTheme | None,
    labels: Mapping[str, str] | None,
    x_label: str | None,
    y_label: str | None,
    x_max: float | None,
    y_range: Range | None,
    margin: float,
    title: str | None,
    size: tuple[float, float],
    dpi: int,
    symbol: str | None = None,
) -> _Start:
    """The axes of a monopoly figure: price up to the demand intercept."""
    reach = demand.quantity_intercept
    if analysis is not None:
        reach = max(reach, analysis.output_range[1])
    return _start(
        theme=theme,
        labels=labels,
        x_symbol=symbol or (analysis.cost.output_symbol if analysis is not None else "Q"),
        x_label=x_label,
        y_label=y_label,
        y_text_id="competition.axis.price",
        x_max=x_max if x_max is not None else reach * (1 + margin),
        y_range=y_range or pad_range(0.0, demand.intercept, margin),
        title=title,
        size=size,
        dpi=dpi,
    )


def _demand_curves(
    start: _Start,
    demand: DemandLike,
    *,
    key: str = "monopoly.demand",
    mr_key: str = "monopoly.mr",
    suffix: str = "",
    role: str = "micro.curve.demand",
    mr_role: str = "micro.curve.marginal_revenue",
    mr: bool = True,
    along: float = 0.0,
    model: object | None = None,
) -> None:
    line = curve(
        _demand_points(demand), layer_id=f"{_PREFIX}.demand{suffix}", role=role, model=model
    )
    start.layers.extend((line, curve_name(line, start.texts(key), at=along)))
    if mr:
        marginal = curve(
            _mr_points(demand), layer_id=f"{_PREFIX}.mr{suffix}", role=mr_role, model=model
        )
        start.layers.extend((marginal, curve_name(marginal, start.texts(mr_key), at=0.82)))


def _cost_curves(
    start: _Start,
    analysis: CostAnalysis,
    names: Sequence[str],
    *,
    role: str | None = None,
    key_suffix: str = "",
    suffix: str = "",
) -> None:
    styles = {
        "mc": ("micro.curve.marginal", "monopoly.mc"),
        "atc": ("micro.curve.average", "monopoly.atc"),
    }
    for name in names:
        base_role, key = styles[name]
        path = curve(
            _unit_points(analysis, name),
            layer_id=f"{_PREFIX}.{name}{suffix}",
            role=role or base_role,
            model=analysis,
        )
        start.layers.extend((path, curve_name(path, start.texts(key + key_suffix))))


def _point_marks(
    start: _Start,
    symbol: str,
    quantity: float,
    price: float,
    *,
    mark_id: str,
    output_key: str = "monopoly.mark.output",
    price_key: str = "monopoly.mark.price",
    output_mark: bool = True,
) -> None:
    """Dashed guides from the point ``(quantity, price)`` to both axes with their names."""
    start.layers.append(drop_line(quantity, price, layer_id=f"{_PREFIX}.guide.{mark_id}.output"))
    if output_mark:
        start.layers.append(
            axis_mark(
                "x",
                quantity,
                start.texts(output_key, output=symbol),
                layer_id=f"{_PREFIX}.mark.{mark_id}",
            )
        )
    _level_mark(start, price, price_key, mark_id=mark_id, dotted=False)
    start.layers.append(
        guide((0.0, price), (quantity, price), layer_id=f"{_PREFIX}.guide.{mark_id}.price")
    )


def _region_label(start: _Start, layer_id: str, key: str) -> None:
    start.layers.append(
        RegionLabelLayer(
            layer_id,
            start.texts(key),
            id=f"{layer_id}.label",
            role="micro.annotation",
            z_index=8,
        )
    )


def _mc_path(analysis: CostAnalysis, low: float, high: float) -> list[Point]:
    cost = analysis.cost
    steps = 40
    return [
        (q, cost.marginal_cost(q))
        for q in (low + (high - low) * index / steps for index in range(steps + 1))
    ]
