"""Aligned multi-panel production figures."""

from __future__ import annotations

from collections.abc import Mapping

from mosaickit import CanvasGrid, GridLink, GridSpacing

from micro_viz.core.theme import PlotTheme
from micro_viz.firm.production import ProductionAnalysis
from micro_viz.firm.visuals.production.panels import (
    average_marginal_product_canvas,
    total_product_canvas,
)
from micro_viz.visuals.common import FIGURE_DPI, FIGURE_SIZE, MARGIN, resolve_theme


def production_grid(
    result: ProductionAnalysis,
    *,
    titles: tuple[str | None, str | None] = (None, None),
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    x_label: str | None = None,
    x_max: float | None = None,
    margin: float = MARGIN,
    regions: bool = False,
    region_colors: Mapping[str, str] | None = None,
    guides: bool = True,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> CanvasGrid:
    """TP above AP/MP, sharing one input scale and vertically aligned key inputs."""
    selected = resolve_theme(theme)
    horizontal = x_max if x_max is not None else result.input_range[1] * (1 + margin)
    upper = total_product_canvas(
        result,
        title=titles[0],
        marks=False,
        theme=selected,
        labels=labels,
        x_label=x_label,
        x_max=horizontal,
        margin=margin,
        regions=regions,
        region_colors=region_colors,
        guides=guides,
        size=size,
        dpi=dpi,
    )
    lower = average_marginal_product_canvas(
        result,
        title=titles[1],
        theme=selected,
        labels=labels,
        x_label=x_label,
        x_max=horizontal,
        margin=margin,
        regions=regions,
        region_colors=region_colors,
        guides=guides,
        size=size,
        dpi=dpi,
    )
    links: list[GridLink] = []
    if guides:
        function = result.production_function
        corresponding = (
            (
                result.inflection_input,
                function.total_product(result.inflection_input),
                function.marginal_product(result.inflection_input),
            ),
            (
                result.average_product_max_input,
                function.total_product(result.average_product_max_input),
                function.marginal_product(result.average_product_max_input),
            ),
            (
                result.total_product_max_input,
                function.total_product(result.total_product_max_input),
                0.0,
            ),
        )
        links.extend(
            GridLink(0, (variable_input, total), 1, (variable_input, product), role="micro.guide")
            for variable_input, total, product in corresponding
        )
    return CanvasGrid(
        [[upper], [lower]],
        links=links,
        spacing=GridSpacing(row_gap=0.18, outer=0.04),
    )


__all__ = ["production_grid"]
