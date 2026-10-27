"""Render the four short-run competitive-firm cases and their demand-increase responses."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import Session, parser

from micro_viz import (
    CubicCost,
    PlotTheme,
    analyze_costs,
    competitive_demand_increase_grid,
    competitive_firm_supply_grid,
    competitive_industry_supply_grid,
    competitive_market_supply_equilibrium_grid,
    competitive_short_run_grid,
)


def competitive_market_examples(output_dir: Path, theme: PlotTheme) -> list[Path]:
    """Write the four initial states and four demand-increase responses."""
    output_dir.mkdir(parents=True, exist_ok=True)
    costs = (
        CubicCost(9.6, 15.6, -3.0, 0.3),
        CubicCost(21.6, 15.6, -3.0, 0.3),
        CubicCost(33.6, 15.6, -3.0, 0.3),
        CubicCost(24.0, 21.6, -3.0, 0.3),
    )
    paths: list[Path] = []
    for index, cost in enumerate(costs, start=1):
        analysis = analyze_costs(cost, output_range=(2.0, 8.2), samples=241)
        figures = (
            (
                f"type_{index}_short_run.png",
                competitive_short_run_grid(
                    analysis,
                    12.0,
                    curve_index=index,
                    theme=theme,
                    size=(5.0, 4.2),
                ),
            ),
            (
                f"type_{index}_demand_increase.png",
                competitive_demand_increase_grid(
                    analysis,
                    (12.0, 16.0),
                    curve_index=index,
                    theme=theme,
                    size=(5.0, 4.2),
                ),
            ),
        )
        for name, figure in figures:
            path = output_dir / name
            figure.save(path)
            paths.append(path)
    supply_cost = CubicCost(186.0, 40.0, -10.0, 1.0)
    supply_analysis = analyze_costs(supply_cost, output_range=(2.4, 8.2), samples=241)
    supply_figures = (
        (
            "firm_short_run_supply.png",
            competitive_firm_supply_grid(
                supply_analysis,
                (10.0, 22.0, 32.0),
                theme=theme,
                size=(5.0, 4.2),
            ),
        ),
        (
            "industry_short_run_supply.png",
            competitive_industry_supply_grid(
                supply_analysis,
                20,
                22.0,
                theme=theme,
                size=(5.0, 4.2),
            ),
        ),
        (
            "market_supply_equilibrium.png",
            competitive_market_supply_equilibrium_grid(
                supply_analysis,
                20,
                22.0,
                theme=theme,
                size=(5.0, 4.2),
            ),
        ),
    )
    for name, figure in supply_figures:
        path = output_dir / name
        figure.save(path)
        paths.append(path)
    return paths


def main() -> None:
    args = parser(__doc__).parse_args()
    session = Session(args)
    try:
        competitive_market_examples(args.output_dir, session.theme)
    finally:
        session.close()


if __name__ == "__main__":
    main()
