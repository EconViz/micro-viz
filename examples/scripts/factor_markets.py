"""Render factor-market figures: derived demand, hiring, industry demand, equilibrium and rent."""

from __future__ import annotations

from pathlib import Path

from common import Session, parser

from micro_viz import (
    CapitalAdjustment,
    DerivedDemand,
    FactorMarket,
    IndustryFactorDemand,
    InputAdjustment,
    LandMarket,
    LinearSupply,
    LinearValue,
    PlotTheme,
    capital_adjustment_canvas,
    derived_demand_canvas,
    economic_rent_canvas,
    factor_equilibrium_canvas,
    firm_hiring_canvas,
    industry_factor_demand_canvas,
    land_rent_canvas,
    market_supply_canvas,
    short_long_run_canvas,
)


def factor_examples(
    output_dir: Path,
    theme: PlotTheme,
    *,
    product: LinearValue,
    price: float,
    mr_share: float,
    supply: LinearSupply,
    wage: float,
    lower_wage: float,
    firms: int,
    price_effect: float,
    capital: tuple[float, ...],
    wages: tuple[float, ...],
    land: tuple[float, float, float],
    title: str | None = None,
) -> list[Path]:
    """Write the factor-market figures into ``output_dir`` and return their paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    competitive = DerivedDemand(product, price)
    monopoly = DerivedDemand(product, price, mr_share)
    market = FactorMarket(competitive.demand, supply)
    anchor = market.equilibrium()
    firm = FactorMarket(competitive.demand, supply)
    industry = IndustryFactorDemand(competitive.demand, firms, price_effect)
    adjustment = InputAdjustment(
        anchor[0], anchor[1], competitive.demand.slope * 2, competitive.demand.slope / 2
    )
    figures = {
        "derived_demand.svg": derived_demand_canvas(monopoly, theme=theme, title=title),
        "firm_hiring.svg": firm_hiring_canvas(firm, wage, theme=theme, title=title),
        "wage_decline.svg": firm_hiring_canvas(firm, wage, lower_wage, theme=theme, title=title),
        "capital_adjustment.svg": capital_adjustment_canvas(
            CapitalAdjustment(competitive.demand, capital), wages, theme=theme, title=title
        ),
        "industry_demand.svg": industry_factor_demand_canvas(industry, anchor[1], theme=theme),
        "short_long_run.svg": short_long_run_canvas(
            adjustment, competitive.demand.intercept, theme=theme, title=title
        ),
        "market_supply.svg": market_supply_canvas(market, theme=theme),
        "factor_equilibrium.svg": factor_equilibrium_canvas(
            market, FactorMarket(monopoly.demand, supply), theme=theme
        ),
        "economic_rent.svg": economic_rent_canvas(market, theme=theme, title=title),
        "land_rent.svg": land_rent_canvas(
            LandMarket(LinearValue(land[0], land[1]), land[2]), theme=theme, title=title
        ),
    }
    paths = []
    for name, figure in figures.items():
        figure.save(output_dir / name)
        paths.append(output_dir / name)
    return paths


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument("--product", type=float, nargs=2, default=[10.0, 0.5], help="a b")
    args_parser.add_argument("--price", type=float, default=3.0)
    args_parser.add_argument("--mr-share", type=float, default=0.6)
    args_parser.add_argument("--supply", type=float, nargs=2, default=[4.0, 0.6], help="a b")
    args_parser.add_argument("--wage", type=float, default=12.0)
    args_parser.add_argument("--lower-wage", type=float, default=8.0)
    args_parser.add_argument("--firms", type=int, default=5)
    args_parser.add_argument("--price-effect", type=float, default=1.0)
    args_parser.add_argument("--wages", type=float, nargs="+", default=[14.0, 12.0, 10.0])
    args_parser.add_argument("--capital", type=float, nargs="+", default=[1.0, 1.4, 1.8])
    args_parser.add_argument("--land", type=float, nargs=3, default=[30.0, 1.0, 12.0], help="a b T")
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    session = Session(args)
    try:
        factor_examples(
            args.output_dir,
            session.theme,
            product=LinearValue(*args.product),
            price=args.price,
            mr_share=args.mr_share,
            supply=LinearSupply(*args.supply),
            wage=args.wage,
            lower_wage=args.lower_wage,
            firms=args.firms,
            price_effect=args.price_effect,
            capital=tuple(args.capital),
            wages=tuple(args.wages),
            land=(args.land[0], args.land[1], args.land[2]),
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
