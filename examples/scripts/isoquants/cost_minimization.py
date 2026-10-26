"""Render cost minimization: tangency, input price change, technical change, expansion path."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import Session, parser

from micro_viz import (
    CobbDouglas,
    PlotTheme,
    cost_minimization_canvas,
    expansion_path_canvas,
    fixed_capital_canvas,
    input_price_change_canvas,
    technical_change_canvas,
)


def floats(text: str) -> list[float]:
    """Numbers separated by spaces."""
    return [float(part) for part in text.split()]


def cost_examples(
    output_dir: Path,
    theme: PlotTheme,
    *,
    technology: CobbDouglas,
    improved: CobbDouglas,
    outputs: list[float],
    output: float,
    wage: float,
    rent: float,
    new_wage: float,
    capital: float,
    bounds: tuple[float, float],
    title: str | None = None,
) -> list[Path]:
    """Write the cost-minimization figures into ``output_dir`` and return their paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    figures = {
        "cost_minimization.svg": cost_minimization_canvas(
            technology, output, wage, rent, bounds, theme=theme, title=title
        ),
        "input_price_change.svg": input_price_change_canvas(
            technology, output, wage, rent, new_wage, bounds, along=True, theme=theme, title=title
        ),
        "technical_change.svg": technical_change_canvas(
            technology, improved, output, wage, rent, bounds, theme=theme, title=title
        ),
        "expansion_path.svg": expansion_path_canvas(
            technology, outputs, wage, rent, bounds, theme=theme
        ),
        "fixed_capital.svg": fixed_capital_canvas(
            technology, outputs, capital, wage, rent, bounds, theme=theme, title=title
        ),
    }
    paths = []
    for name, figure in figures.items():
        figure.save(output_dir / name)
        paths.append(output_dir / name)
    return paths


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument("--shares", type=float, nargs=2, default=[0.5, 0.5])
    args_parser.add_argument("--improved-scale", type=float, default=1.3)
    args_parser.add_argument("--outputs", default="4 6 8")
    args_parser.add_argument("--output", type=float, default=6.0)
    args_parser.add_argument("--wage", type=float, default=1.0)
    args_parser.add_argument("--rent", type=float, default=1.0)
    args_parser.add_argument("--new-wage", type=float, default=2.0)
    args_parser.add_argument("--capital", type=float, default=4.0)
    args_parser.add_argument("--bounds", type=float, nargs=2, default=[14.0, 14.0])
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    session = Session(args)
    try:
        cost_examples(
            args.output_dir,
            session.theme,
            technology=CobbDouglas(*args.shares),
            improved=CobbDouglas(args.shares[0], args.shares[1], args.improved_scale),
            outputs=floats(args.outputs),
            output=args.output,
            wage=args.wage,
            rent=args.rent,
            new_wage=args.new_wage,
            capital=args.capital,
            bounds=(args.bounds[0], args.bounds[1]),
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
