"""Render vertical-chain figures: stacked monopolies, integration and transfer pricing."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import Session, parser

from micro_viz import (
    LinearDemand,
    PlotTheme,
    VerticalChain,
    double_marginalization_canvas,
    integrated_firm_canvas,
    transfer_price_outside_market_canvas,
)


def vertical_examples(
    output_dir: Path,
    theme: PlotTheme,
    *,
    chain: VerticalChain,
    market_price: float,
    title: str | None = None,
) -> list[Path]:
    """Write the vertical-chain figures into ``output_dir`` and return their paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    figures = {
        "double_marginalization.svg": double_marginalization_canvas(
            chain, theme=theme, title=title
        ),
        "integrated_firm.svg": integrated_firm_canvas(chain, theme=theme, title=title),
        "transfer_kinked.svg": transfer_price_outside_market_canvas(
            chain, market_price, theme=theme, title=title
        ),
        "transfer_price.svg": transfer_price_outside_market_canvas(
            chain, market_price, kinked=False, theme=theme, title=title
        ),
    }
    paths = []
    for name, figure in figures.items():
        figure.save(output_dir / name)
        paths.append(output_dir / name)
    return paths


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument("--demand", type=float, nargs=2, default=[40.0, 1.0], help="a b")
    args_parser.add_argument("--downstream-cost", type=float, default=2.0)
    args_parser.add_argument("--upstream", type=float, nargs=2, default=[2.0, 0.5], help="m0 m1")
    args_parser.add_argument("--market-price", type=float, default=10.0)
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    session = Session(args)
    try:
        vertical_examples(
            args.output_dir,
            session.theme,
            chain=VerticalChain(
                LinearDemand(*args.demand), args.downstream_cost, args.upstream[0], args.upstream[1]
            ),
            market_price=args.market_price,
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
