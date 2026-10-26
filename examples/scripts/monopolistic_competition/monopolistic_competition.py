"""Render monopolistic competition: short-run profit, long-run tangency and excess capacity."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import Session, parser

from micro_viz import (
    CubicCost,
    LinearDemand,
    PlotTheme,
    analyze_costs,
    excess_capacity_grid,
    monopolistic_long_run_canvas,
    monopolistic_short_run_canvas,
    solve_monopolistic_competition,
)


def monopolistic_examples(
    output_dir: Path,
    theme: PlotTheme,
    *,
    cost: CubicCost,
    demand: LinearDemand,
    min_output: float,
    max_output: float,
    samples: int,
    title: str | None = None,
) -> list[Path]:
    """Write the monopolistic-competition figures into ``output_dir``."""
    output_dir.mkdir(parents=True, exist_ok=True)
    unit = analyze_costs(cost, output_range=(min_output, max_output), samples=samples)
    outcome = solve_monopolistic_competition(demand, cost)
    figures = {
        "short_run.svg": monopolistic_short_run_canvas(outcome, unit, theme=theme, title=title),
        "long_run.svg": monopolistic_long_run_canvas(outcome, unit, theme=theme, title=title),
        "excess_capacity.svg": excess_capacity_grid(outcome, unit, theme=theme),
    }
    paths = []
    for name, figure in figures.items():
        figure.save(output_dir / name)
        paths.append(output_dir / name)
    return paths


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument("--cost", default="20:6:-1.5:0.15", help="fixed:linear:quad:cubic")
    args_parser.add_argument("--demand", default="30:2", help="intercept:slope")
    args_parser.add_argument("--min-output", type=float, default=2.0)
    args_parser.add_argument("--max-output", type=float, default=10.0)
    args_parser.add_argument("--samples", type=int, default=221)
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    fixed, linear, quadratic, cubic = (float(part) for part in args.cost.split(":"))
    intercept, slope = (float(part) for part in args.demand.split(":"))
    session = Session(args)
    try:
        monopolistic_examples(
            args.output_dir,
            session.theme,
            cost=CubicCost(fixed, linear, quadratic, cubic),
            demand=LinearDemand(intercept, slope),
            min_output=args.min_output,
            max_output=args.max_output,
            samples=args.samples,
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
