from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from micro_viz import (
    FactorError,
    LinearSupply,
    LinearValue,
    Monopsonist,
    TwoSectorLabor,
    UnionWageSetting,
    competitive_pair_canvas,
    monopoly_monopsony_pair_canvas,
    monopsony_canvas,
    monopsony_dwl_canvas,
    supply_elasticity_canvas,
    two_sector_labor_canvas,
    union_wage_canvas,
)

ROOT = Path(__file__).parents[1]
VALUE = LinearValue(30.0, 1.0)
SUPPLY = LinearSupply(4.0, 1.0)
MODEL = Monopsonist(SUPPLY, VALUE)
SECTORS = TwoSectorLabor(VALUE, LinearValue(26.0, 1.0), 30.0)


def test_monopsony_hires_where_me_equals_mv() -> None:
    result = MODEL.solve()
    assert SUPPLY.marginal_expenditure(result.quantity) == pytest.approx(result.marginal_value)
    assert result.wage == pytest.approx(SUPPLY.wage(result.quantity))


def test_monopsony_below_competitive_quantity_and_wage() -> None:
    result = MODEL.solve()
    assert result.quantity < result.competitive_quantity
    assert result.wage < result.competitive_wage
    assert result.transfer == pytest.approx(
        (result.competitive_wage - result.wage) * result.quantity
    )
    assert result.deadweight_loss > 0


def test_dwl_is_triangle_between_value_and_supply() -> None:
    result = MODEL.solve()
    q, qc = result.quantity, result.competitive_quantity
    gap = VALUE.value(q) - SUPPLY.wage(q)
    assert result.deadweight_loss == pytest.approx(0.5 * (qc - q) * gap)


def test_elastic_supply_keeps_me_close_to_ae() -> None:
    flat = LinearSupply(8.0, 0.4)
    steep = LinearSupply(0.0, 2.0)
    for supply in (flat, steep):
        outcome = Monopsonist(supply, VALUE).solve()
        assert outcome.marginal_expenditure > outcome.wage

    def gap(supply: LinearSupply) -> float:
        outcome = Monopsonist(supply, VALUE).solve()
        return (outcome.marginal_expenditure - outcome.wage) / outcome.wage

    assert gap(flat) < gap(steep)


def test_union_maximises_wage_bill_by_default() -> None:
    result = UnionWageSetting(VALUE, SUPPLY).solve()
    assert result.wage == pytest.approx(VALUE.intercept / 2)
    assert result.wage_bill == pytest.approx(result.wage * result.employment)
    assert result.rent == pytest.approx(
        result.wage_bill - (4.0 * result.employment + 0.5 * result.employment**2)
    )
    higher = UnionWageSetting(VALUE, SUPPLY).solve(20.0)
    assert higher.employment < result.competitive_employment


def test_two_sector_union_wage_moves_workers() -> None:
    wage, l1, l2 = SECTORS.competitive()
    assert l1 + l2 == pytest.approx(30.0)
    result = SECTORS.solve(wage + 3.0)
    assert result.employment_1 < l1
    assert result.employment_2 > l2
    assert result.wage_2 < wage
    assert result.employment_1 + result.employment_2 == pytest.approx(30.0)


def test_invalid_inputs() -> None:
    with pytest.raises(FactorError):
        LinearSupply(0.0, 0.0)
    with pytest.raises(FactorError):
        Monopsonist(LinearSupply(40.0, 1.0), VALUE)
    with pytest.raises(FactorError):
        UnionWageSetting(VALUE, SUPPLY).solve(100.0)
    with pytest.raises(FactorError):
        SECTORS.solve(1.0)


def test_canvases_follow_parameters() -> None:
    assert monopsony_canvas(MODEL, title="T").spec.title == "T"
    assert monopsony_canvas(MODEL, labor=True) is not None
    assert monopsony_dwl_canvas(MODEL) is not None
    assert union_wage_canvas(UnionWageSetting(VALUE, SUPPLY), 18.0) is not None
    assert competitive_pair_canvas(VALUE, SUPPLY, 12.0) is not None
    assert monopoly_monopsony_pair_canvas(MODEL) is not None
    assert supply_elasticity_canvas(VALUE, (LinearSupply(8.0, 0.4), LinearSupply(0.0, 2.0)))
    assert two_sector_labor_canvas(SECTORS, 18.0) is not None


def test_example_runs(tmp_path: Path) -> None:
    config = tmp_path / "econ-viz.toml"
    config.write_text('base = "manual"\n', encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "scripts" / "monopsony.py"),
            "--output-dir",
            str(tmp_path / "out"),
            "--config",
            str(config),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    assert (tmp_path / "out" / "union.svg").exists()
