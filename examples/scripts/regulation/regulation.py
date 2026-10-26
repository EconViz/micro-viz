"""Render the regulation of a monopoly: a price ceiling and natural-monopoly pricing."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import Session, parser

from micro_viz import (
    CostSegment,
    CubicCost,
    LinearDemand,
    Monopolist,
    PiecewiseCost,
    PlotTheme,
    analyze_costs,
    natural_monopoly_canvas,
    natural_monopoly_pricing,
    price_ceiling_canvas,
    price_ceiling_outcome,
)


def regulation_examples(
    output_dir: Path,
    theme: PlotTheme,
    *,
    cost: CubicCost,
    demand: LinearDemand,
    ceiling: float,
    natural_demand: LinearDemand,
    fixed_cost: float,
    marginal_cost: float,
    min_output: float,
    max_output: float,
    samples: int,
    title: str | None = None,
) -> list[Path]:
    """Write the regulation figures into ``output_dir`` and return their paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    unit = analyze_costs(cost, output_range=(min_output, max_output), samples=samples)
    capped = price_ceiling_outcome(Monopolist(demand, cost), ceiling)
    natural_cost = PiecewiseCost(
        (CostSegment(natural_demand.quantity_intercept * 1.05, marginal_cost),),
        fixed_cost=fixed_cost,
    )
    natural = analyze_costs(
        natural_cost, output_range=(min_output, natural_demand.quantity_intercept), samples=samples
    )
    pricing = natural_monopoly_pricing(Monopolist(natural_demand, natural_cost))
    figures = {
        "price_ceiling.svg": price_ceiling_canvas(capped, unit, theme=theme, title=title),
        "natural_monopoly.svg": natural_monopoly_canvas(pricing, natural, theme=theme, title=title),
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
    args_parser.add_argument("--ceiling", type=float, default=12.0)
    args_parser.add_argument("--natural-demand", default="30:1", help="intercept:slope")
    args_parser.add_argument("--fixed-cost", type=float, default=120.0)
    args_parser.add_argument("--marginal-cost", type=float, default=4.0)
    args_parser.add_argument("--min-output", type=float, default=2.0)
    args_parser.add_argument("--max-output", type=float, default=10.0)
    args_parser.add_argument("--samples", type=int, default=221)
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    fixed, linear, quadratic, cubic = (float(part) for part in args.cost.split(":"))
    intercept, slope = (float(part) for part in args.demand.split(":"))
    nat_intercept, nat_slope = (float(part) for part in args.natural_demand.split(":"))
    session = Session(args)
    try:
        regulation_examples(
            args.output_dir,
            session.theme,
            cost=CubicCost(fixed, linear, quadratic, cubic),
            demand=LinearDemand(intercept, slope),
            ceiling=args.ceiling,
            natural_demand=LinearDemand(nat_intercept, nat_slope),
            fixed_cost=args.fixed_cost,
            marginal_cost=args.marginal_cost,
            min_output=args.min_output,
            max_output=args.max_output,
            samples=args.samples,
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
