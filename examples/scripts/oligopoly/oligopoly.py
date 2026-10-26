"""Render duopoly figures: residual demands, reaction curves and price reaction curves."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import Session, parser

from micro_viz import (
    DifferentiatedDuopoly,
    Duopoly,
    PlotTheme,
    price_reaction_canvas,
    reaction_curves_canvas,
    residual_demand_canvas,
)


def oligopoly_examples(
    output_dir: Path,
    theme: PlotTheme,
    *,
    duopoly: Duopoly,
    guesses: tuple[float, ...],
    differentiated: DifferentiatedDuopoly,
    title: str | None = None,
) -> list[Path]:
    """Write the oligopoly figures into ``output_dir`` and return their paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    figures = {
        "residual_demand.svg": residual_demand_canvas(duopoly, guesses, theme=theme, title=title),
        "cournot.svg": reaction_curves_canvas(duopoly, theme=theme, title=title),
        "cournot_points.svg": reaction_curves_canvas(
            duopoly, competitive=True, collusive=True, theme=theme, title=title
        ),
        "stackelberg.svg": reaction_curves_canvas(duopoly, leader=1, theme=theme, title=title),
        "price_reaction.svg": price_reaction_canvas(differentiated, theme=theme, title=title),
    }
    paths = []
    for name, figure in figures.items():
        figure.save(output_dir / name)
        paths.append(output_dir / name)
    return paths


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument("--intercept", type=float, default=30.0)
    args_parser.add_argument("--slope", type=float, default=1.0)
    args_parser.add_argument("--costs", type=float, nargs=2, default=[6.0, 6.0])
    args_parser.add_argument("--guesses", type=float, nargs="+", default=[0.0, 6.0])
    args_parser.add_argument("--alphas", type=float, nargs=2, default=[12.0, 12.0])
    args_parser.add_argument("--betas", type=float, nargs=2, default=[2.0, 2.0])
    args_parser.add_argument("--gammas", type=float, nargs=2, default=[1.0, 1.0])
    args_parser.add_argument("--unit-costs", type=float, nargs=2, default=[2.0, 2.0])
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    session = Session(args)
    try:
        oligopoly_examples(
            args.output_dir,
            session.theme,
            duopoly=Duopoly(args.intercept, args.slope, *args.costs),
            guesses=tuple(args.guesses),
            differentiated=DifferentiatedDuopoly(
                args.alphas[0],
                args.alphas[1],
                args.betas[0],
                args.betas[1],
                args.gammas[0],
                args.gammas[1],
                args.unit_costs[0],
                args.unit_costs[1],
            ),
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
