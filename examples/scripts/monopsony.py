"""Render monopsony and union figures: competitive pair, monopsony, DWL, union, two sectors."""

from __future__ import annotations

from pathlib import Path

from common import Session, parser

from micro_viz import (
    LinearSupply,
    LinearValue,
    Monopsonist,
    PlotTheme,
    TwoSectorLabor,
    UnionWageSetting,
    competitive_pair_canvas,
    monopoly_monopsony_pair_canvas,
    monopsony_canvas,
    monopsony_dwl_canvas,
    supply_elasticity_canvas,
    two_sector_labor_canvas,
    union_wage_canvas,
)


def monopsony_examples(
    output_dir: Path,
    theme: PlotTheme,
    *,
    value: LinearValue,
    supply: LinearSupply,
    elastic: LinearSupply,
    inelastic: LinearSupply,
    price: float,
    sector_2: LinearValue,
    total: float,
    union_wage: float,
    title: str | None = None,
) -> list[Path]:
    """Write the monopsony figures into ``output_dir`` and return their paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    model = Monopsonist(supply, value)
    figures = {
        "competitive_pair.svg": competitive_pair_canvas(value, supply, price, theme=theme),
        "monopsony.svg": monopsony_canvas(model, theme=theme, title=title),
        "monopoly_monopsony.svg": monopoly_monopsony_pair_canvas(model, theme=theme),
        "supply_elasticity.svg": supply_elasticity_canvas(value, (elastic, inelastic), theme=theme),
        "monopsony_dwl.svg": monopsony_dwl_canvas(model, theme=theme, title=title),
        "labor_monopsony.svg": monopsony_canvas(model, labor=True, theme=theme, title=title),
        "union.svg": union_wage_canvas(UnionWageSetting(value, supply), theme=theme, title=title),
        "two_sector.svg": two_sector_labor_canvas(
            TwoSectorLabor(value, sector_2, total), union_wage, theme=theme
        ),
    }
    paths = []
    for name, figure in figures.items():
        figure.save(output_dir / name)
        paths.append(output_dir / name)
    return paths


def main() -> None:
    args_parser = parser(__doc__)
    args_parser.add_argument("--value", type=float, nargs=2, default=[30.0, 1.0], help="a b")
    args_parser.add_argument("--supply", type=float, nargs=2, default=[2.0, 0.4], help="a b")
    args_parser.add_argument("--elastic", type=float, nargs=2, default=[8.0, 0.4], help="a b")
    args_parser.add_argument("--inelastic", type=float, nargs=2, default=[0.0, 2.0], help="a b")
    args_parser.add_argument("--price", type=float, default=12.0)
    args_parser.add_argument("--sector-2", type=float, nargs=2, default=[26.0, 1.0], help="a b")
    args_parser.add_argument("--total", type=float, default=30.0)
    args_parser.add_argument("--union-wage", type=float, default=18.0)
    args_parser.add_argument("--title", default=None)
    args = args_parser.parse_args()
    session = Session(args)
    try:
        monopsony_examples(
            args.output_dir,
            session.theme,
            value=LinearValue(*args.value),
            supply=LinearSupply(*args.supply),
            elastic=LinearSupply(*args.elastic),
            inelastic=LinearSupply(*args.inelastic),
            price=args.price,
            sector_2=LinearValue(*args.sector_2),
            total=args.total,
            union_wage=args.union_wage,
            title=args.title,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
