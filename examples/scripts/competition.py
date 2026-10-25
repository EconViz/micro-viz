"""Render short-run perfect competition: firm decision, supply, surplus, shifts, industry."""

from __future__ import annotations

from pathlib import Path

from common import Session, parser

from micro_viz import (
    CubicCost,
    IndustrySupply,
    LinearDemand,
    PlotTheme,
    analyze_costs,
    analyze_revenue_cost,
    competitive_firm_canvas,
    cost_shift_canvas,
    firm_supply_canvas,
    industry_supply_canvas,
    market_and_firm_canvas,
    producer_surplus_canvas,
    revenue_cost_profit_canvas,
    solve_competitive_firm,
)

FIRMS = "50:24:-6:0.6 50:30:-6:0.6 50:36:-6:0.6"
"""Preset: three firms ``fixed:linear:quadratic:cubic`` with different lowest AVC."""


def parse_firms(text: str) -> tuple[CubicCost, ...]:
    """Cubic cost functions from ``fixed:linear:quadratic:cubic`` items separated by spaces."""
    costs = []
    for item in text.split():
        fixed, linear, quadratic, cubic = (float(part) for part in item.split(":"))
        costs.append(CubicCost(fixed, linear, quadratic, cubic))
    return tuple(costs)


def competition_examples(
    output_dir: Path,
    theme: PlotTheme,
    *,
    cost: CubicCost,
    profit_price: float,
    loss_price: float,
    shutdown_price: float,
    lost_profit: tuple[float, float],
    supply_prices: tuple[float, float],
    tax: float,
    firms: tuple[CubicCost, ...],
    industry_prices: tuple[float, ...],
    demand: LinearDemand,
    market_price: float,
    min_output: float,
    max_output: float,
    samples: int,
    title: str | None = None,
) -> list[Path]:
    """Write the competition figures into ``output_dir`` and return their paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    unit = analyze_costs(cost, output_range=(min_output, max_output), samples=samples)
    taxed_cost = cost.with_unit_tax(tax)
    taxed = analyze_costs(taxed_cost, output_range=(min_output, max_output), samples=samples)
    figures = {
        "revenue_cost_profit.svg": revenue_cost_profit_canvas(
            analyze_revenue_cost(
                cost, profit_price, output_range=(0.0, max_output), samples=samples
            ),
            theme=theme,
            title=title,
        ),
        "market_and_firm.svg": market_and_firm_canvas(
            demand,
            market_price,
            firm_output_max=max_output,
            theme=theme,
            titles=(title, None),
        ),
        "firm_profit.svg": competitive_firm_canvas(
            unit, solve_competitive_firm(cost, profit_price), theme=theme, title=title
        ),
        "firm_lost_profit.svg": competitive_firm_canvas(
            unit,
            solve_competitive_firm(cost, profit_price),
            lost_profit=lost_profit,
            theme=theme,
            title=title,
        ),
        "firm_loss.svg": competitive_firm_canvas(
            unit, solve_competitive_firm(cost, loss_price), theme=theme, title=title
        ),
        "firm_shutdown.svg": competitive_firm_canvas(
            unit, solve_competitive_firm(cost, shutdown_price), theme=theme, title=title
        ),
        "firm_supply.svg": firm_supply_canvas(unit, prices=supply_prices, theme=theme, title=title),
        "cost_shift.svg": cost_shift_canvas(unit, taxed, profit_price, theme=theme, title=title),
        "unit_tax.svg": cost_shift_canvas(
            unit, taxed, profit_price, tax=tax, theme=theme, title=title
        ),
        "industry_supply.svg": industry_supply_canvas(
            IndustrySupply(firms),
            prices=industry_prices,
            price_max=max(industry_prices) * 1.1,
            theme=theme,
            title=title,
        ),
        "producer_surplus.svg": producer_surplus_canvas(
            unit, solve_competitive_firm(cost, profit_price), theme=theme, title=title
        ),
    }
    paths = []
    for name, figure in figures.items():
        figure.save(output_dir / name)
        paths.append(output_dir / name)
    return paths


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument("--fixed", type=float, default=30.0)
    args_parser.add_argument("--linear", type=float, default=36.0)
    args_parser.add_argument("--quadratic", type=float, default=-8.0)
    args_parser.add_argument("--cubic", type=float, default=0.6)
    args_parser.add_argument("--min-output", type=float, default=3.0)
    args_parser.add_argument("--max-output", type=float, default=8.6)
    args_parser.add_argument("--profit-price", type=float, default=18.0)
    args_parser.add_argument("--loss-price", type=float, default=11.0)
    args_parser.add_argument("--shutdown-price", type=float, default=8.0)
    args_parser.add_argument("--lost-profit", type=float, nargs=2, default=[6.0, 8.2])
    args_parser.add_argument("--supply-prices", type=float, nargs=2, default=[12.0, 18.0])
    args_parser.add_argument("--tax", type=float, default=4.0)
    args_parser.add_argument("--firms", default=FIRMS, help="fixed:linear:quadratic:cubic ...")
    args_parser.add_argument("--industry-prices", type=float, nargs="*", default=[11.0, 14.0, 20.0])
    args_parser.add_argument("--demand-intercept", type=float, default=12.0)
    args_parser.add_argument("--demand-slope", type=float, default=0.5)
    args_parser.add_argument("--market-price", type=float, default=4.0)
    args_parser.add_argument("--samples", type=int, default=221)
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    session = Session(args)
    try:
        competition_examples(
            args.output_dir,
            session.theme,
            cost=CubicCost(args.fixed, args.linear, args.quadratic, args.cubic),
            profit_price=args.profit_price,
            loss_price=args.loss_price,
            shutdown_price=args.shutdown_price,
            lost_profit=(args.lost_profit[0], args.lost_profit[1]),
            supply_prices=(args.supply_prices[0], args.supply_prices[1]),
            tax=args.tax,
            firms=parse_firms(args.firms),
            industry_prices=tuple(args.industry_prices),
            demand=LinearDemand(args.demand_intercept, args.demand_slope),
            market_price=args.market_price,
            min_output=args.min_output,
            max_output=args.max_output,
            samples=args.samples,
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
