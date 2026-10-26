"""Render kinked demand, dominant-firm and cartel-with-fringe figures."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import Session, parser

from micro_viz import (
    DominantFirm,
    KinkedDemand,
    PlotTheme,
    cartel_elasticity_canvas,
    dominant_firm_canvas,
    kinked_demand_canvas,
)


def dominant_examples(
    output_dir: Path,
    theme: PlotTheme,
    *,
    kinked: KinkedDemand,
    costs: tuple[float, ...],
    firm: DominantFirm,
    inelastic: DominantFirm,
    elastic: DominantFirm,
    title: str | None = None,
) -> list[Path]:
    """Write the dominant-firm figures into ``output_dir`` and return their paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    figures = {
        "kinked_demand.svg": kinked_demand_canvas(kinked, costs, theme=theme, title=title),
        "dominant_firm.svg": dominant_firm_canvas(firm, theme=theme, title=title),
        "cartel_fringe.svg": dominant_firm_canvas(
            firm, cartel=True, theme=theme, title=title, prefix="oligopoly.cartel"
        ),
        "cartel_elasticity.svg": cartel_elasticity_canvas(inelastic, elastic, theme=theme),
    }
    paths = []
    for name, figure in figures.items():
        figure.save(output_dir / name)
        paths.append(output_dir / name)
    return paths


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument(
        "--kink", type=float, nargs=4, default=[10.0, 20.0, 0.5, 1.5], help="Q P upper lower"
    )
    args_parser.add_argument("--kink-costs", type=float, nargs="+", default=[8.0, 12.0])
    args_parser.add_argument(
        "--firm",
        type=float,
        nargs=6,
        default=[40.0, 1.0, 6.0, 1.5, 4.0, 0.2],
        help="a b p0 e c0 c1",
    )
    args_parser.add_argument(
        "--inelastic", type=float, nargs=6, default=[30.0, 0.6, 6.0, 1.0, 4.0, 0.2]
    )
    args_parser.add_argument(
        "--elastic", type=float, nargs=6, default=[60.0, 2.5, 6.0, 1.0, 4.0, 0.2]
    )
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    session = Session(args)
    try:
        dominant_examples(
            args.output_dir,
            session.theme,
            kinked=KinkedDemand(*args.kink),
            costs=tuple(args.kink_costs),
            firm=DominantFirm(*args.firm),
            inelastic=DominantFirm(*args.inelastic),
            elastic=DominantFirm(*args.elastic),
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
