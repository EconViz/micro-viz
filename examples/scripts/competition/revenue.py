"""Render total, average and marginal revenue under monopoly and perfect competition."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import Session, parser

from micro_viz import (
    LinearDemand,
    competitive_revenue_grid,
    competitive_revenue_shift_grid,
    monopoly_revenue_grid,
)


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument("--price", type=float, default=4.0)
    args_parser.add_argument("--new-price", type=float, default=5.4)
    args_parser.add_argument("--output-max", type=float, default=10.0)
    args_parser.add_argument("--demand-intercept", type=float, default=10.0)
    args_parser.add_argument("--demand-slope", type=float, default=1.0)
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    session = Session(args)
    try:
        figures = {
            "competitive_revenue.svg": competitive_revenue_grid(
                args.price,
                output_max=args.output_max,
                theme=session.theme,
                title=args.title,
            ),
            "competitive_revenue_shift.svg": competitive_revenue_shift_grid(
                args.price,
                args.new_price,
                output_max=args.output_max,
                theme=session.theme,
                title=args.title,
            ),
            "monopoly_revenue.svg": monopoly_revenue_grid(
                LinearDemand(args.demand_intercept, args.demand_slope),
                theme=session.theme,
                title=args.title,
            ),
        }
        for name, figure in figures.items():
            figure.save(session.path(name))
    finally:
        session.close()


if __name__ == "__main__":
    main()
