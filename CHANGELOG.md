# Changelog

All notable changes to this project are documented in this file.

## 0.2.0.dev0 - Unreleased

### Added

- Short-run perfect competition: `micro_viz.competition` (firm decision, shutdown and break-even
  prices, firm and industry supply, producer surplus, unit tax) with figure builders
  `competitive_firm_canvas`, `firm_supply_canvas`, `producer_surplus_canvas`,
  `cost_shift_canvas`, `revenue_cost_profit_canvas`, `industry_supply_canvas`,
  `market_and_firm_canvas` and `examples/scripts/competition.py`.

### Changed

- Variable names are uppercase italic except the price `p` (`Q`, `C`).

### Changed

- Region braces of the TP and AP/MP figures hang inside the plot exactly under their shaded
  regions (`[micro.brace] gap` points below), single row, with the region names kept short in the
  locale table.
- Restyled the TP and AP/MP figures to the `principle-viz` manual look: greys from the
  shared `manual` theme, direct curve names, shaded and named marginal-return regions, dashed
  drop lines with axis marks at the MP maximum, the AP = MP point and the MP = 0 point.
- Nothing is hard-coded: titles default to `None`, axis names, texts, ranges, sizes and styles are
  arguments or `[micro.*]` settings; built-in text comes from a locale table (en, zh-TW, zh-CN).
- Examples take their output directory, settings, fonts and model parameters from arguments.

### Added

- Short-run costs (#11): `CubicCost`, `PiecewiseCost` (stepped and kinked marginal cost with a
  capacity), `analyze_costs`, and the `total_cost_canvas`, `unit_cost_canvas`, `cost_curves_grid`
  and `piecewise_cost_canvas` builders with price bands, minimum-point guides and an optional
  marked output; examples and an animation of output and price sweeps.
- Optional `micro-viz[animation]` extra (kinetickit): `micro_viz.animation.save_svg` and `save_gif`
  animate any figure through its own canvas builder; an architecture test keeps static figures
  independent of kinetickit.
- `[micro]` settings: `language`, `color`, `stroke`, `marker`, `opacity` and `label.<group>`.
- `ProductionAnalysis.average_product_max_input` (the AP = MP input).
- Typed, renderer-neutral short-run cubic production functions and TP/AP/MP analysis.
- Exact increasing, diminishing, and negative marginal-return regions.
- MosaicKit TP and AP/MP visual builders with stable `micro.production.*` layer IDs.
- Executable black-and-white production examples with ignored generated output.

## 0.1.0.dev0 - Unreleased

### Added

- Initial uv package scaffold for Python 3.10 and later.
- MosaicKit configuration entry point with the shared colour default theme on a white canvas.
- Architecture, configuration, and rendering tests.
