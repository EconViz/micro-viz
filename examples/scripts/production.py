"""Render short-run TP, AP, and MP diagrams with marginal-return regions."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from common import Session, parser

from micro_viz import (
    PlotTheme,
    ShortRunProductionFunction,
    analyze_production,
    average_marginal_product_canvas,
    total_product_canvas,
)


def production_examples(
    output_dir: Path,
    theme: PlotTheme,
    *,
    function: ShortRunProductionFunction,
    input_range: tuple[float, float],
    samples: int,
    region_colors: dict[str, str] | None = None,
    title: str | None = None,
) -> tuple[Path, Path]:
    """Write the TP and AP/MP figures, shaded to the top and under the curve, into ``output_dir``.

    The two returned paths are the figures shaded to the top.
    """
    analysis = analyze_production(function, input_range=input_range, samples=samples)
    output_dir.mkdir(parents=True, exist_ok=True)
    total_output = output_dir / "total_product.svg"
    products_output = output_dir / "average_marginal_product.svg"
    total_product_canvas(analysis, theme=theme, title=title, region_colors=region_colors).save(
        total_output
    )
    average_marginal_product_canvas(
        analysis, theme=theme, title=title, region_colors=region_colors
    ).save(products_output)
    # The same figures with the shade stopping at the curve instead of reaching the top.
    under = replace(theme, region_extent="curve")
    total_product_canvas(analysis, theme=under, title=title, region_colors=region_colors).save(
        output_dir / "total_product_under_curve.svg"
    )
    average_marginal_product_canvas(
        analysis, theme=under, title=title, region_colors=region_colors
    ).save(output_dir / "average_marginal_product_under_curve.svg")
    return total_output, products_output


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument("--linear", type=float, default=6.0, help="a in Q = aL + bL^2 + cL^3")
    args_parser.add_argument("--quadratic", type=float, default=3.0, help="b, positive")
    args_parser.add_argument("--cubic", type=float, default=-0.5, help="c, negative")
    args_parser.add_argument("--max-input", type=float, default=6.0)
    args_parser.add_argument("--samples", type=int, default=241)
    args_parser.add_argument(
        "--region-colors",
        nargs=3,
        default=None,
        metavar=("INCREASING", "DIMINISHING", "NEGATIVE"),
        help="a colour for each marginal-return region (default: the theme's shades)",
    )
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    session = Session(args)
    try:
        production_examples(
            args.output_dir,
            session.theme,
            function=ShortRunProductionFunction(args.linear, args.quadratic, args.cubic),
            input_range=(0.0, args.max_input),
            samples=args.samples,
            region_colors=(
                dict(
                    zip(("increasing", "diminishing", "negative"), args.region_colors, strict=True)
                )
                if args.region_colors
                else None
            ),
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
