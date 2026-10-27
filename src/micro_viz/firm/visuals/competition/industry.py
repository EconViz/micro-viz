"""Industry supply and the market beside the firm."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import Canvas, CanvasGrid, GridLink

from micro_viz.core.theme import PlotTheme
from micro_viz.firm.competition import (
    IndustrySupply,
    LinearDemand,
)
from micro_viz.firm.visuals.competition._base import (
    PANEL_SIZE,
    SAMPLES,
    _finish,
    _level_mark,
    _output_marks,
    _start,
)
from micro_viz.visuals.common import (
    FIGURE_DPI,
    FIGURE_SIZE,
    MARGIN,
    Range,
    curve,
    curve_name,
    dot,
    drop_line,
    guide,
    pad_range,
    resolve_theme,
)


def industry_supply_canvas(
    industry: IndustrySupply,
    *,
    prices: Sequence[float] = (),
    price_max: float,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    x_label: str | None = None,
    y_label: str | None = None,
    x_max: float | None = None,
    y_range: Range | None = None,
    margin: float = MARGIN,
    samples: int = SAMPLES,
    firm_curves: bool = True,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Industry supply as the horizontal sum of the firms' supply curves.

    Each firm's supply (MC above its lowest AVC) is a dashed curve; the industry supply, the
    sum of the firms' quantities at each price, is solid and steps where a firm enters at its
    shutdown price. Each price in ``prices`` is a dashed line to the industry quantity.
    ``firm_curves=False`` leaves out the firms' curves (see :func:`industry_supply_panels` for
    the firms side by side).
    """
    symbol = industry.firms[0].output_symbol
    total = industry.curve(price_max, samples=samples)
    quantity_top = max(point[0] for point in total)
    start = _start(
        theme=theme,
        labels=labels,
        x_symbol=symbol,
        x_label=x_label,
        y_label=y_label,
        y_text_id="competition.axis.price",
        x_max=x_max if x_max is not None else quantity_top * (1 + margin),
        y_range=y_range or pad_range(0.0, price_max, margin),
        title=title,
        size=size,
        dpi=dpi,
    )
    texts = start.texts
    from micro_viz.firm.competition import FirmSupply

    for index, firm in enumerate(industry.firms if firm_curves else (), start=1):
        points = FirmSupply(firm).curve(price_max, samples=samples)
        path = curve(
            tuple(points),
            layer_id=f"micro.competition.firm.{index}",
            role="micro.curve.fixed",
        )
        start.layers.extend((path, curve_name(path, texts("competition.firm", index=index))))
    supply = curve(total, layer_id="micro.competition.industry", role="micro.curve.marginal")
    start.layers.extend((supply, curve_name(supply, texts("competition.supply"))))
    for index, price in enumerate(prices, start=1):
        quantity = industry.quantity(price)
        _level_mark(
            start, price, "competition.mark.price_index", mark_id=f"price.{index}", index=index
        )
        if quantity > 0:
            _output_marks(
                start,
                symbol,
                quantity,
                price,
                mark_id=f"output.{index}",
                key="competition.mark.output_index",
                index=index,
            )
    return _finish(start)


