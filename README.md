# micro-viz

`micro-viz` is the EconViz package for producer theory, costs, firm behaviour,
market structure, nonlinear pricing, factor demand, uncertainty, and information
economics. The project is in its initial scaffold stage; economic models will be
added incrementally according to the [roadmap](https://github.com/EconViz/micro-viz/issues/2).

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

## Scaffold example

The smoke example verifies the public MosaicKit scene-to-renderer path without inventing
an economic model. Like all bundled examples, it explicitly uses the `manual` theme:

```bash
uv run python examples/scripts/smoke.py
```

It writes `examples/output/smoke.svg`. The figure deliberately has no title by default;
pass `--title` to exercise the optional title parameter.

## Development

```bash
uv run ruff check src tests examples/scripts
uv run ruff format --check src tests examples/scripts
uv run mypy
uv run pytest
uv build
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for architecture and pull-request conventions.
