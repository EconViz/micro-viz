"""Render the advertising decision: AR shifts out, average cost rises, profit before and after."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import Session, parser

from micro_viz import (
    AdvertisingDecision,
    LinearDemand,
    PlotTheme,
    advertising_effect_canvas,
)


def advertising_examples(
    output_dir: Path,
    theme: PlotTheme,
    *,
    decision: AdvertisingDecision,
    title: str | None = None,
) -> list[Path]:
    """Write the advertising figure into ``output_dir`` and return its path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "advertising.svg"
    advertising_effect_canvas(decision, theme=theme, title=title).save(path)
    return [path]


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument("--baseline", type=float, nargs=2, default=[30.0, 1.0], help="a b")
    args_parser.add_argument("--advertised", type=float, nargs=2, default=[36.0, 1.0], help="a b")
    args_parser.add_argument("--marginal-cost", type=float, default=4.0)
    args_parser.add_argument("--fixed-cost", type=float, default=40.0)
    args_parser.add_argument("--advertising-cost", type=float, default=60.0)
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    session = Session(args)
    try:
        advertising_examples(
            args.output_dir,
            session.theme,
            decision=AdvertisingDecision(
                LinearDemand(*args.baseline),
                LinearDemand(*args.advertised),
                args.marginal_cost,
                args.fixed_cost,
                args.advertising_cost,
            ),
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
