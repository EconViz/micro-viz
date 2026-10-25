from __future__ import annotations

import math
from collections.abc import Mapping
from typing import cast

import pytest

from micro_viz import (
    MarginalReturns,
    ProductionError,
    ShortRunProductionFunction,
    analyze_production,
)


@pytest.fixture  # type: ignore[untyped-decorator]
def production() -> ShortRunProductionFunction:
    return ShortRunProductionFunction(linear=6.0, quadratic=3.0, cubic=-0.5)


def test_short_run_function_computes_tp_ap_and_mp(
    production: ShortRunProductionFunction,
) -> None:
    assert production.total_product(4.0) == pytest.approx(40.0)
    assert production.average_product(4.0) == pytest.approx(10.0)
    assert production.marginal_product(4.0) == pytest.approx(6.0)
    assert production.average_product(0.0) is None


def test_analysis_finds_the_three_marginal_return_regions(
    production: ShortRunProductionFunction,
) -> None:
    result = analyze_production(production, input_range=(0.0, 6.0), samples=7)

    assert result.inflection_input == pytest.approx(2.0)
    assert result.total_product_max_input == pytest.approx(2.0 + math.sqrt(8.0))
    assert tuple(region.kind for region in result.regions) == (
        MarginalReturns.INCREASING,
        MarginalReturns.DIMINISHING,
        MarginalReturns.NEGATIVE,
    )
    assert tuple((region.start_input, region.end_input) for region in result.regions) == (
        pytest.approx((0.0, 2.0)),
        pytest.approx((2.0, 2.0 + math.sqrt(8.0))),
        pytest.approx((2.0 + math.sqrt(8.0), 6.0)),
    )


def test_analysis_samples_endpoints_and_keeps_ap_undefined_at_zero(
    production: ShortRunProductionFunction,
) -> None:
    result = analyze_production(production, input_range=(0.0, 6.0), samples=4)

    assert tuple(point.variable_input for point in result.points) == pytest.approx(
        (0.0, 2.0, 4.0, 6.0)
    )
    assert result.points[0].total_product == pytest.approx(0.0)
    assert result.points[0].average_product is None
    assert result.points[1].marginal_product == pytest.approx(12.0)


def test_analysis_crops_regions_to_the_requested_input_range(
    production: ShortRunProductionFunction,
) -> None:
    result = analyze_production(production, input_range=(3.0, 4.0), samples=2)

    assert len(result.regions) == 1
    assert result.regions[0].kind is MarginalReturns.DIMINISHING
    assert (result.regions[0].start_input, result.regions[0].end_input) == pytest.approx((3.0, 4.0))


def test_serialized_result_documents_equation_and_sign_convention(
    production: ShortRunProductionFunction,
) -> None:
    payload = analyze_production(production, input_range=(0.0, 6.0), samples=3).to_dict()
    production_payload = cast(Mapping[str, object], payload["production_function"])
    regions = cast(list[dict[str, object]], payload["regions"])
    points = cast(list[dict[str, object]], payload["points"])

    assert production_payload == {
        "equation": "Q(L) = aL + bL^2 + cL^3",
        "sign_convention": "a >= 0, b > 0, c < 0",
        "coefficients": {"a": 6.0, "b": 3.0, "c": -0.5},
        "input_symbol": "L",
        "output_symbol": "Q",
    }
    assert regions[0]["kind"] == "increasing"
    assert points[0]["average_product"] is None


def test_serialized_equation_uses_custom_input_and_output_symbols() -> None:
    production = ShortRunProductionFunction(
        linear=1.0,
        quadratic=1.0,
        cubic=-0.1,
        input_symbol="N",
        output_symbol="Y",
    )

    assert production.to_dict()["equation"] == "Y(N) = aN + bN^2 + cN^3"


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    ("linear", "quadratic", "cubic", "message"),
    [
        (math.nan, 1.0, -1.0, "finite"),
        (-1.0, 1.0, -1.0, "linear"),
        (1.0, 0.0, -1.0, "quadratic"),
        (1.0, 1.0, 0.0, "cubic"),
    ],
)
def test_invalid_short_run_coefficients_are_rejected(
    linear: float, quadratic: float, cubic: float, message: str
) -> None:
    with pytest.raises(ProductionError, match=message):
        ShortRunProductionFunction(linear=linear, quadratic=quadratic, cubic=cubic)


def test_negative_or_nonfinite_input_is_rejected(
    production: ShortRunProductionFunction,
) -> None:
    with pytest.raises(ProductionError, match="nonnegative"):
        production.total_product(-1.0)
    with pytest.raises(ProductionError, match="finite"):
        production.marginal_product(math.inf)


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    ("input_range", "samples", "message"),
    [
        ((-1.0, 2.0), 3, "nonnegative"),
        ((2.0, 2.0), 3, "increasing"),
        ((0.0, math.inf), 3, "finite"),
        ((0.0, 2.0), 1, "at least 2"),
    ],
)
def test_invalid_analysis_inputs_are_rejected(
    production: ShortRunProductionFunction,
    input_range: tuple[float, float],
    samples: int,
    message: str,
) -> None:
    with pytest.raises(ProductionError, match=message):
        analyze_production(production, input_range=input_range, samples=samples)


def test_average_product_peaks_where_it_equals_marginal_product() -> None:
    function = ShortRunProductionFunction(linear=6.0, quadratic=3.0, cubic=-0.5)
    peak = function.average_product_max_input
    assert function.marginal_product(peak) == pytest.approx(function.average_product(peak))
    assert function.inflection_input < peak < function.total_product_max_input
    for step in (-0.01, 0.01):
        assert function.average_product(peak + step) < function.average_product(peak)  # type: ignore[operator]
