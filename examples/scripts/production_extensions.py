"""Render learning, scope, technical-progress and frontier figures."""

from __future__ import annotations

from pathlib import Path

from common import Session, parser

from micro_viz import (
    LearningAverageCost,
    LearningCurve,
    PlotTheme,
    ProductionFrontier,
    ProductTransformation,
    ShortRunProductionFunction,
    TechnologyShift,
    learning_curve_canvas,
    product_transformation_canvas,
    production_frontier_canvas,
    scale_vs_learning_canvas,
    technology_shift_canvas,
)


def extension_examples(
    output_dir: Path,
    theme: PlotTheme,
    *,
    learning: LearningCurve,
    cumulative_max: float,
    cost: LearningAverageCost,
    learning_gain: float,
    scale_range: tuple[float, float],
    transformation: ProductTransformation,
    production: ShortRunProductionFunction,
    factors: tuple[float, ...],
    input_max: float,
    frontier: ProductionFrontier,
    point_names: tuple[str, ...],
    title: str | None = None,
) -> list[Path]:
    """Write the production-extension figures into ``output_dir`` and return their paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    figures = {
        "learning_curve.svg": learning_curve_canvas(
            learning, cumulative_max, theme=theme, title=title
        ),
        "scale_vs_learning.svg": scale_vs_learning_canvas(
            cost, learning_gain, scale_range[0], scale_range[1], theme=theme, title=title
        ),
        "product_transformation.svg": product_transformation_canvas(
            transformation, theme=theme, title=title
        ),
        "technology_shift.svg": technology_shift_canvas(
            TechnologyShift(production, factors),
            input_max,
            input_max / 2,
            theme=theme,
            title=title,
        ),
        "production_frontier.svg": production_frontier_canvas(
            frontier, input_max, point_names, theme=theme, title=title
        ),
    }
    paths = []
    for name, figure in figures.items():
        figure.save(output_dir / name)
        paths.append(output_dir / name)
    return paths


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument(
        "--learning", type=float, nargs=3, default=[2.0, 10.0, 0.45], help="A B beta"
    )
    args_parser.add_argument("--cumulative-max", type=float, default=60.0)
    args_parser.add_argument(
        "--cost", type=float, nargs=3, default=[10.0, 20.0, 0.02], help="c q0 k"
    )
    args_parser.add_argument("--learning-gain", type=float, default=0.3)
    args_parser.add_argument("--scale-range", type=float, nargs=2, default=[10.0, 26.0])
    args_parser.add_argument(
        "--transformation", type=float, nargs=3, default=[100.0, 100.0, 2.0], help="M1 M2 bow"
    )
    args_parser.add_argument(
        "--production", type=float, nargs=3, default=[2.0, 1.0, -0.06], help="a b c"
    )
    args_parser.add_argument("--factors", type=float, nargs="+", default=[1.0, 1.3, 1.6])
    args_parser.add_argument("--input-max", type=float, default=12.0)
    args_parser.add_argument(
        "--frontier", type=float, nargs=2, default=[10.0, 0.5], help="scale exponent"
    )
    args_parser.add_argument(
        "--interior", type=float, nargs="+", default=[3.0, 0.7, 8.0, 0.6], help="L efficiency pairs"
    )
    args_parser.add_argument("--point-names", nargs="+", default=["A", "B"])
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    session = Session(args)
    try:
        pairs = tuple(
            (args.interior[i], args.interior[i + 1]) for i in range(0, len(args.interior), 2)
        )
        extension_examples(
            args.output_dir,
            session.theme,
            learning=LearningCurve(*args.learning),
            cumulative_max=args.cumulative_max,
            cost=LearningAverageCost(*args.cost),
            learning_gain=args.learning_gain,
            scale_range=(args.scale_range[0], args.scale_range[1]),
            transformation=ProductTransformation(*args.transformation),
            production=ShortRunProductionFunction(*args.production),
            factors=tuple(args.factors),
            input_max=args.input_max,
            frontier=ProductionFrontier(args.frontier[0], args.frontier[1], pairs),
            point_names=tuple(args.point_names),
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
