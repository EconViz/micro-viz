"""Render choice-under-uncertainty figures: utility of income, risk premium and risk-return."""

from __future__ import annotations

from pathlib import Path

from common import Session, parser

from micro_viz import (
    Gamble,
    IncomeUtility,
    MeanVarianceInvestor,
    PlotTheme,
    RiskReturnLine,
    risk_attitude_canvas,
    risk_premium_canvas,
    risk_return_choice_canvas,
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
    title: str | None = None,
) -> list[Path]:
    """Write the uncertainty figures into ``output_dir`` and return their paths."""
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
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
