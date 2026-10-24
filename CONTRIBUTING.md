# Contributing to micro-viz

Thank you for helping build `micro-viz`.

## Development setup

```bash
git clone https://github.com/EconViz/micro-viz.git
cd micro-viz
uv sync --frozen
```

Run every check before opening a pull request:

```bash
uv run ruff check src tests examples/scripts
uv run ruff format --check src tests examples/scripts
uv run mypy
uv run pytest
uv build
```

## Architecture

Every feature follows one direction:

```text
domain model -> solver or analysis -> typed result -> visual builder
             -> MosaicKit scene and layers -> renderer
```

- Keep domain models, solvers, and typed results independent of MosaicKit and rendering
  backends.
- Use public MosaicKit layers for visuals; do not import Matplotlib from `micro_viz`.
- Keep consumer theory and general equilibrium in `utility-viz`.
- Keep game theory outside this package.
- Put package settings below `[micro.*]`; MosaicKit owns parsing of `econ-viz.toml`.
- Give layers stable `micro.*` IDs and roles, and make figure titles optional.

## Pull requests

- Work from current `main` on a focused branch.
- Add numerical and visual-builder tests with each feature.
- Keep generated example output, caches, and build artifacts out of commits.
- Update the README or changelog when public behaviour changes.
- Include the commands run and an example figure in the pull-request description.

## License

Contributions are licensed under the [MIT License](LICENSE).
