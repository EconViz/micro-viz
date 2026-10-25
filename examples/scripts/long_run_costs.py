"""Render long-run costs: LAC and LMC, and the plants whose SAC curves envelope LAC."""

from __future__ import annotations

from pathlib import Path

from common import Session, parser

from micro_viz import PlantFamily, PlotTheme, lac_lmc_canvas, plant_family_canvas


def long_run_examples(
    output_dir: Path,
    theme: PlotTheme,
    *,
    family: PlantFamily,
    sizes: tuple[float, ...],
    output_max: float,
    smc_for: tuple[int, ...],
    title: str | None = None,
) -> list[Path]:
    """Write the long-run cost figures into ``output_dir`` and return their paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    figures = {
        "lac_lmc.svg": lac_lmc_canvas(family, output_max, theme=theme, title=title),
        "short_run_envelope.svg": plant_family_canvas(
            family, sizes, output_max, smc_for=smc_for, theme=theme, title=title
        ),
    }
    paths = []
    for name, figure in figures.items():
        figure.save(output_dir / name)
        paths.append(output_dir / name)
    return paths


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument("--efficient-scale", type=float, default=10.0)
    args_parser.add_argument("--minimum-cost", type=float, default=4.0)
    args_parser.add_argument("--scale-curvature", type=float, default=0.15)
    args_parser.add_argument("--steepness", type=float, default=0.2)
    args_parser.add_argument("--sizes", type=float, nargs="+", default=[6.0, 10.0, 14.0])
    args_parser.add_argument(
        "--smc-for",
        type=int,
        nargs="*",
        default=[0, 1, 2],
        help="indices of the plants whose SMC is drawn",
    )
    args_parser.add_argument("--output-max", type=float, default=22.0)
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    session = Session(args)
    try:
        long_run_examples(
            args.output_dir,
            session.theme,
            family=PlantFamily(
                args.efficient_scale, args.minimum_cost, args.scale_curvature, args.steepness
            ),
            sizes=tuple(args.sizes),
            output_max=args.output_max,
            smc_for=tuple(args.smc_for),
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
