"""Render stepped and kinked marginal cost with price bands (capacity steps)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import Session, parser

from micro_viz import (
    CostSegment,
    PiecewiseCost,
    PlotTheme,
    analyze_costs,
    piecewise_cost_canvas,
)

STEPPED = "6:11.4 9:13.0"
"""Preset: a flat marginal cost that steps up once, as when an extra shift starts."""
KINKED = "5:7.2:0.05 8.2:7.6:0.1:0.05 9:8.8:2.0"
"""Preset: rising marginal cost with two jumps, as when processing units are switched on."""


def parse_segments(text: str) -> tuple[CostSegment, ...]:
    """Segments from ``end:intercept[:slope[:curvature]]`` items separated by spaces."""
    segments = []
    for item in text.split():
        end, intercept, *rest = (float(part) for part in item.split(":"))
        segments.append(CostSegment(end, intercept, *rest))
    return tuple(segments)


def piecewise_examples(
    output_dir: Path,
    theme: PlotTheme,
    *,
    stepped: PiecewiseCost,
    kinked: PiecewiseCost,
    prices: tuple[float, ...],
    kinked_prices: tuple[float, ...],
    kinked_y_min: float,
    samples: int,
    title: str | None = None,
) -> list[Path]:
    """Write the stepped and kinked marginal-cost examples into ``output_dir``."""
    output_dir.mkdir(parents=True, exist_ok=True)
    step_analysis = analyze_costs(stepped, output_range=(0.0, stepped.capacity), samples=samples)
    kink_analysis = analyze_costs(kinked, output_range=(0.0, kinked.capacity), samples=samples)
    kink_top = max(value for _, value in kink_analysis.marginal_cost_path)
    figures = {
        "stepped_cost.svg": piecewise_cost_canvas(step_analysis, theme=theme, title=title),
        "stepped_cost_prices.svg": piecewise_cost_canvas(
            step_analysis, prices=prices, theme=theme, title=title
        ),
        "kinked_marginal_cost.svg": piecewise_cost_canvas(
            kink_analysis,
            prices=kinked_prices,
            average=False,
            y_range=(kinked_y_min, kink_top + (kink_top - kinked_y_min) * 0.1),
            theme=theme,
            title=title,
        ),
    }
    for name, figure in figures.items():
        figure.save(output_dir / name)
    return [output_dir / name for name in figures]


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument("--stepped", default=STEPPED, help="end:intercept[:slope[:curvature]]")
    args_parser.add_argument("--kinked", default=KINKED, help="same format as --stepped")
    args_parser.add_argument("--prices", type=float, nargs="*", default=[12.2, 14.0])
    args_parser.add_argument("--kinked-prices", type=float, nargs="*", default=[7.5, 8.2, 9.5])
    args_parser.add_argument("--kinked-y-min", type=float, default=6.8)
    args_parser.add_argument("--fixed", type=float, default=0.0, help="fixed cost")
    args_parser.add_argument("--samples", type=int, default=201)
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    session = Session(args)
    try:
        piecewise_examples(
            args.output_dir,
            session.theme,
            stepped=PiecewiseCost(parse_segments(args.stepped), fixed_cost=args.fixed),
            kinked=PiecewiseCost(parse_segments(args.kinked), fixed_cost=args.fixed),
            prices=tuple(args.prices),
            kinked_prices=tuple(args.kinked_prices),
            kinked_y_min=args.kinked_y_min,
            samples=args.samples,
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
