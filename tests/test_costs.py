from __future__ import annotations

import math

import pytest

from micro_viz import (
    CostError,
    CostSegment,
    CubicCost,
    PiecewiseCost,
    analyze_costs,
)


@pytest.fixture  # type: ignore[untyped-decorator]
def cubic() -> CubicCost:
    return CubicCost(fixed_cost=50.0, linear=36.0, quadratic=-8.0, cubic=0.6)


@pytest.fixture  # type: ignore[untyped-decorator]
def stepped() -> PiecewiseCost:
    return PiecewiseCost((CostSegment(6.0, 11.4), CostSegment(9.0, 13.0)), fixed_cost=3.0)


@pytest.fixture  # type: ignore[untyped-decorator]
def kinked() -> PiecewiseCost:
    return PiecewiseCost(
        (
            CostSegment(5.0, 7.2, 0.05),
            CostSegment(8.2, 7.6, 0.1, 0.05),
            CostSegment(9.0, 8.8, 2.0),
        )
    )


def test_cubic_measures_follow_the_definitions(cubic: CubicCost) -> None:
    q = 4.0
    assert cubic.variable_cost(q) == pytest.approx(36 * q - 8 * q**2 + 0.6 * q**3)
    assert cubic.total_cost(q) == pytest.approx(50 + cubic.variable_cost(q))
    assert cubic.marginal_cost(q) == pytest.approx(36 - 16 * q + 1.8 * q**2)
    assert cubic.average_fixed_cost(q) == pytest.approx(50 / q)
    assert cubic.average_variable_cost(q) == pytest.approx(cubic.variable_cost(q) / q)
    assert cubic.average_total_cost(q) == pytest.approx(
        cubic.average_fixed_cost(q) + cubic.average_variable_cost(q)  # type: ignore[operator]
    )
    assert cubic.average_total_cost(0.0) is None
    assert cubic.average_variable_cost(0.0) is None and cubic.average_fixed_cost(0.0) is None


def test_marginal_cost_is_the_derivative_of_total_cost(cubic: CubicCost) -> None:
    for q in (0.5, 3.0, 8.0):
        step = 1e-6
        numeric = (cubic.total_cost(q + step) - cubic.total_cost(q - step)) / (2 * step)
        assert cubic.marginal_cost(q) == pytest.approx(numeric, rel=1e-6)


def test_mc_crosses_avc_and_atc_exactly_at_their_minima(cubic: CubicCost) -> None:
    low = cubic.minimum_average_variable_cost_output
    assert cubic.marginal_cost(low) == pytest.approx(cubic.average_variable_cost(low))
    high = cubic.minimum_average_total_cost_output
    assert cubic.marginal_cost(high) == pytest.approx(cubic.average_total_cost(high))
    assert low < high
    for q in (low - 0.2, low + 0.2):
        assert cubic.average_variable_cost(q) > cubic.average_variable_cost(low)  # type: ignore[operator]
    for q in (high - 0.2, high + 0.2):
        assert cubic.average_total_cost(q) > cubic.average_total_cost(high)  # type: ignore[operator]
    # MC lies below an average curve where it falls and above it where it rises
    assert cubic.marginal_cost(high - 1) < cubic.average_total_cost(high - 1)  # type: ignore[operator]
    assert cubic.marginal_cost(high + 1) > cubic.average_total_cost(high + 1)  # type: ignore[operator]


def test_minimum_marginal_cost_output_is_where_mc_is_lowest(cubic: CubicCost) -> None:
    q = cubic.minimum_marginal_cost_output
    assert q == pytest.approx(8.0 / (3 * 0.6))
    assert cubic.marginal_cost(q) < cubic.marginal_cost(q + 0.1)
    assert cubic.marginal_cost(q) < cubic.marginal_cost(q - 0.1)


