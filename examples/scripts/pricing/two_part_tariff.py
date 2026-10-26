"""Render two-part tariffs: a single buyer, two buyer types, and profit against the entry fee."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import Session, parser

from micro_viz import (
    BuyerType,
    LinearDemand,
    PlotTheme,
    best_tariff,
    evaluate_tariff,
    tariff_profit_canvas,
    two_part_tariff_canvas,
)


def buyer_from(text: str) -> BuyerType:
    """A buyer type from ``intercept:slope`` or ``intercept:slope:count``."""
    parts = [float(part) for part in text.split(":")]
    return BuyerType(LinearDemand(parts[0], parts[1]), parts[2] if len(parts) > 2 else 1.0)


def tariff_examples(
    output_dir: Path,
    theme: PlotTheme,
    *,
    single: BuyerType,
    buyers: tuple[BuyerType, ...],
    marginal_cost: float,
    usage_fee: float,
    fee_max: float,
    title: str | None = None,
) -> list[Path]:
    """Write the tariff figures into ``output_dir`` and return their paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    flat = evaluate_tariff((single,), marginal_cost, marginal_cost, single.surplus(marginal_cost))
    best = best_tariff(buyers, marginal_cost)
    figures = {
        "single_buyer.svg": two_part_tariff_canvas((single,), flat, theme=theme, title=title),
        "two_buyers.svg": two_part_tariff_canvas(buyers, best, theme=theme, title=title),
        "tariff_profit.svg": tariff_profit_canvas(
            buyers, marginal_cost, usage_fee, fee_max, theme=theme, title=title
        ),
    }
    paths = []
    for name, figure in figures.items():
        figure.save(output_dir / name)
        paths.append(output_dir / name)
    return paths


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument("--single", default="30:1")
    args_parser.add_argument("--buyers", nargs="+", default=["30:1:1", "20:1:3"])
    args_parser.add_argument("--marginal-cost", type=float, default=4.0)
    args_parser.add_argument("--usage-fee", type=float, default=6.5)
    args_parser.add_argument(
        "--fee-max", type=float, default=0.0, help="0 means the largest surplus"
    )
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    buyers = tuple(buyer_from(item) for item in args.buyers)
    fee_max = args.fee_max or max(b.surplus(args.usage_fee) for b in buyers) * 1.15
    session = Session(args)
    try:
        tariff_examples(
            args.output_dir,
            session.theme,
            single=buyer_from(args.single),
            buyers=buyers,
            marginal_cost=args.marginal_cost,
            usage_fee=args.usage_fee,
            fee_max=fee_max,
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
