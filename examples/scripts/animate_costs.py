"""Animate cost curves: unit costs as output grows, and output as the price rises.

The first animation sweeps the marked output along the MC, ATC, AVC and AFC curves; the second
raises the price through a stepped marginal cost, so the output jumps when the price passes the
step. Every frame is drawn by the same canvas builder as the static figure.
"""

from __future__ import annotations

from pathlib import Path

from common import Session, parser

from micro_viz import (
    CostSegment,
    CubicCost,
    PiecewiseCost,
    PlotTheme,
    analyze_costs,
    piecewise_cost_canvas,
    unit_cost_canvas,
)
from micro_viz.animation import save_gif, save_svg


def linspace(start: float, stop: float, steps: int) -> list[float]:
    """``steps + 1`` evenly spaced values from ``start`` to ``stop``."""
    return [start + (stop - start) * index / steps for index in range(steps + 1)]


def cost_animations(
    output_dir: Path,
    theme: PlotTheme,
    *,
    cost: CubicCost,
    stepped: PiecewiseCost,
    outputs: list[float],
    prices: list[float],
    min_output: float,
    max_output: float,
    y_max: float,
    gif: bool,
    title: str | None = None,
) -> list[Path]:
    """Write both animated SVGs (and GIFs when ``gif``) and return their paths."""
    unit = analyze_costs(cost, output_range=(min_output, max_output))
    step = analyze_costs(stepped, output_range=(0.0, stepped.capacity))
    x_unit = max_output * 1.1
    x_step = stepped.capacity * 1.1
    top = max(prices) * 1.1

    def unit_frame(output: float):  # type: ignore[no-untyped-def]
        return unit_cost_canvas(
            unit, output=output, theme=theme, title=title, x_max=x_unit, y_range=(0.0, y_max)
        )

    def price_frame(price: float):  # type: ignore[no-untyped-def]
        return piecewise_cost_canvas(
            step,
            prices=(price,),
            theme=theme,
            title=title,
            x_max=x_step,
            y_range=(0.0, top),
        )

    written: list[Path] = []
    for name, frame, values in (
        ("unit_cost_output", unit_frame, outputs),
        ("stepped_cost_price", price_frame, prices),
    ):
        written.append(save_svg(frame, values, output_dir / f"{name}_animated.svg"))
        if gif:
            written.append(save_gif(frame, values, output_dir / f"{name}_animated.gif"))
    return written


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument("--fixed", type=float, default=50.0)
    args_parser.add_argument("--linear", type=float, default=36.0)
    args_parser.add_argument("--quadratic", type=float, default=-8.0)
    args_parser.add_argument("--cubic", type=float, default=0.6)
    args_parser.add_argument("--min-output", type=float, default=1.0)
    args_parser.add_argument("--max-output", type=float, default=11.0)
    args_parser.add_argument("--y-max", type=float, default=95.0)
    args_parser.add_argument("--steps", type=int, default=6)
    args_parser.add_argument("--segments", default="6:11.4 9:13.0", help="end:intercept per step")
    args_parser.add_argument("--price-from", type=float, default=10.0)
    args_parser.add_argument("--price-to", type=float, default=14.5)
    args_parser.add_argument("--gif", action="store_true", help="also write GIFs")
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    segments = tuple(
        CostSegment(*(float(part) for part in item.split(":"))) for item in args.segments.split()
    )
    session = Session(args)
    try:
        cost_animations(
            args.output_dir,
            session.theme,
            cost=CubicCost(args.fixed, args.linear, args.quadratic, args.cubic),
            stepped=PiecewiseCost(segments),
            outputs=linspace(args.min_output, args.max_output, args.steps),
            prices=linspace(args.price_from, args.price_to, args.steps),
            min_output=args.min_output,
            max_output=args.max_output,
            y_max=args.y_max,
            gif=args.gif,
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
