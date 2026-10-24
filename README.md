# micro-viz

`micro-viz` is the EconViz package for producer theory, costs, firm behaviour,
market structure, nonlinear pricing, factor demand, uncertainty, and information
economics. The first production milestone provides typed short-run TP, AP, and MP
analysis according to the [roadmap](https://github.com/EconViz/micro-viz/issues/2).

## Boundaries

- `micro-viz` owns firm-side and market-structure analysis.
- [`utility-viz`](https://github.com/EconViz/utility-viz) owns consumer theory and
  general equilibrium.
- [`principle-viz`](https://github.com/EconViz/principle-viz) owns introductory
  demand-and-supply policy diagrams, externalities, and public goods.
- Game theory is outside this package.
- [`mosaickit`](https://github.com/EconViz/mosaickit) owns scenes, layers, themes,
  layout, and rendering backends.

Domain models and solvers must remain renderer-neutral. Visual builders compile typed
economic results into public MosaicKit layers, and only MosaicKit talks to a backend.

### Dependency boundary

P0 directly depends only on MosaicKit. GlyphKit remains MosaicKit's transitive text layer;
`micro-viz` does not declare it separately. BezierKit becomes a direct dependency only when an
isoquant, implicit-path, or TikZ milestone consumes its public geometry API. KineticKit remains
absent until `micro-viz` exposes animation publicly; that milestone should add the optional
`kinetickit[raster]` extra following `utility-viz`. This keeps each dependency tied to an actual
public capability instead of installing the whole lower-level stack in advance.

## Short-run production

`ShortRunProductionFunction` uses the textbook cubic equation
`Q(L) = aL + bL^2 + cL^3`, with `a >= 0`, `b > 0`, and `c < 0`. The analysis reports
sampled total, average, and marginal products plus exact boundaries for increasing,
diminishing, and negative marginal returns.

```python
from micro_viz import (
    ShortRunProductionFunction,
    analyze_production,
    average_marginal_product_canvas,
    total_product_canvas,
)

production = ShortRunProductionFunction(linear=6, quadratic=3, cubic=-0.5)
result = analyze_production(production, input_range=(0, 6))

total_product_canvas(result, title="Total product").save("total-product.svg")
average_marginal_product_canvas(result, title=None).save("products.svg")
```

The returned `ProductionAnalysis` is renderer-neutral and `to_dict()` includes the equation,
coefficient sign convention, sampled values, and return-region boundaries. Visual layers use
stable `micro.production.*` IDs and roles.

## Install

`micro-viz` requires Python 3.10 or later.

```bash
uv add micro-viz
```

For a source checkout:

```bash
git clone https://github.com/EconViz/micro-viz.git
cd micro-viz
uv sync --frozen
```

## Shared settings

Every EconViz diagram package reads the same `econ-viz.toml`. `micro-viz` declares its
configuration schema to MosaicKit and does not parse TOML itself. With no settings file,
figures use the same colour `default` theme as `principle-viz`, always on a white background.
Manuals, documentation, and bundled examples explicitly select the black-and-white `manual`
theme. Shared settings such as `base`, fonts,
axis and label colours, and per-figure label nudges work across installed EconViz packages.

```toml
base = "manual"

[font]
text = "serif"

[color]
axis = "#1a1a1a"
label = "#1a1a1a"
```

Package-specific options, once introduced by real diagram features, will live below
`[micro.*]`. Unknown settings are rejected instead of being silently ignored.

## Examples

Bundled examples explicitly select the black-and-white `manual` theme. Generated SVG files
stay local under `examples/output/` and are ignored by Git.

```bash
uv run python examples/scripts/production.py
uv run python examples/scripts/smoke.py
```

The production script writes `total_product.svg` and `average_marginal_product.svg`. The smoke
figure deliberately has no title by default; pass `--title` to exercise its optional title.

## Development

```bash
uv run ruff check src tests examples/scripts
uv run ruff format --check src tests examples/scripts
uv run mypy
uv run pytest
uv build
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for architecture and pull-request conventions.
