"""Render information figures: lemons, signaling, moral hazard, bonuses, efficiency wage."""

from __future__ import annotations

from pathlib import Path

from common import Session, parser

from micro_viz import (
    BonusSchedule,
    EfficiencyWage,
    LemonsMarket,
    LinearDemand,
    MoralHazard,
    PlotTheme,
    Signaling,
    bonus_schedule_canvas,
    efficiency_wage_canvas,
    lemons_market_canvas,
    moral_hazard_canvas,
    signaling_canvas,
)


def information_examples(
    output_dir: Path,
    theme: PlotTheme,
    *,
    lemons: LemonsMarket,
    shares: tuple[float, ...],
    signaling: Signaling,
    hazard: MoralHazard,
    bonus: BonusSchedule,
    capacities: tuple[float, ...],
    reach: float,
    efficiency: EfficiencyWage,
    title: str | None = None,
) -> list[Path]:
    """Write the information figures into ``output_dir`` and return their paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    figures = {
        "lemons.svg": lemons_market_canvas(lemons, shares, theme=theme),
        "signaling.svg": signaling_canvas(signaling, theme=theme),
        "moral_hazard.svg": moral_hazard_canvas(hazard, theme=theme, title=title),
        "bonus_schedule.svg": bonus_schedule_canvas(
            bonus, capacities, reach, theme=theme, title=title
        ),
        "efficiency_wage.svg": efficiency_wage_canvas(efficiency, theme=theme, title=title),
    }
    paths = []
    for name, figure in figures.items():
        figure.save(output_dir / name)
        paths.append(output_dir / name)
    return paths


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument("--demand-high", type=float, nargs=2, default=[40.0, 1.0], help="a b")
    args_parser.add_argument("--demand-low", type=float, nargs=2, default=[20.0, 1.0], help="a b")
    args_parser.add_argument("--costs", type=float, nargs=2, default=[24.0, 6.0], help="high low")
    args_parser.add_argument("--supply-slope", type=float, default=0.5)
    args_parser.add_argument("--shares", type=float, nargs="+", default=[0.8, 0.3])
    args_parser.add_argument(
        "--signal", type=float, nargs=3, default=[20.0, 2.0, 1.0], help="B kL kH"
    )
    args_parser.add_argument(
        "--hazard", type=float, nargs=3, default=[30.0, 1.0, 12.0], help="a b mc"
    )
    args_parser.add_argument("--coverage", type=float, default=0.6)
    args_parser.add_argument(
        "--bonus", type=float, nargs=3, default=[0.5, 0.1, 1.2], help="report under over"
    )
    args_parser.add_argument("--capacities", type=float, nargs="+", default=[30.0, 60.0])
    args_parser.add_argument("--reach", type=float, default=100.0)
    args_parser.add_argument(
        "--efficiency",
        type=float,
        nargs=6,
        default=[40.0, 1.0, 4.0, 0.5, 10.0, 0.9],
        help="a b s0 s1 n0 n1",
    )
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    session = Session(args)
    try:
        information_examples(
            args.output_dir,
            session.theme,
            lemons=LemonsMarket(
                LinearDemand(*args.demand_high),
                LinearDemand(*args.demand_low),
                args.costs[0],
                args.costs[1],
                args.supply_slope,
            ),
            shares=tuple(args.shares),
            signaling=Signaling(*args.signal),
            hazard=MoralHazard(
                LinearDemand(args.hazard[0], args.hazard[1]), args.hazard[2], args.coverage
            ),
            bonus=BonusSchedule(*args.bonus),
            capacities=tuple(args.capacities),
            reach=args.reach,
            efficiency=EfficiencyWage(*args.efficiency),
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
