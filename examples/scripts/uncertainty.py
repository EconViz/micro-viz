"""Render the uncertainty figures: risk, mean-variance choice, state claims, dominance."""

from __future__ import annotations

from pathlib import Path

from common import Session, parser

from micro_viz import (
    Gamble,
    IncomeUtility,
    MeanVarianceInvestor,
    PlotTheme,
    RiskReturnLine,
    StateClaims,
    TwoAssetFrontier,
    UniformLottery,
    mean_variance_frontier_canvas,
    risk_attitude_canvas,
    risk_premium_canvas,
    risk_return_choice_canvas,
    state_claims_canvas,
    stochastic_dominance_canvas,
    utility_of_income_canvas,
)


def uncertainty_examples(
    output_dir: Path,
    theme: PlotTheme,
    *,
    gamble: Gamble,
    exponents: tuple[float, float, float],
    averse: float,
    flat: float,
    level: float,
    line: RiskReturnLine,
    sd_max: float,
    market_sd: float,
    claims: StateClaims,
    premiums: tuple[float, float],
    lotteries: tuple[UniformLottery, UniformLottery, UniformLottery, UniformLottery],
    frontier: TwoAssetFrontier,
    title: str | None = None,
) -> list[Path]:
    """Write the utility, risk, state-claim, dominance and frontier figures into ``output_dir``."""
    output_dir.mkdir(parents=True, exist_ok=True)
    concave, convex, linear = (IncomeUtility(e) for e in exponents)
    steep, shallow = MeanVarianceInvestor(averse), MeanVarianceInvestor(flat)
    figures = {
        "utility_of_income.svg": utility_of_income_canvas(
            gamble, (concave, convex, linear), theme=theme
        ),
        "risk_premium.svg": risk_premium_canvas(gamble, concave, theme=theme, title=title),
        "risk_attitude.svg": risk_attitude_canvas((steep, shallow), level, sd_max, theme=theme),
        "risk_return_choice.svg": risk_return_choice_canvas(
            line, (steep,), level, sd_max, theme=theme, title=title
        ),
        "risk_return_two_investors.svg": risk_return_choice_canvas(
            line, (steep, shallow), level, sd_max, theme=theme, title=title
        ),
        "state_claims_fair.svg": state_claims_canvas(
            claims, premiums[:1], theme=theme, title=title
        ),
        "state_claims_unfair.svg": state_claims_canvas(claims, premiums, theme=theme, title=title),
        "first_order_dominance.svg": stochastic_dominance_canvas(
            lotteries[0], lotteries[1], "first", theme=theme, title=title
        ),
        "second_order_dominance.svg": stochastic_dominance_canvas(
            lotteries[2], lotteries[3], "second", theme=theme, title=title
        ),
        "mean_variance_frontier.svg": mean_variance_frontier_canvas(
            frontier, theme=theme, title=title
        ),
        "risk_return_borrowing.svg": risk_return_choice_canvas(
            line, (shallow,), level, sd_max, market_sd, theme=theme, title=title
        ),
    }
    paths = []
    for name, figure in figures.items():
        figure.save(output_dir / name)
        paths.append(output_dir / name)
    return paths


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument(
        "--gamble", type=float, nargs=3, default=[10.0, 30.0, 0.5], help="low high p"
    )
    args_parser.add_argument(
        "--exponents", type=float, nargs=3, default=[0.5, 2.0, 1.0], help="concave convex linear"
    )
    args_parser.add_argument(
        "--risk-aversion", type=float, nargs=2, default=[0.08, 0.02], help="averse flat"
    )
    args_parser.add_argument("--level", type=float, default=5.0)
    args_parser.add_argument(
        "--line", type=float, nargs=2, default=[5.0, 0.6], help="risk_free price_of_risk"
    )
    args_parser.add_argument("--sd-max", type=float, default=30.0)
    args_parser.add_argument("--market-sd", type=float, default=12.0)
    args_parser.add_argument(
        "--claims",
        type=float,
        nargs=4,
        default=[100.0, 40.0, 0.5, 0.3],
        help="good bad p exponent",
    )
    args_parser.add_argument(
        "--premiums", type=float, nargs=2, default=[0.5, 0.6], help="fair unfair"
    )
    args_parser.add_argument(
        "--lotteries",
        type=float,
        nargs=8,
        default=[30.0, 90.0, 10.0, 70.0, 40.0, 60.0, 20.0, 80.0],
        help="low high of A, B, narrow, wide",
    )
    args_parser.add_argument(
        "--assets",
        type=float,
        nargs=5,
        default=[8.0, 10.0, 14.0, 24.0, 0.2],
        help="m1 s1 m2 s2 rho",
    )
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    session = Session(args)
    try:
        uncertainty_examples(
            args.output_dir,
            session.theme,
            gamble=Gamble(*args.gamble),
            exponents=(args.exponents[0], args.exponents[1], args.exponents[2]),
            averse=args.risk_aversion[0],
            flat=args.risk_aversion[1],
            level=args.level,
            line=RiskReturnLine(*args.line),
            sd_max=args.sd_max,
            market_sd=args.market_sd,
            claims=StateClaims(*args.claims),
            premiums=(args.premiums[0], args.premiums[1]),
            lotteries=(
                UniformLottery(*args.lotteries[0:2]),
                UniformLottery(*args.lotteries[2:4]),
                UniformLottery(*args.lotteries[4:6]),
                UniformLottery(*args.lotteries[6:8]),
            ),
            frontier=TwoAssetFrontier(*args.assets),
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
