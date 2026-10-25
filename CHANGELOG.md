# Changelog

All notable changes to this project are documented in this file.

## 0.2.0.dev0 - Unreleased

### Changed

- Restyled the TP and AP/MP figures to the `principle-viz` manual look: greys from the
  shared `manual` theme, direct curve names, shaded and named marginal-return regions, dashed
  drop lines with axis marks at the MP maximum, the AP = MP point and the MP = 0 point.
- Nothing is hard-coded: titles default to `None`, axis names, texts, ranges, sizes and styles are
  arguments or `[micro.*]` settings; built-in text comes from a locale table (en, zh-TW, zh-CN).
- Examples take their output directory, settings, fonts and model parameters from arguments.

### Added

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
