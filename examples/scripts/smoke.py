"""Render a minimal public-MosaicKit smoke figure."""

from __future__ import annotations

import argparse
from pathlib import Path

from mosaickit import Canvas, CanvasSpec, PathLayer, quadrant_axes

from micro_viz import default_theme


def smoke_canvas(*, title: str | None = None) -> Canvas:
    """Build a neutral line figure that exercises the rendering boundary."""
    spec = CanvasSpec(
        x_range=(0.0, 10.0),
        y_range=(0.0, 10.0),
        width=5.0,
        height=5.0,
        dpi=150,
        x_label="",
        y_label="",
        title=title,
    )
    theme = default_theme()
    canvas = Canvas(spec=spec, config=theme.mosaickit_config())
    canvas.extend(quadrant_axes(10.0, 10.0))
    canvas.add(
        PathLayer(
            ((1.0, 2.0), (5.0, 7.0), (9.0, 4.0)),
            id="micro.scaffold.curve",
            role="micro.scaffold.curve",
        )
    )
    return canvas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parents[1] / "output" / "smoke.svg",
    )
    parser.add_argument("--title", default=None)
    args = parser.parse_args()
    smoke_canvas(title=args.title).save(args.output)


if __name__ == "__main__":
    main()
