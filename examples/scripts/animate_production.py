"""Animate the AP/MP diagram while the production technology improves.

The linear coefficient ``a`` of ``Q = aL + bL^2 + cL^3`` is swept from ``--from`` to ``--to``;
every frame is drawn by the same canvas builder as the static figure.
"""

from __future__ import annotations

from pathlib import Path

from common import Session, parser

from micro_viz import (
    PlotTheme,
    ShortRunProductionFunction,
    analyze_production,
    average_marginal_product_canvas,
)
from micro_viz.animation import save_gif, save_svg


def production_animation(
    output_dir: Path,
    theme: PlotTheme,
    *,
    linear_values: tuple[float, ...],
    quadratic: float,
    cubic: float,
    max_input: float,
    y_range: tuple[float, float],
    gif: bool,
    title: str | None = None,
) -> list[Path]:
    """Write the animated SVG (and a GIF when ``gif``) of a rising linear coefficient."""

    def frame(linear: float):  # type: ignore[no-untyped-def]
        function = ShortRunProductionFunction(linear=linear, quadratic=quadratic, cubic=cubic)
        analysis = analyze_production(function, input_range=(0.0, max_input))
        return average_marginal_product_canvas(
            analysis, theme=theme, title=title, y_range=y_range, x_max=max_input * 1.1
        )

    written = [save_svg(frame, linear_values, output_dir / "average_marginal_product_animated.svg")]
    if gif:
        written.append(
            save_gif(frame, linear_values, output_dir / "average_marginal_product_animated.gif")
        )
    return written


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument("--from", dest="start", type=float, default=4.0)
    args_parser.add_argument("--to", dest="stop", type=float, default=8.0)
    args_parser.add_argument("--steps", type=int, default=4)
    args_parser.add_argument("--quadratic", type=float, default=3.0)
    args_parser.add_argument("--cubic", type=float, default=-0.5)
    args_parser.add_argument("--max-input", type=float, default=6.0)
    args_parser.add_argument("--y-min", type=float, default=-25.0)
    args_parser.add_argument("--y-max", type=float, default=25.0)
    args_parser.add_argument("--gif", action="store_true", help="also write a GIF")
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    values = tuple(
        args.start + (args.stop - args.start) * index / args.steps
        for index in range(args.steps + 1)
    )
    session = Session(args)
    try:
        production_animation(
            args.output_dir,
            session.theme,
            linear_values=values,
            quadratic=args.quadratic,
            cubic=args.cubic,
            max_input=args.max_input,
            y_range=(args.y_min, args.y_max),
            gif=args.gif,
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
