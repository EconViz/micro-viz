"""Render isoquants: a map, diminishing MRTS, substitutes, fixed proportions, returns to scale."""

from __future__ import annotations

from pathlib import Path

from common import Session, parser

from micro_viz import (
    CobbDouglas,
    FixedProportions,
    PerfectSubstitutes,
    PlotTheme,
    isoquant_map_canvas,
    mrts_steps_canvas,
    returns_to_scale_grid,
)


def floats(text: str) -> list[float]:
    """Numbers separated by spaces."""
    return [float(part) for part in text.split()]


def isoquant_examples(
    output_dir: Path,
    theme: PlotTheme,
    *,
    technology: CobbDouglas,
    outputs: list[float],
    bounds: tuple[float, float],
    steps: list[float],
    triangle: list[float],
    substitutes: PerfectSubstitutes,
    proportions: FixedProportions,
    increasing: CobbDouglas,
    scale_outputs: list[float],
    direction: tuple[float, float],
    title: str | None = None,
) -> list[Path]:
    """Write the isoquant figures into ``output_dir`` and return their paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    middle = outputs[len(outputs) // 2]
    figures = {
        "isoquant_map.svg": isoquant_map_canvas(
            technology, outputs, bounds, theme=theme, title=title
        ),
        "mrts_steps.svg": mrts_steps_canvas(
            technology, middle, steps, bounds, theme=theme, title=title
        ),
        "mrts_triangle.svg": mrts_steps_canvas(
            technology, middle, triangle, bounds, delta_labels=True, theme=theme, title=title
        ),
        "perfect_substitutes.svg": isoquant_map_canvas(
            substitutes, outputs, bounds, theme=theme, title=title
        ),
        "fixed_proportions.svg": isoquant_map_canvas(
            proportions, outputs, bounds, ray=True, theme=theme, title=title
        ),
        "returns_to_scale.svg": returns_to_scale_grid(
            (technology, increasing),
            (scale_outputs, scale_outputs),
            bounds,
            direction,
            theme=theme,
        ),
    }
    paths = []
    for name, figure in figures.items():
        figure.save(output_dir / name)
        paths.append(output_dir / name)
    return paths


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument("--labor-share", type=float, default=0.5)
    args_parser.add_argument("--capital-share", type=float, default=0.5)
    args_parser.add_argument("--increasing-shares", type=float, nargs=2, default=[0.65, 0.65])
    args_parser.add_argument("--outputs", default="4 6 8")
    args_parser.add_argument("--scale-outputs", default="2 4 6")
    args_parser.add_argument("--bounds", type=float, nargs=2, default=[12.0, 12.0])
    args_parser.add_argument("--steps", default="2 3.5 5.5 8")
    args_parser.add_argument("--triangle", default="3 6")
    args_parser.add_argument("--substitute-weights", type=float, nargs=2, default=[1.0, 1.0])
    args_parser.add_argument("--proportion-weights", type=float, nargs=2, default=[1.0, 1.0])
    args_parser.add_argument("--direction", type=float, nargs=2, default=[1.0, 1.0])
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    session = Session(args)
    try:
        isoquant_examples(
            args.output_dir,
            session.theme,
            technology=CobbDouglas(args.labor_share, args.capital_share),
            outputs=floats(args.outputs),
            bounds=(args.bounds[0], args.bounds[1]),
            steps=floats(args.steps),
            triangle=floats(args.triangle),
            substitutes=PerfectSubstitutes(*args.substitute_weights),
            proportions=FixedProportions(*args.proportion_weights),
            increasing=CobbDouglas(*args.increasing_shares),
            scale_outputs=floats(args.scale_outputs),
            direction=(args.direction[0], args.direction[1]),
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
