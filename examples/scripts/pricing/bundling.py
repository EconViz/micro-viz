"""Render bundling diagrams in valuation space: points, separate, pure and mixed bundling."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import Session, parser

from micro_viz import (
    PlotTheme,
    ValuationProfile,
    best_mixed,
    best_pure,
    best_separate,
    mixed_bundling_canvas,
    pure_bundling_canvas,
    separate_selling_regions_canvas,
    valuation_scatter_canvas,
)


def pair_from(text: str) -> tuple[float, float]:
    """A consumer from ``r1:r2``."""
    first, second = (float(part) for part in text.split(":"))
    return first, second


def bundling_examples(
    output_dir: Path,
    theme: PlotTheme,
    *,
    consumers: tuple[tuple[float, float], ...],
    count: int,
    low: float,
    high: float,
    spread: float,
    cost_1: float,
    cost_2: float,
    title: str | None = None,
) -> list[Path]:
    """Write the bundling figures into ``output_dir`` and return their paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    few = ValuationProfile(consumers)
    negative = ValuationProfile.correlated(count, low=low, high=high, direction=-1.0, spread=spread)
    costly = ValuationProfile.correlated(
        count, low=low, high=high, direction=-1.0, spread=spread, cost_1=cost_1, cost_2=cost_2
    )
    positive = ValuationProfile.correlated(count, low=low, high=high, direction=1.0, spread=spread)
    separate = best_separate(negative).offer
    figures = {
        "valuation_points.svg": valuation_scatter_canvas(few, theme=theme, title=title),
        "separate_regions.svg": separate_selling_regions_canvas(
            negative, separate, theme=theme, title=title
        ),
        "pure_bundling.svg": pure_bundling_canvas(
            negative, best_pure(negative).offer.price_bundle or 0.0, theme=theme, title=title
        ),
        "mixed_bundling.svg": mixed_bundling_canvas(
            negative, best_mixed(negative).offer, theme=theme, title=title
        ),
        "mixed_with_costs.svg": mixed_bundling_canvas(
            costly, best_mixed(costly).offer, theme=theme, title=title
        ),
        "regions_numbered.svg": mixed_bundling_canvas(
            positive, best_mixed(positive).offer, numbered=True, theme=theme, title=title
        ),
    }
    paths = []
    for name, figure in figures.items():
        figure.save(output_dir / name)
        paths.append(output_dir / name)
    return paths


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument("--consumers", nargs="+", default=["20:80", "50:50", "80:20"])
    args_parser.add_argument("--count", type=int, default=24)
    args_parser.add_argument("--low", type=float, default=10.0)
    args_parser.add_argument("--high", type=float, default=90.0)
    args_parser.add_argument("--spread", type=float, default=36.0)
    args_parser.add_argument("--cost-1", type=float, default=15.0)
    args_parser.add_argument("--cost-2", type=float, default=15.0)
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    session = Session(args)
    try:
        bundling_examples(
            args.output_dir,
            session.theme,
            consumers=tuple(pair_from(item) for item in args.consumers),
            count=args.count,
            low=args.low,
            high=args.high,
            spread=args.spread,
            cost_1=args.cost_1,
            cost_2=args.cost_2,
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
