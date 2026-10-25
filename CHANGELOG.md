# Changelog

All notable changes to this project are documented in this file.

## 0.2.0.dev0 - Unreleased

### Added

- State-claims figures: wider-spread defaults (loss probability 0.5, premiums 0.5 and 0.6, exponent 0.3), budget lines named at their upper-left ends and indifference curves at their lower-right ends; a test renders both figures with layout warnings as errors.
- Short-run envelope: SAC curves run across the whole output axis so they cross, SMC can be drawn for several plants (`smc_for` takes indices), tangency outputs are marked (`drops`).
- Natural monopoly: the loss label sits in the free part of the loss rectangle, left of MR, instead of a leader into the curves.
- Monopolistic competition: the short run is its own figure (`monopolistic_short_run_canvas`, `short_run.svg`) next to `long_run.svg`; the combined `short_and_long_run.svg` is no longer in the example.
- Monopoly totals name total revenue `TR`; the multiplant dashed level runs unbroken across all panels. `firm_demand_canvas` is removed (it did not show a difference worth a figure).
- Competition figures: no duplicate `p` in the market panel, dashed guides that lie on a solid line are dropped (their marks stay; `drop_covered_guides`), and industry supply is drawn as the firms' panels beside the industry panel (`industry_supply_panels`).
- Cost figures: AVC named at its right end, wider cubic AVC figure (`--avc-reach`), and `cost_curves_panels` so each panel of the cost-curves figure also stands alone.
- Marginal-return regions: shade is optional (`[micro.region] fill`), can stop at the curve (`extent`), and each region takes its own colour (`region_colors`).
- Auctions: first- and second-price bid functions, revenue equivalence, and a pooling signal figure (`Auction`, `bid_functions_canvas`, `revenue_equivalence_canvas`, `Signaling.pooling`).
- Uncertainty, second part: `StateClaims` (insurance with fair and unfair premiums), stochastic
  dominance of uniform lotteries and `TwoAssetFrontier` with `state_claims_canvas`,
  `stochastic_dominance_canvas` and `mean_variance_frontier_canvas`.
- Information economics: `micro_viz.information` (`LemonsMarket`, `Signaling`, `MoralHazard`,
  `BonusSchedule`, `EfficiencyWage`) with the matching canvases and the example `information.py`.
- Choice under uncertainty: `micro_viz.uncertainty` (`Gamble`, `IncomeUtility`, `MeanVarianceInvestor`,
  `RiskReturnLine`) with `utility_of_income_canvas`, `risk_premium_canvas`, `risk_attitude_canvas`,
  `risk_return_choice_canvas` and the example `uncertainty.py`.
- Exhaustible resource: `micro_viz.capital` (`ExhaustibleResourcePath`) with
  `resource_price_path_canvas` and the example `exhaustible_resource.py`.
- Vertical chains: `micro_viz.vertical` (`VerticalChain`, `transfer_pricing`) with
  `double_marginalization_canvas`, `integrated_firm_canvas`, `transfer_price_outside_market_canvas` and
  the example `vertical.py`.
- Advertising decision: `micro_viz.advertising` (`AdvertisingDecision`) with `advertising_effect_canvas` and
  the example `advertising.py`.
- Production extensions: learning curve, scale versus learning, product transformation curve,
  technology shift and production frontier in `micro_viz.production.extras` with the example
  `production_extensions.py`.
- Kinked demand, dominant firm and cartel with a competitive fringe in `micro_viz.oligopoly`
  (`KinkedDemand`, `DominantFirm`) with `kinked_demand_canvas`, `dominant_firm_canvas`,
  `cartel_elasticity_canvas` and the example `dominant_firm.py`.
- Time-based pricing: `IntertemporalPricing` and `PeakLoadPricing` in `micro_viz.pricing` with
  `intertemporal_pricing_canvas`, `peak_load_canvas` and the example `time_pricing.py`.
- Factor markets: derived demand (VMP, MRP), firm hiring, capital adjustment, industry and
  short-run/long-run input demand, factor-market equilibrium, economic rent and land rent in
  `micro_viz.factors` and the example `factor_markets.py`.
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
