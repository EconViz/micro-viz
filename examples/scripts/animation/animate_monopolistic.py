"""Animate entry into monopolistic competition: demand shifts in until profit is zero."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import Session, parser

from micro_viz import (
    CubicCost,
    LinearDemand,
    Monopolist,
    PlotTheme,
    analyze_costs,
    monopoly_canvas,
    solve_monopolistic_competition,
)
from micro_viz.animation import save_gif, save_svg


def entry_animation(
    output_dir: Path,
    theme: PlotTheme,
    *,
    cost: CubicCost,
    demand: LinearDemand,
    steps: int,
    min_output: float,
    max_output: float,
    gif: bool,
    title: str | None = None,
) -> list[Path]:
    """Write the animated SVG (and a GIF when ``gif``) of demand shifting in with entry."""
    unit = analyze_costs(cost, output_range=(min_output, max_output))
    final = solve_monopolistic_competition(demand, cost).long_run_demand
    intercepts = [
        demand.intercept + (final.intercept - demand.intercept) * index / steps
        for index in range(steps + 1)
    ]
    reach = (demand.quantity_intercept, max_output)

    def frame(intercept: float):  # type: ignore[no-untyped-def]
        outcome = Monopolist(LinearDemand(intercept, demand.slope), cost).solve()
        return monopoly_canvas(
            outcome,
            unit,
            profit=True,
            theme=theme,
            title=title,
            x_max=max(reach) * 1.1,
            y_range=(0.0, demand.intercept * 1.1),
        )

    written = [save_svg(frame, intercepts, output_dir / "monopolistic_entry_animated.svg")]
    if gif:
        written.append(save_gif(frame, intercepts, output_dir / "monopolistic_entry_animated.gif"))
    return written


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument("--cost", default="20:6:-1.5:0.15", help="fixed:linear:quad:cubic")
    args_parser.add_argument("--demand", default="30:2", help="intercept:slope")
    args_parser.add_argument("--min-output", type=float, default=2.0)
    args_parser.add_argument("--max-output", type=float, default=10.0)
    args_parser.add_argument("--steps", type=int, default=6)
    args_parser.add_argument("--gif", action="store_true", help="also write a GIF")
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    fixed, linear, quadratic, cubic = (float(part) for part in args.cost.split(":"))
    intercept, slope = (float(part) for part in args.demand.split(":"))
    session = Session(args)
    try:
        entry_animation(
            args.output_dir,
            session.theme,
            cost=CubicCost(fixed, linear, quadratic, cubic),
            demand=LinearDemand(intercept, slope),
            steps=args.steps,
            min_output=args.min_output,
            max_output=args.max_output,
            gif=args.gif,
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