def industry_supply_panels(
    industry: IndustrySupply,
    *,
    prices: Sequence[float],
    price_max: float,
    titles: tuple[str | None, ...] = (),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    samples: int = SAMPLES,
    size: tuple[float, float] = PANEL_SIZE,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """The firms' supply curves side by side and the industry supply that sums them.

    Each firm panel shows its MC above the lowest AVC; each price in ``prices`` is a dashed line
    across every panel (joined by grid links over the gaps) to the firm's quantity and, in the
    last panel, to the industry quantity, the sum of the firms' quantities.
    """
    from micro_viz.firm.competition import FirmSupply

    selected = resolve_theme(theme)
    symbol = industry.firms[0].output_symbol
    supplies = [FirmSupply(firm) for firm in industry.firms]
    firm_top = max(supply.quantity(price_max) for supply in supplies) * (1 + margin)
    total = industry.curve(price_max, samples=samples)
    total_top = max(point[0] for point in total) * (1 + margin)
    height = pad_range(0.0, price_max, margin)
    names = (*titles, *([None] * (len(supplies) + 1 - len(titles))))
    cells: list[Canvas] = []
    for index, supply in enumerate(supplies, start=1):
        panel = _start(
            theme=selected,
            labels=labels,
            x_symbol=symbol,
            x_label=None,
            y_label=None,
            y_text_id="competition.axis.price",
            x_max=firm_top,
            y_range=height,
            title=names[index - 1],
            size=size,
            dpi=dpi,
        )
        path = curve(
            tuple(supply.curve(price_max, samples=samples)),
            layer_id=f"micro.competition.firm.{index}",
            role="micro.curve.marginal",
        )
        panel.layers.extend((path, curve_name(path, panel.texts("competition.firm", index=index))))
        for number, price in enumerate(prices, start=1):
            if index == 1:
                _level_mark(
                    panel,
                    price,
                    "competition.mark.price_index",
                    mark_id=f"price.{number}",
                    dotted=False,
                    index=number,
                )
            panel.layers.append(
                guide(
                    (0.0, price),
                    (panel.x_axis[1], price),
                    layer_id=f"micro.competition.guide.firm.{index}.price.{number}",
                )
            )
            quantity = supply.quantity(price)
            if quantity > 0:
                panel.layers.append(
                    drop_line(
                        quantity, price, layer_id=f"micro.competition.guide.firm.{index}.q.{number}"
                    )
                )
                panel.layers.append(
                    dot(
                        (quantity, price), layer_id=f"micro.competition.point.firm.{index}.{number}"
                    )
                )
        cells.append(_finish(panel))
    market = _start(
        theme=selected,
        labels=labels,
        x_symbol=panel.texts("competition.axis.industry_output"),
        x_label=None,
        y_label=None,
        y_text_id="competition.axis.price",
        x_max=total_top,
        y_range=height,
        title=names[len(supplies)],
        size=size,
        dpi=dpi,
    )
    supply_path = curve(total, layer_id="micro.competition.industry", role="micro.curve.marginal")
    market.layers.extend((supply_path, curve_name(supply_path, market.texts("competition.supply"))))
    for number, price in enumerate(prices, start=1):
        quantity = industry.quantity(price)
        market.layers.append(
            guide(
                (0.0, price),
                (quantity, price),
                layer_id=f"micro.competition.guide.price.{number}",
            )
        )
        if quantity > 0:
            _output_marks(
                market,
                "Q",
                quantity,
                price,
                mark_id=f"output.{number}",
                key="competition.mark.output_index",
                index=number,
            )
    cells.append(_finish(market))
    links = [
        GridLink(
            cell,
            (firm_top if cell < len(supplies) else total_top, price),
            cell + 1,
            (0.0, price),
            role="micro.guide",
        )
        for cell in range(len(supplies))
        for price in prices
    ]
    return CanvasGrid([cells], links=links)


def market_and_firm_canvas(
    demand: LinearDemand,
    price: float,
    *,
    firm_output_max: float,
    titles: tuple[str | None, str | None] = (None, None),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = PANEL_SIZE,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """The firm beside the market: horizontal demand ``d`` at the market price, and the
    downward market demand ``D``, with a dashed link carrying the price across.

    The firm panel's output axis runs to ``firm_output_max``; the market quantity is where
    the price meets ``D``.
    """
    selected = resolve_theme(theme)
    market_quantity = demand.quantity(price)
    firm = _start(
        theme=selected,
        labels=labels,
        x_symbol="q",
        x_label=None,
        y_label=None,
        y_text_id="competition.axis.price",
        x_max=firm_output_max,
        y_range=pad_range(0.0, demand.intercept, margin),
        title=titles[0],
        size=size,
        dpi=dpi,
    )
    line = curve(
        ((0.0, price), (firm_output_max, price)),
        layer_id="micro.competition.firm_demand",
        role="micro.curve.price",
    )
    firm.layers.extend((line, curve_name(line, firm.texts("competition.demand_firm"))))
    _level_mark(firm, price, "competition.mark.price", mark_id="price", dotted=False)
    market = _start(
        theme=selected,
        labels=labels,
        x_symbol=firm.texts("competition.axis.industry_output"),
        x_label=None,
        y_label=None,
        y_text_id="competition.axis.price",
        x_max=demand.quantity_intercept * (1 + margin),
        y_range=pad_range(0.0, demand.intercept, margin),
        title=titles[1],
        size=size,
        dpi=dpi,
    )
    curve_d = curve(
        ((0.0, demand.intercept), (demand.quantity_intercept, 0.0)),
        layer_id="micro.competition.market_demand",
        role="micro.curve.average",
    )
    market.layers.extend(
        (curve_d, curve_name(curve_d, market.texts("competition.demand_industry")))
    )
    market.layers.append(
        guide(
            (0.0, price), (market_quantity, price), layer_id="micro.competition.guide.market_price"
        )
    )
    _output_marks(
        market,
        "Q",
        market_quantity,
        price,
        mark_id="market_output",
        key="competition.mark.industry_output",
    )
    upper = _finish(firm)
    lower = _finish(market)
    link = GridLink(0, (firm_output_max, price), 1, (0.0, price), role="micro.guide")
    return CanvasGrid([[upper, lower]], links=[link])
