"""Render intertemporal and peak-load pricing figures."""

from __future__ import annotations

from pathlib import Path

from common import Session, parser

from micro_viz import (
    IntertemporalPricing,
    LinearDemand,
    PeakLoadPricing,
    PlotTheme,
    intertemporal_pricing_canvas,
    peak_load_canvas,
)


def time_pricing_examples(
    output_dir: Path,
    theme: PlotTheme,
    *,
    first: LinearDemand,
    second: LinearDemand,
    peak: LinearDemand,
    off_peak: LinearDemand,
    marginal_cost: float,
    capacity_cost: float,
    title: str | None = None,
) -> list[Path]:
    """Write the time-pricing figures into ``output_dir`` and return their paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    figures = {
        "intertemporal.svg": intertemporal_pricing_canvas(
            IntertemporalPricing(first, second, marginal_cost), theme=theme, title=title
        ),
        "peak_load.svg": peak_load_canvas(
            PeakLoadPricing(peak, off_peak, marginal_cost, capacity_cost), theme=theme, title=title
        ),
    }
    paths = []
    for name, figure in figures.items():
        figure.save(output_dir / name)
        paths.append(output_dir / name)
    return paths


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument("--first", type=float, nargs=2, default=[30.0, 1.0], help="a b")
    args_parser.add_argument("--second", type=float, nargs=2, default=[22.0, 1.0], help="a b")
    args_parser.add_argument("--peak", type=float, nargs=2, default=[30.0, 1.0], help="a b")
    args_parser.add_argument("--off-peak", type=float, nargs=2, default=[20.0, 1.0], help="a b")
    args_parser.add_argument("--marginal-cost", type=float, default=4.0)
    args_parser.add_argument("--capacity-cost", type=float, default=6.0)
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    session = Session(args)
    try:
        time_pricing_examples(
            args.output_dir,
            session.theme,
            first=LinearDemand(*args.first),
            second=LinearDemand(*args.second),
            peak=LinearDemand(*args.peak),
            off_peak=LinearDemand(*args.off_peak),
            marginal_cost=args.marginal_cost,
            capacity_cost=args.capacity_cost,
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
