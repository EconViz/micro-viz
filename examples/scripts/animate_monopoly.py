"""Animate monopoly: the demand curve shifting out, and a per-unit tax growing.

Every frame is drawn by the same canvas builder as the static figure.
"""

from __future__ import annotations

from pathlib import Path

from common import Session, parser

from micro_viz import (
    CubicCost,
    LinearDemand,
    Monopolist,
    PlotTheme,
    analyze_costs,
    monopoly_demand_shift_canvas,
    monopoly_tax_canvas,
)
from micro_viz.animation import save_gif, save_svg


def linspace(start: float, stop: float, steps: int) -> list[float]:
    """``steps + 1`` evenly spaced values from ``start`` to ``stop``."""
    return [start + (stop - start) * index / steps for index in range(steps + 1)]


def monopoly_animations(
    output_dir: Path,
    theme: PlotTheme,
    *,
    cost: CubicCost,
    demand: LinearDemand,
    intercepts: list[float],
    taxes: list[float],
    min_output: float,
    max_output: float,
    y_max: float,
    x_max: float,
    gif: bool,
    title: str | None = None,
) -> list[Path]:
    """Write the animated SVGs (and GIFs when ``gif``) and return their paths."""
    window = (min_output, max_output)
    unit = analyze_costs(cost, output_range=window)
    firm = Monopolist(demand, cost)
    before = firm.solve()

    def shift_frame(intercept: float):  # type: ignore[no-untyped-def]
        after = firm.with_demand(LinearDemand(intercept, demand.slope)).solve()
        return monopoly_demand_shift_canvas(
            before, after, unit, theme=theme, title=title, x_max=x_max, y_range=(0.0, y_max)
        )

    def tax_frame(tax: float):  # type: ignore[no-untyped-def]
        taxed_cost = cost.with_unit_tax(tax)
        taxed = analyze_costs(taxed_cost, output_range=window)
        after = Monopolist(demand, taxed_cost).solve()
        return monopoly_tax_canvas(
            before, after, unit, taxed, theme=theme, title=title, x_max=x_max, y_range=(0.0, y_max)
        )

    written: list[Path] = []
    for name, frame, values in (
        ("demand_shift", shift_frame, intercepts),
        ("unit_tax", tax_frame, taxes),
    ):
        written.append(save_svg(frame, values, output_dir / f"monopoly_{name}_animated.svg"))
        if gif:
            written.append(save_gif(frame, values, output_dir / f"monopoly_{name}_animated.gif"))
    return written


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument("--cost", default="20:6:-1.5:0.15", help="fixed:linear:quad:cubic")
    args_parser.add_argument("--demand", default="30:2", help="intercept:slope")
    args_parser.add_argument("--min-output", type=float, default=2.0)
    args_parser.add_argument("--max-output", type=float, default=10.0)
    args_parser.add_argument("--intercept-to", type=float, default=38.0)
    args_parser.add_argument("--tax-to", type=float, default=6.0)
    args_parser.add_argument("--y-max", type=float, default=42.0)
    args_parser.add_argument("--x-max", type=float, default=19.0)
    args_parser.add_argument("--steps", type=int, default=6)
    args_parser.add_argument("--gif", action="store_true", help="also write GIFs")
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    fixed, linear, quadratic, cubic = (float(part) for part in args.cost.split(":"))
    intercept, slope = (float(part) for part in args.demand.split(":"))
    session = Session(args)
    try:
        monopoly_animations(
            args.output_dir,
            session.theme,
            cost=CubicCost(fixed, linear, quadratic, cubic),
            demand=LinearDemand(intercept, slope),
            intercepts=linspace(intercept, args.intercept_to, args.steps),
            taxes=linspace(0.0, args.tax_to, args.steps),
            min_output=args.min_output,
            max_output=args.max_output,
            y_max=args.y_max,
            x_max=args.x_max,
            gif=args.gif,
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
