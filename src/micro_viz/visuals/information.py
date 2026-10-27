"""mosaickit figure builders for asymmetric information."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import Canvas, CanvasGrid

from micro_viz.information.model import (
    BonusSchedule,
    EfficiencyWage,
    LemonsMarket,
    MoralHazard,
    Signaling,
)
from micro_viz.theme import PlotTheme
from micro_viz.visuals.common import FIGURE_DPI, FIGURE_SIZE, MARGIN, Texts, resolve_theme
from micro_viz.visuals.plane import PANEL, Plane, linear

STEPS = 60
"""Points per sampled curve."""


def lemons_market_canvas(
    market: LemonsMarket,
    shares: Sequence[float],
    *,
    titles: Sequence[str | None] | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """One panel per high-quality share: demands for high (``D_H``) and low (``D_L``) quality,
    the sellers' reservation lines ``S_H`` and ``S_L`` and the demand ``D`` of buyers who cannot
    tell them apart. When ``D`` starts below ``S_H`` high quality is driven out."""
    heading = list(titles) if titles is not None else [None] * len(shares)
    top = market.demand_high.intercept
    reach = market.demand_high.quantity_intercept
    cells = []
    for index, share in enumerate(shares, start=1):
        plane = Plane(
            prefix=f"information.lemons{index}",
            x_label="Q",
            y_label="p",
            x_max=reach,
            y_max=top,
            theme=theme,
            labels=labels,
            title=heading[index - 1],
            margin=margin,
            size=size,
            dpi=dpi,
        )
        for name, demand in (("high", market.demand_high), ("low", market.demand_low)):
            plane.thin(
                ((0.0, demand.intercept), (demand.quantity_intercept, 0.0)),
                plane.t(f"information.curve.demand_{name}"),
                at=0.9,
            )
        mixed = market.mixed_demand(share)
        plane.line(
            ((0.0, mixed.intercept), (mixed.quantity_intercept, 0.0)),
            plane.t("information.curve.demand_mix"),
            role="micro.curve.demand",
            at=0.8,
        )
        for name, cost in (("high", market.cost_high), ("low", market.cost_low)):
            end = (top - cost) / market.supply_slope
            plane.line(
                linear(cost, market.supply_slope, min(end, plane.x_max)),
                plane.t(f"information.curve.supply_{name}"),
            )
        cells.append(plane.finish())
    return CanvasGrid([cells])


def signaling_canvas(
    signaling: Signaling,
    signal: float | None = None,
    *,
    titles: tuple[str | None, str | None] = (None, None),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """Education cost against the wage benefit for the low-ability group (left) and the
    high-ability group (right): at a separating signal ``y*`` only the high group's cost lies
    below the benefit."""
    chosen = signaling.separating_signal if signal is None else signal
    texts = Texts(resolve_theme(theme), labels)
    reach = signaling.high_ceiling * 1.3
    top = signaling.wage_gap * 1.5
    cells = []
    for side, slope, ceiling, title in (
        ("low", signaling.cost_low, signaling.low_ceiling, titles[0]),
        ("high", signaling.cost_high, signaling.high_ceiling, titles[1]),
    ):
        plane = Plane(
            prefix=f"information.signal.{side}",
            x_label=texts("information.axis.signal"),
            y_label=texts("information.axis.money"),
            x_max=reach,
            y_max=top,
            theme=theme,
            labels=labels,
            title=title,
            margin=margin,
            size=size,
            dpi=dpi,
        )
        end = min(reach, top / slope)
        plane.line(
            ((0.0, 0.0), (end, slope * end)),
            plane.t(f"information.curve.cost_{side}"),
            role="micro.curve.demand",
        )
        plane.line(
            ((0.0, signaling.wage_gap), (plane.x_max, signaling.wage_gap)),
            plane.t("information.curve.benefit"),
        )
        plane.point(ceiling, signaling.wage_gap, xtext=plane.t(f"information.mark.ceiling_{side}"))
        plane.guide((chosen, 0.0), (chosen, slope * chosen))
        plane.xmark(chosen, plane.t("information.mark.signal"))
        plane.dot((chosen, slope * chosen))
        cells.append(plane.finish())
    return CanvasGrid([cells])


def moral_hazard_canvas(
    hazard: MoralHazard,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Demand ``D`` against the true marginal cost ``MC`` and the lower price ``MC'`` an insured
    patient faces: use rises from ``Q_e`` to ``Q_i`` and the triangle between is the loss."""
    outcome = hazard.solve()
    demand = hazard.demand
    plane = Plane(
        prefix="information.moral_hazard",
        x_label="Q",
        y_label="p",
        x_max=demand.quantity_intercept,
        y_max=demand.intercept,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    mc, insured = hazard.marginal_cost, hazard.insured_price
    plane.area(
        (
            (outcome.efficient_quantity, mc),
            (outcome.insured_quantity, mc),
            (outcome.insured_quantity, insured),
        ),
        plane.t("information.region.loss"),
        shade="mid",
    )
    plane.line(
        ((0.0, demand.intercept), (demand.quantity_intercept, 0.0)),
        plane.t("information.curve.demand"),
        role="micro.curve.demand",
    )
    plane.line(((0.0, mc), (plane.x_max, mc)), plane.t("information.curve.mc"))
    plane.thin(((0.0, insured), (plane.x_max, insured)), plane.t("information.curve.mc_insured"))
    plane.point(
        outcome.efficient_quantity,
        mc,
        xtext=plane.t("information.mark.efficient"),
        ytext=plane.t("information.mark.mc"),
    )
    plane.point(
        outcome.insured_quantity,
        insured,
        xtext=plane.t("information.mark.insured"),
        ytext=plane.t("information.mark.mc_insured"),
    )
    return plane.finish()


def bonus_schedule_canvas(
    schedule: BonusSchedule,
    capacities: Sequence[float],
    reach: float,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Bonus against the reported plant size ``R`` for each true capacity: every schedule peaks
    where the report equals the capacity, so truthful reporting is incentive compatible."""
    texts = Texts(resolve_theme(theme), labels)
    top = max(schedule.bonus(c, c) for c in capacities) * 1.05
    plane = Plane(
        prefix="information.bonus",
        x_label=texts("information.axis.report"),
        y_label=texts("information.axis.bonus"),
        x_max=reach,
        y_max=top,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    for index, capacity in enumerate(capacities, start=1):
        points = [
            (reach * i / STEPS, schedule.bonus(reach * i / STEPS, capacity))
            for i in range(STEPS + 1)
        ]
        points = [p for p in points if p[1] >= 0] or points
        plane.line(
            points,
            plane.t("information.curve.bonus", index=index),
            role="micro.curve.demand" if index == 1 else "micro.curve.marginal",
            at=0.9,
        )
        best = schedule.best_report(capacity)
        plane.point(
            best,
            schedule.bonus(best, capacity),
            xtext=plane.t("information.mark.capacity", index=index),
        )
    return plane.finish()


def efficiency_wage_canvas(
    model: EfficiencyWage,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Labor demand ``D``, supply ``S`` and the no-shirking constraint ``NSC``: equilibrium is
    where ``NSC`` meets ``D``, at a wage above the competitive one, so ``L_s - L*`` workers are
    unemployed."""
    out = model.solve()
    texts = Texts(resolve_theme(theme), labels)
    top = model.demand_intercept
    reach = model.demand_intercept / model.demand_slope
    plane = Plane(
        prefix="information.efficiency",
        x_label=texts("information.axis.labor"),
        y_label=texts("information.axis.wage"),
        x_max=reach,
        y_max=top,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )
    plane.line(
        ((0.0, top), (reach, 0.0)),
        plane.t("information.curve.labor_demand"),
        role="micro.curve.demand",
    )
    supply_end = min(reach, (top - model.supply_intercept) / model.supply_slope)
    plane.line(
        linear(model.supply_intercept, model.supply_slope, supply_end),
        plane.t("information.curve.labor_supply"),
    )
    nsc_end = min(reach, (top - model.shirk_intercept) / model.shirk_slope)
    plane.line(
        linear(model.shirk_intercept, model.shirk_slope, nsc_end),
        plane.t("information.curve.nsc"),
        role="micro.curve.marginal",
    )
    plane.point(
        out.employment,
        out.wage,
        xtext=plane.t("information.mark.employment"),
        ytext=plane.t("information.mark.wage"),
    )
    plane.guide((out.labor_supplied, 0.0), (out.labor_supplied, out.wage))
    plane.guide((out.employment, out.wage), (out.labor_supplied, out.wage))
    plane.dot((out.labor_supplied, out.wage))
    plane.xmark(out.labor_supplied, plane.t("information.mark.supplied"))
    plane.dot((out.competitive_employment, out.competitive_wage))
    return plane.finish()


__all__ = [
    "bonus_schedule_canvas",
    "efficiency_wage_canvas",
    "lemons_market_canvas",
    "moral_hazard_canvas",
    "signaling_canvas",
]
