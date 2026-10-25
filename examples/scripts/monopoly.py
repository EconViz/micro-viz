"""Render monopoly: MR = MC, profit, deadweight loss, tax, demand change, plants, Lerner index."""

from __future__ import annotations

from pathlib import Path

from common import Session, parser

from micro_viz import (
    CubicCost,
    LinearDemand,
    Monopolist,
    MultiplantMonopoly,
    PlotTheme,
    analyze_costs,
    firm_demand_canvas,
    lerner_markup_canvas,
    monopoly_canvas,
    monopoly_demand_shift_canvas,
    monopoly_dwl_canvas,
    monopoly_tax_canvas,
    monopoly_totals_canvas,
    monopoly_totals_grid,
    multiplant_canvas,
)


def cost_from(text: str) -> CubicCost:
    """A cubic cost from ``fixed:linear:quadratic:cubic``."""
    fixed, linear, quadratic, cubic = (float(part) for part in text.split(":"))
    return CubicCost(fixed, linear, quadratic, cubic)


def demand_from(text: str) -> LinearDemand:
    """A linear demand from ``intercept:slope``."""
    intercept, slope = (float(part) for part in text.split(":"))
    return LinearDemand(intercept, slope)


def monopoly_examples(
    output_dir: Path,
    theme: PlotTheme,
    *,
    demand: LinearDemand,
    shifted: LinearDemand,
    rotated: LinearDemand,
    cost: CubicCost,
    plants: tuple[CubicCost, CubicCost],
    plant_demand: LinearDemand,
    elastic: LinearDemand,
    inelastic: LinearDemand,
    firm_demand: LinearDemand,
    market_price: float,
    tax: float,
    lost_profit: tuple[float, float],
    min_output: float,
    max_output: float,
    samples: int,
    title: str | None = None,
) -> list[Path]:
    """Write the monopoly figures into ``output_dir`` and return their paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    window = (min_output, max_output)

    unit = analyze_costs(cost, output_range=window, samples=samples)
    firm = Monopolist(demand, cost)
    outcome = firm.solve()
    taxed_cost = cost.with_unit_tax(tax)
    taxed = analyze_costs(taxed_cost, output_range=window, samples=samples)
    taxed_outcome = Monopolist(demand, taxed_cost).solve()
    shifted_outcome = firm.with_demand(shifted).solve()
    rotated_outcome = firm.with_demand(rotated).solve()
    multi = MultiplantMonopoly(plant_demand, plants)
    elastic_outcome = Monopolist(elastic, cost).solve()
    inelastic_outcome = Monopolist(inelastic, cost).solve()
    figures = {
        "monopoly.svg": monopoly_canvas(outcome, unit, curves=("mc",), title=title, theme=theme),
        "monopoly_lost_profit.svg": monopoly_canvas(
            outcome, unit, curves=("mc",), lost_profit=lost_profit, title=title, theme=theme
        ),
        "monopoly_profit.svg": monopoly_canvas(
            outcome, unit, profit=True, title=title, theme=theme
        ),
        "monopoly_totals.svg": monopoly_totals_canvas(
            outcome, output_range=window, title=title, theme=theme
        ),
        "monopoly_totals_grid.svg": monopoly_totals_grid(outcome, unit, theme=theme),
        "monopoly_dwl.svg": monopoly_dwl_canvas(outcome, unit, title=title, theme=theme),
        "monopoly_tax.svg": monopoly_tax_canvas(
            outcome, taxed_outcome, unit, taxed, title=title, theme=theme
        ),
        "monopoly_demand_shift.svg": monopoly_demand_shift_canvas(
            outcome, shifted_outcome, unit, title=title, theme=theme
        ),
        "monopoly_demand_rotate.svg": monopoly_demand_shift_canvas(
            outcome, rotated_outcome, unit, rotate=True, title=title, theme=theme
        ),
        "multiplant.svg": multiplant_canvas(multi, multi.solve(), theme=theme),
        "lerner_markup.svg": lerner_markup_canvas(
            (elastic_outcome, inelastic_outcome), (unit, unit), theme=theme
        ),
        "firm_demand.svg": firm_demand_canvas(demand, firm_demand, market_price, theme=theme),
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
    args_parser.add_argument("--shifted-demand", default="36:2", help="intercept:slope")
    args_parser.add_argument("--rotated-demand", default="30:1.5", help="intercept:slope")
    args_parser.add_argument("--plant-1", default="10:4:-1:0.12")
    args_parser.add_argument("--plant-2", default="10:8:-1.5:0.15")
    args_parser.add_argument("--plant-demand", default="30:0.8")
    args_parser.add_argument("--elastic-demand", default="20:0.5")
    args_parser.add_argument("--inelastic-demand", default="40:3")
    args_parser.add_argument("--firm-demand", default="26:2")
    args_parser.add_argument("--market-price", type=float, default=18.0)
    args_parser.add_argument("--tax", type=float, default=4.0)
    args_parser.add_argument("--lost-profit", type=float, nargs=2, default=[4.5, 8.0])
    args_parser.add_argument("--min-output", type=float, default=2.0)
    args_parser.add_argument("--max-output", type=float, default=10.0)
    args_parser.add_argument("--samples", type=int, default=221)
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    session = Session(args)
    try:
        monopoly_examples(
            args.output_dir,
            session.theme,
            demand=demand_from(args.demand),
            shifted=demand_from(args.shifted_demand),
            rotated=demand_from(args.rotated_demand),
            cost=cost_from(args.cost),
            plants=(cost_from(args.plant_1), cost_from(args.plant_2)),
            plant_demand=demand_from(args.plant_demand),
            elastic=demand_from(args.elastic_demand),
            inelastic=demand_from(args.inelastic_demand),
            firm_demand=demand_from(args.firm_demand),
            market_price=args.market_price,
            tax=args.tax,
            lost_profit=(args.lost_profit[0], args.lost_profit[1]),
            min_output=args.min_output,
            max_output=args.max_output,
            samples=args.samples,
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
