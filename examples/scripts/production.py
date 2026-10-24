"""Render short-run TP, AP, and MP diagrams with marginal-return regions."""

from __future__ import annotations

import argparse
from pathlib import Path

from micro_viz import (
    Config,
    ShortRunProductionFunction,
    analyze_production,
    average_marginal_product_canvas,
    total_product_canvas,
)


def production_examples(output_dir: Path) -> tuple[Path, Path]:
    """Write the two manual-theme production examples into ``output_dir``."""
    production = ShortRunProductionFunction(linear=6.0, quadratic=3.0, cubic=-0.5)
    analysis = analyze_production(production, input_range=(0.0, 6.0), samples=241)
    theme = Config.from_dict({"base": "manual"}).theme
    output_dir.mkdir(parents=True, exist_ok=True)
    total_output = output_dir / "total_product.svg"
    products_output = output_dir / "average_marginal_product.svg"
    total_product_canvas(analysis, theme=theme).save(total_output)
    average_marginal_product_canvas(analysis, theme=theme).save(products_output)
    return total_output, products_output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parents[1] / "output",
    )
    args = parser.parse_args()
    production_examples(args.output_dir)


if __name__ == "__main__":
    main()
