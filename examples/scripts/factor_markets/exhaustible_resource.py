"""Render the exhaustible-resource price path and its static demand view."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import Session, parser

from micro_viz import ExhaustibleResourcePath, PlotTheme, resource_price_path_canvas


def resource_examples(
    output_dir: Path,
    theme: PlotTheme,
    *,
    path: ExhaustibleResourcePath,
    title: str | None = None,
) -> list[Path]:
    """Write the resource figure into ``output_dir`` and return its path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "resource_price_path.svg"
    resource_price_path_canvas(path, titles=(title, None), theme=theme).save(target)
    return [target]


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument("--demand", type=float, nargs=2, default=[100.0, 2.0], help="a b")
    args_parser.add_argument("--cost", type=float, default=10.0)
    args_parser.add_argument("--rate", type=float, default=0.05)
    args_parser.add_argument("--stock", type=float, default=600.0)
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    session = Session(args)
    try:
        resource_examples(
            args.output_dir,
            session.theme,
            path=ExhaustibleResourcePath(
                args.demand[0], args.demand[1], args.cost, args.rate, args.stock
            ),
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
