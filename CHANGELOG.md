# Changelog

All notable changes to this project are documented in this file.

## 0.2.0.dev0 - Unreleased

### Added

- Monopsony and unions: `micro_viz.factors` (`Monopsonist`, `UnionWageSetting`, `TwoSectorLabor`) with
  `competitive_pair_canvas`, `monopsony_canvas`, `monopoly_monopsony_pair_canvas`,
  `supply_elasticity_canvas`, `monopsony_dwl_canvas`, `union_wage_canvas`, `two_sector_labor_canvas` and
  the example `monopsony.py`.
- Oligopoly: `micro_viz.oligopoly` (`Duopoly`, `cournot`, `stackelberg`, `DifferentiatedDuopoly`,
  `bertrand`) with `residual_demand_canvas`, `reaction_curves_canvas`, `price_reaction_canvas` and the
  example `oligopoly.py`.
- Bundling in valuation space: `micro_viz.bundling` (`ValuationProfile`, `Offer`, `choice_regions`,
  `best_separate`, `best_pure`, `best_mixed`) with `valuation_scatter_canvas`,
  `separate_selling_regions_canvas`, `pure_bundling_canvas`, `mixed_bundling_canvas` and the example
  `bundling.py`.
- Two-part tariff: `micro_viz.pricing` (`BuyerType`, `TariffOutcome`, `best_tariff`) with
  `two_part_tariff_canvas`, `tariff_profit_canvas` and the example `two_part_tariff.py`.
- Price discrimination: `micro_viz.discrimination` (first degree, block pricing, third degree) with
  `single_price_canvas`, `first_degree_canvas`, `block_pricing_canvas`, `third_degree_canvas` and the
  example `price_discrimination.py`.
- Cost minimization: isocost lines, cost-minimizing bundles, expansion paths and long-run total cost
  (`cost_minimization_canvas`, `input_price_change_canvas`, `technical_change_canvas`,
  `expansion_path_canvas`, `fixed_capital_canvas`, example `cost_minimization.py`).
- Long-run competition: `micro_viz.entry` (`IndustryEntry`: entry, exit, long-run supply) with
  `long_run_firm_canvas`, `entry_canvas`, `rent_canvas`, `constant_cost_canvas`,
  `increasing_cost_canvas` and the example `long_run_competition.py`.
- Long-run costs: `micro_viz.longrun` (`PlantFamily`: SAC, LAC envelope, LMC) with `lac_lmc_canvas`,
  `plant_family_canvas` and the example `long_run_costs.py`; the shared `Plane` drawing kit.
- Isoquants: `micro_viz.isoquant` (`CobbDouglas`, `PerfectSubstitutes`, `FixedProportions`, MRTS,
  returns to scale) with `isoquant_map_canvas`, `mrts_steps_canvas`, `returns_to_scale_grid` and the
  example `isoquants.py`.
- Monopoly regulation: `micro_viz.regulation` (price ceiling, natural-monopoly pricing) with
  `price_ceiling_canvas`, `natural_monopoly_canvas` and the example `regulation.py`.
- Monopolistic competition: `micro_viz.monopolistic` (short run, long-run tangency, excess
  capacity) with `monopolistic_competition_grid`, `monopolistic_long_run_canvas`,
  `excess_capacity_grid` and the examples `monopolistic_competition.py` and
  `animate_monopolistic.py`.
- Monopoly: `micro_viz.monopoly` (`Monopolist`, `MultiplantMonopoly`, Lerner index, deadweight
  loss) with `monopoly_canvas`, `monopoly_dwl_canvas`, `monopoly_tax_canvas`,
  `monopoly_demand_shift_canvas`, `multiplant_canvas`, `lerner_markup_canvas`,
  `firm_demand_canvas`, `monopoly_totals_canvas`, `monopoly_totals_grid`, the example
  `monopoly.py` and the animation `animate_monopoly.py`.
- Short-run perfect competition: `micro_viz.competition` (firm decision, shutdown and break-even
  prices, firm and industry supply, producer surplus, unit tax) with figure builders
  `competitive_firm_canvas`, `firm_supply_canvas`, `producer_surplus_canvas`,
  `cost_shift_canvas`, `revenue_cost_profit_canvas`, `industry_supply_canvas`,
  `market_and_firm_canvas` and `examples/scripts/competition.py`.

### Changed

- Curves after a change and movement arrows are thin and solid (1.5 pt and 1.2 pt against 3.5 pt
  for main curves), set by `[micro.stroke] after` and `arrow`.
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
