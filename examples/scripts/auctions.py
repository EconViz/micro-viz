"""Render auction figures: first- and second-price bid functions and revenue equivalence."""

from __future__ import annotations

from pathlib import Path

from common import Session, parser

from micro_viz import (
    Auction,
    PlotTheme,
    bid_functions_canvas,
    revenue_equivalence_canvas,
)


def auction_examples(
    output_dir: Path,
    theme: PlotTheme,
    *,
    bidders: tuple[int, ...],
    max_value: float,
    title: str | None = None,
) -> list[Path]:
    """Write the auction figures into ``output_dir`` and return their paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    figures = {
        "bid_functions.svg": bid_functions_canvas(
            (Auction(bidders[0], max_value),), theme=theme, title=title
        ),
        "bid_functions_by_bidders.svg": bid_functions_canvas(
            tuple(Auction(n, max_value) for n in bidders), theme=theme, title=title
        ),
        "revenue_equivalence.svg": revenue_equivalence_canvas(
            tuple(range(2, max(bidders) + 8)), max_value, theme=theme, title=title
        ),
    }
    paths = []
    for name, figure in figures.items():
        figure.save(output_dir / name)
        paths.append(output_dir / name)
    return paths


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument("--bidders", type=int, nargs="+", default=[3, 6])
    args_parser.add_argument("--max-value", type=float, default=100.0)
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    session = Session(args)
    try:
        auction_examples(
            args.output_dir,
            session.theme,
            bidders=tuple(args.bidders),
            max_value=args.max_value,
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
