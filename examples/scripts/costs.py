"""Render short-run cost curves: totals, unit costs and the two stacked panels."""

from __future__ import annotations

from pathlib import Path

from common import Session, parser

from micro_viz import (
    Cost,
    PlotTheme,
    analyze_costs,
    cost_curves_grid,
    cost_curves_panels,
    total_cost_canvas,
    unit_cost_canvas,
)


def cost_examples(
    output_dir: Path,
    theme: PlotTheme,
    *,
    cost: Cost,
    min_output: float,
    max_output: float,
    samples: int,
    avc_reach: float = 1.15,
    title: str | None = None,
) -> list[Path]:
    """Write the cost-curve examples for ``cost`` into ``output_dir`` and return the paths."""
    analysis = analyze_costs(cost, output_range=(min_output, max_output), samples=samples)
    no_fixed = analyze_costs(
        cost.without_fixed_cost(),
        output_range=(min_output, max_output * avc_reach),
        samples=samples,
    )
    total_panel, unit_panel = cost_curves_panels(analysis, theme=theme, titles=(title, None))
    output_dir.mkdir(parents=True, exist_ok=True)
    figures = {
        "total_cost.svg": total_cost_canvas(analysis, theme=theme, title=title),
        "unit_cost.svg": unit_cost_canvas(analysis, theme=theme, title=title),
        "cubic_avc_mc.svg": unit_cost_canvas(
            no_fixed, curves=("mc", "avc"), theme=theme, title=title
        ),
        "cost_curves_total.svg": total_panel,
        "cost_curves_unit.svg": unit_panel,
        "cost_curves.svg": cost_curves_grid(analysis, theme=theme, titles=(title, None)),
    }
    paths = []
    for name, figure in figures.items():
        figure.save(output_dir / name)
        paths.append(output_dir / name)
    return paths


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument("--fixed", type=float, default=200.0, help="fixed cost FC")
    args_parser.add_argument(
        "--linear", type=float, default=120.0, help="b in VC = bq + cq^2 + dq^3"
    )
    args_parser.add_argument("--quadratic", type=float, default=-18.0, help="c (negative: U-shape)")
    args_parser.add_argument("--cubic", type=float, default=1.0, help="d, positive")
    args_parser.add_argument(
        "--formula",
        default=None,
        help='total cost as a formula, such as "TC = 200 + 120Q - 18Q^2 + Q^3"; '
        "replaces the four coefficients",
    )
    args_parser.add_argument("--min-output", type=float, default=1.0)
    args_parser.add_argument("--max-output", type=float, default=16.0)
    args_parser.add_argument("--samples", type=int, default=221)
    args_parser.add_argument(
        "--avc-reach",
        type=float,
        default=1.15,
        help="the AVC and MC figure runs to this multiple of --max-output",
    )
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    session = Session(args)
    try:
        cost_examples(
            args.output_dir,
            session.theme,
            cost=(
                Cost(args.formula)
                if args.formula
                else Cost.polynomial(args.fixed, args.linear, args.quadratic, args.cubic)
            ),
            min_output=args.min_output,
            max_output=args.max_output,
            samples=args.samples,
            avc_reach=args.avc_reach,
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
