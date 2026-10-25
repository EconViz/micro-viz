from importlib.metadata import entry_points, version

import micro_viz


def test_version_matches_installed_metadata() -> None:
    assert micro_viz.__version__ == "0.2.0.dev0"
    assert version("micro-viz") == micro_viz.__version__


def test_config_entry_point_is_registered() -> None:
    matches = [entry for entry in entry_points(group="econviz.config") if entry.name == "micro"]
    assert len(matches) == 1
    assert matches[0].load() is micro_viz.Config


def test_public_api_is_explicit() -> None:
    assert set(micro_viz.__all__) == {
        "CompetitionError",
        "CompetitiveOutcome",
        "Config",
        "MonopolisticOutcome",
        "long_run_demand",
        "solve_monopolistic_competition",
        "CostAnalysis",
        "CostError",
        "CostFunction",
        "CostPoint",
        "CostSegment",
        "CubicCost",
        "Extremum",
        "FirmSupply",
        "IndustrySupply",
        "LinearDemand",
        "MarginalReturns",
        "Monopolist",
        "MonopolyError",
        "MonopolyOutcome",
        "MultiplantMonopoly",
        "MultiplantOutcome",
        "PiecewiseCost",
        "PlotTheme",
        "ProductionAnalysis",
        "ProductionError",
        "ProductionPoint",
        "Regime",
        "ReturnsRegion",
        "RevenueCostAnalysis",
        "RevenueCostPoint",
        "ShortRunProductionFunction",
        "__version__",
        "analyze_costs",
        "analyze_production",
        "analyze_revenue_cost",
        "average_marginal_product_canvas",
        "break_even_price",
        "competitive_firm_canvas",
        "cost_curves_grid",
        "cost_shift_canvas",
        "default_theme",
        "elasticity",
        "excess_capacity_grid",
        "firm_demand_canvas",
        "firm_supply_canvas",
        "industry_supply_canvas",
        "lerner_markup_canvas",
        "marginal_revenue",
        "market_and_firm_canvas",
        "monopolistic_competition_grid",
        "monopolistic_long_run_canvas",
        "monopoly_canvas",
        "monopoly_demand_shift_canvas",
        "monopoly_dwl_canvas",
        "monopoly_tax_canvas",
        "monopoly_totals_canvas",
        "monopoly_totals_grid",
        "multiplant_canvas",
        "piecewise_cost_canvas",
        "producer_surplus_canvas",
        "profit_maximizing_output",
        "revenue_cost_profit_canvas",
        "shared_theme",
        "shutdown_price",
        "solve_competitive_firm",
        "total_cost_canvas",
        "total_product_canvas",
        "unit_cost_canvas",
    }
