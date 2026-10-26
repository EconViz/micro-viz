"""Render price discrimination: single price, first degree, block pricing, third degree."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import Session, parser

from micro_viz import (
    CostFunction,
    CostSegment,
    CubicCost,
    LinearDemand,
    PiecewiseCost,
    PlotTheme,
    block_pricing,
    block_pricing_canvas,
    first_degree,
    first_degree_canvas,
    single_price_canvas,
    third_degree,
    third_degree_canvas,
)


def demand_from(text: str) -> LinearDemand:
    """A linear demand from ``intercept:slope``."""
    intercept, slope = (float(part) for part in text.split(":"))
    return LinearDemand(intercept, slope)


def discrimination_examples(
    output_dir: Path,
    theme: PlotTheme,
    *,
    demand: LinearDemand,
    marginal_cost: float,
    fixed_cost: float,
    blocks: int,
    markets: tuple[LinearDemand, ...],
    skipped_market: LinearDemand,
    rising_cost: CubicCost,
    capacity: float,
    title: str | None = None,
) -> list[Path]:
    """Write the price-discrimination figures into ``output_dir``."""
    output_dir.mkdir(parents=True, exist_ok=True)
    flat: CostFunction = PiecewiseCost((CostSegment(capacity, marginal_cost),))
    with_fixed = PiecewiseCost((CostSegment(capacity, marginal_cost),), fixed_cost=fixed_cost)
    figures = {
        "single_price.svg": single_price_canvas(
            demand, flat, groups=True, theme=theme, title=title
        ),
        "first_degree.svg": first_degree_canvas(
            first_degree(demand, flat), theme=theme, title=title
        ),
        "block_pricing_three.svg": block_pricing_canvas(
            block_pricing(demand, flat, 3), theme=theme, title=title
        ),
        "block_pricing.svg": block_pricing_canvas(
            block_pricing(demand, with_fixed, blocks), average_cost=True, theme=theme, title=title
        ),
        "third_degree.svg": third_degree_canvas(third_degree(markets, flat), theme=theme),
        "third_degree_corner.svg": third_degree_canvas(
            third_degree((markets[0], skipped_market), rising_cost), theme=theme
        ),
    }
    paths = []
    for name, figure in figures.items():
        figure.save(output_dir / name)
        paths.append(output_dir / name)
    return paths


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument("--demand", default="30:1", help="intercept:slope")
    args_parser.add_argument("--marginal-cost", type=float, default=6.0)
    args_parser.add_argument("--fixed-cost", type=float, default=60.0)
    args_parser.add_argument("--capacity", type=float, default=100.0)
    args_parser.add_argument("--blocks", type=int, default=6)
    args_parser.add_argument("--markets", nargs=2, default=["30:1", "20:1"])
    args_parser.add_argument("--skipped-market", default="10:1")
    args_parser.add_argument("--rising-cost", type=float, nargs=4, default=[0.0, 6.0, 0.0, 0.3])
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    session = Session(args)
    try:
        discrimination_examples(
            args.output_dir,
            session.theme,
            demand=demand_from(args.demand),
            marginal_cost=args.marginal_cost,
            fixed_cost=args.fixed_cost,
            blocks=args.blocks,
            markets=tuple(demand_from(item) for item in args.markets),
            skipped_market=demand_from(args.skipped_market),
            rising_cost=CubicCost(*args.rising_cost),
            capacity=args.capacity,
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