def test_without_fixed_cost_both_minima_coincide() -> None:
    cost = CubicCost(fixed_cost=0.0, linear=36.0, quadratic=-8.0, cubic=0.6)
    assert cost.minimum_average_total_cost_output == cost.minimum_average_variable_cost_output


def test_cubic_with_nonnegative_quadratic_has_increasing_marginal_cost() -> None:
    cost = CubicCost(fixed_cost=10.0, linear=2.0, quadratic=1.0, cubic=0.5)
    assert cost.minimum_marginal_cost_output == 0.0
    assert cost.minimum_average_variable_cost_output == 0.0
    q = cost.minimum_average_total_cost_output
    assert cost.marginal_cost(q) == pytest.approx(cost.average_total_cost(q))


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    "arguments",
    [
        {"fixed_cost": -1.0},
        {"linear": 0.0},
        {"cubic": 0.0},
        {"quadratic": -100.0},
        {"linear": math.inf},
        {"output_symbol": " "},
    ],
)
def test_invalid_cubic_costs_are_rejected(arguments: dict[str, object]) -> None:
    defaults: dict[str, object] = {
        "fixed_cost": 1.0,
        "linear": 5.0,
        "quadratic": -1.0,
        "cubic": 0.5,
    }
    with pytest.raises(CostError):
        CubicCost(**{**defaults, **arguments})  # type: ignore[arg-type]


def test_negative_output_and_non_finite_output_are_rejected(cubic: CubicCost) -> None:
    with pytest.raises(CostError, match="nonnegative"):
        cubic.total_cost(-1.0)
    with pytest.raises(CostError, match="finite"):
        cubic.total_cost(math.nan)


def test_piecewise_variable_cost_integrates_marginal_cost(kinked: PiecewiseCost) -> None:
    steps = 20000
    top = 8.9
    total = 0.0
    width = top / steps
    for index in range(steps):
        total += kinked.marginal_cost((index + 0.5) * width) * width
    assert kinked.variable_cost(top) == pytest.approx(total, rel=1e-4)
    assert kinked.variable_cost(0.0) == 0.0


def test_stepped_cost_matches_the_hand_computed_bands(stepped: PiecewiseCost) -> None:
    assert stepped.variable_cost(6.0) == pytest.approx(11.4 * 6)
    assert stepped.variable_cost(9.0) == pytest.approx(11.4 * 6 + 13.0 * 3)
    assert stepped.average_variable_cost(4.0) == pytest.approx(11.4)
    assert stepped.average_variable_cost(9.0) == pytest.approx((11.4 * 6 + 39.0) / 9)
    assert stepped.total_cost(2.0) == pytest.approx(3.0 + 11.4 * 2)
    assert stepped.marginal_cost(5.9) == 11.4 and stepped.marginal_cost(6.0) == 13.0
    assert stepped.capacity == 9.0 and stepped.breakpoints == (6.0,)


def test_output_beyond_capacity_is_rejected(stepped: PiecewiseCost) -> None:
    with pytest.raises(CostError, match="capacity"):
        stepped.variable_cost(9.5)


def test_output_at_price_follows_the_price_bands(stepped: PiecewiseCost) -> None:
    assert stepped.output_at_price(10.0) == 0.0  # below the first marginal cost
    assert stepped.output_at_price(12.0) == 6.0  # between the steps: stop at the jump
    assert stepped.output_at_price(13.0) == 9.0  # at the second step: run it to capacity
    assert stepped.output_at_price(20.0) == 9.0


def test_output_at_price_solves_rising_marginal_cost(kinked: PiecewiseCost) -> None:
    for price in (7.5, 8.2, 9.5):
        q = kinked.output_at_price(price)
        if 0 < q < kinked.capacity and q not in kinked.breakpoints:
            assert kinked.marginal_cost(q) == pytest.approx(price, abs=1e-6)
    assert kinked.output_at_price(7.5) == 5.0  # inside the jump at the first breakpoint
    assert kinked.output_at_price(1.0) == 0.0


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    "segments",
    [
        (),
        (CostSegment(2.0, 5.0), CostSegment(2.0, 6.0)),
        (CostSegment(3.0, 5.0), CostSegment(2.0, 6.0)),
        (CostSegment(2.0, 5.0, -1.0),),
        (CostSegment(2.0, 5.0), CostSegment(4.0, 4.0)),
    ],
)
def test_invalid_piecewise_costs_are_rejected(segments: tuple[CostSegment, ...]) -> None:
    with pytest.raises(CostError):
        PiecewiseCost(segments)


