"""Render linked total-revenue, total-cost and profit diagrams."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import Session, parser

from micro_viz import (
    CubicCost,
    LinearDemand,
    competitive_profit_grid,
    monopoly_profit_grid,
)


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    session = Session(args)
    try:
        competitive_cost = CubicCost(1.0, 5.0, -1.0, 0.1)
        competitive_loss_cost = CubicCost(18.0, 5.0, -1.0, 0.1)
        demand = LinearDemand(15.0, 0.7)
        monopoly_cost = CubicCost(5.0, 17.0, -3.0, 0.2)
        monopoly_loss_cost = CubicCost(45.0, 17.0, -3.0, 0.2)
        figures = {
            "competitive_profit.svg": competitive_profit_grid(
                competitive_cost,
                4.5,
                output_max=11.0,
                theme=session.theme,
                title=args.title,
            ),
            "competitive_loss.svg": competitive_profit_grid(
                competitive_loss_cost,
                4.5,
                output_max=11.0,
                theme=session.theme,
                title=args.title,
            ),
            "monopoly_profit.svg": monopoly_profit_grid(
                demand,
                monopoly_cost,
                output_max=15.0,
                theme=session.theme,
                title=args.title,
            ),
            "monopoly_loss.svg": monopoly_profit_grid(
                demand,
                monopoly_loss_cost,
                output_max=15.0,
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
