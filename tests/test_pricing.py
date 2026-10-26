from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from micro_viz import (
    BuyerType,
    LinearDemand,
    PricingError,
    best_tariff,
    evaluate_tariff,
    tariff_profit_canvas,
    two_part_tariff_canvas,
)

ROOT = Path(__file__).parents[1]
ONE = BuyerType(LinearDemand(30.0, 1.0))
TWO = (BuyerType(LinearDemand(30.0, 1.0), 1.0), BuyerType(LinearDemand(20.0, 1.0), 3.0))


def test_single_buyer_prices_at_marginal_cost() -> None:
    outcome = best_tariff((ONE,), 4.0)
    assert outcome.usage_fee == pytest.approx(4.0)
    assert outcome.entry_fee == pytest.approx(ONE.surplus(4.0))
    assert outcome.sales_profit == pytest.approx(0.0)


def test_two_types_use_price_above_cost() -> None:
    outcome = best_tariff(TWO, 4.0)
    assert outcome.usage_fee > 4.0
    assert outcome.entry_fee == pytest.approx(TWO[1].surplus(outcome.usage_fee))
    assert outcome.profit > evaluate_tariff(TWO, 4.0, 4.0, TWO[1].surplus(4.0)).profit


def test_high_entry_fee_prices_out_buyers() -> None:
    assert evaluate_tariff(TWO, 4.0, 6.0, 1000.0).entrants == 0


def test_invalid_inputs() -> None:
    with pytest.raises(PricingError):
        BuyerType(LinearDemand(30.0, 1.0), 0.0)
    with pytest.raises(PricingError):
        best_tariff((), 4.0)
    with pytest.raises(PricingError):
        evaluate_tariff(TWO, -1.0, 6.0, 1.0)


def test_canvases_build() -> None:
    outcome = best_tariff(TWO, 4.0)
    assert two_part_tariff_canvas(TWO, outcome) is not None
    assert tariff_profit_canvas(TWO, 4.0, 6.5, 120.0) is not None


def test_example_runs(tmp_path: Path) -> None:
    config = tmp_path / "econ-viz.toml"
    config.write_text('base = "manual"\n', encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "scripts" / "pricing" / "two_part_tariff.py"),
            "--output-dir",
            str(tmp_path / "out"),
            "--config",
            str(config),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    assert (tmp_path / "out" / "tariff_profit.svg").exists()