def test_invalid_segments_are_rejected() -> None:
    with pytest.raises(CostError):
        CostSegment(0.0, 1.0)
    with pytest.raises(CostError):
        CostSegment(1.0, -1.0)
    with pytest.raises(CostError):
        PiecewiseCost((CostSegment(1.0, 1.0),), fixed_cost=-1.0)
    with pytest.raises(CostError):
        PiecewiseCost((CostSegment(1.0, 1.0),), output_symbol="")


def test_analysis_samples_every_measure_and_the_minima(cubic: CubicCost) -> None:
    analysis = analyze_costs(cubic, output_range=(1.0, 11.0), samples=101)
    assert len(analysis.points) == 101
    first, last = analysis.points[0], analysis.points[-1]
    assert (first.output, last.output) == (1.0, 11.0)
    assert last.total_cost == pytest.approx(last.fixed_cost + last.variable_cost)
    assert analysis.minimum_average_total_cost is not None
    sampled = min(
        value for point in analysis.points if (value := point.average_total_cost) is not None
    )
    assert analysis.minimum_average_total_cost.value <= sampled + 1e-9
    assert analysis.minimum_average_variable_cost is not None
    assert analysis.minimum_marginal_cost is not None
    payload = analysis.to_dict()
    assert payload["cost"]["equation"].startswith("TC(Q)")  # type: ignore[index]
    assert len(payload["points"]) == 101  # type: ignore[arg-type]


def test_analysis_from_zero_leaves_averages_undefined(cubic: CubicCost) -> None:
    analysis = analyze_costs(cubic, output_range=(0.0, 5.0), samples=11)
    assert analysis.points[0].average_total_cost is None
    assert analysis.points[0].total_cost == cubic.fixed_cost


def test_piecewise_analysis_path_has_the_vertical_steps(stepped: PiecewiseCost) -> None:
    analysis = analyze_costs(stepped, output_range=(0.0, 9.0), samples=19)
    path = analysis.marginal_cost_path
    jump = [index for index in range(1, len(path)) if path[index][0] == path[index - 1][0]]
    assert len(jump) == 1
    assert path[jump[0] - 1][1] == 11.4 and path[jump[0]][1] == 13.0
    assert analysis.minimum_average_total_cost is None
    assert analysis.to_dict()["cost"]["capacity"] == 9.0  # type: ignore[index]


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    "arguments",
    [
        {"output_range": (0.0, math.inf)},
        {"output_range": (-1.0, 5.0)},
        {"output_range": (5.0, 5.0)},
        {"output_range": (0.0, 5.0), "samples": 1},
        {"output_range": (0.0, 5.0), "samples": True},
    ],
)
def test_invalid_analysis_inputs_are_rejected(
    cubic: CubicCost, arguments: dict[str, object]
) -> None:
    with pytest.raises(CostError):
        analyze_costs(cubic, **arguments)  # type: ignore[arg-type]


def test_range_beyond_capacity_is_rejected(stepped: PiecewiseCost) -> None:
    with pytest.raises(CostError, match="capacity"):
        analyze_costs(stepped, output_range=(0.0, 10.0))


def test_serialization_documents_the_conventions(cubic: CubicCost, kinked: PiecewiseCost) -> None:
    assert "sign_convention" in cubic.to_dict()
    assert kinked.to_dict()["segments"][1]["start"] == 5.0  # type: ignore[index]
