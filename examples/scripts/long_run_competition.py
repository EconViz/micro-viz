"""Render long-run competition: the firm at the long-run price, entry, rent and industry supply."""

from __future__ import annotations

from pathlib import Path

from common import Session, parser

from micro_viz import (
    CubicCost,
    IndustryEntry,
    LinearDemand,
    PlantFamily,
    PlotTheme,
    analyze_costs,
    constant_cost_canvas,
    entry_canvas,
    increasing_cost_canvas,
    long_run_firm_canvas,
    rent_canvas,
)


def cost_from(text: str) -> CubicCost:
    """A cubic cost from ``fixed:linear:quadratic:cubic``."""
    fixed, linear, quadratic, cubic = (float(part) for part in text.split(":"))
    return CubicCost(fixed, linear, quadratic, cubic)


def demand_from(text: str) -> LinearDemand:
    """A linear demand from ``intercept:slope``."""
    intercept, slope = (float(part) for part in text.split(":"))
    return LinearDemand(intercept, slope)


def competition_examples(
    output_dir: Path,
    theme: PlotTheme,
    *,
    family: PlantFamily,
    long_run_price: float,
    family_output_max: float,
    cost: CubicCost,
    advantaged: CubicCost,
    demand: LinearDemand,
    higher_demand: LinearDemand,
    firms: float,
    cost_shift: float,
    min_output: float,
    max_output: float,
    title: str | None = None,
) -> list[Path]:
    """Write the long-run competition figures into ``output_dir``."""
    output_dir.mkdir(parents=True, exist_ok=True)
    window = (min_output, max_output)
    industry = IndustryEntry(demand, cost)
    unit = analyze_costs(cost, output_range=window)
    figures = {
        "long_run_firm.svg": long_run_firm_canvas(
            family, long_run_price, family_output_max, theme=theme, title=title
        ),
        "entry.svg": entry_canvas(industry, firms, unit, theme=theme),
        "economic_rent.svg": rent_canvas(
            industry,
            advantaged,
            unit,
            analyze_costs(advantaged, output_range=window),
            theme=theme,
        ),
        "constant_cost.svg": constant_cost_canvas(industry, higher_demand, unit, theme=theme),
        "increasing_cost.svg": increasing_cost_canvas(
            industry, higher_demand, cost_shift, unit, theme=theme
        ),
    }
    paths = []
    for name, figure in figures.items():
        figure.save(output_dir / name)
        paths.append(output_dir / name)
    return paths


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument("--family", type=float, nargs=4, default=[10.0, 4.0, 1.0, 0.6])
    args_parser.add_argument("--long-run-price", type=float, default=7.0)
    args_parser.add_argument("--family-output-max", type=float, default=18.0)
    args_parser.add_argument("--cost", default="50:24:-6:0.6", help="fixed:linear:quad:cubic")
    args_parser.add_argument("--advantaged-cost", default="20:24:-6:0.6")
    args_parser.add_argument("--demand", default="40:0.04", help="intercept:slope")
    args_parser.add_argument("--higher-demand", default="46:0.04")
    args_parser.add_argument("--firms", type=float, default=50.0)
    args_parser.add_argument("--cost-shift", type=float, default=0.02)
    args_parser.add_argument("--min-output", type=float, default=2.0)
    args_parser.add_argument("--max-output", type=float, default=12.0)
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    session = Session(args)
    try:
        competition_examples(
            args.output_dir,
            session.theme,
            family=PlantFamily(*args.family),
            long_run_price=args.long_run_price,
            family_output_max=args.family_output_max,
            cost=cost_from(args.cost),
            advantaged=cost_from(args.advantaged_cost),
            demand=demand_from(args.demand),
            higher_demand=demand_from(args.higher_demand),
            firms=args.firms,
            cost_shift=args.cost_shift,
            min_output=args.min_output,
            max_output=args.max_output,
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
