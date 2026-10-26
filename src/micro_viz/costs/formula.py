"""``Cost``: a short-run cost function written the way a textbook writes it.

::

    Cost("TC = 200 + 120Q - 18Q^2 + Q^3")
    Cost("VC = 120Q - 18Q^2 + Q^3", fixed=200)
    Cost("MC = 120 - 36Q + 3Q^2", fixed=200)
    Cost("ATC = 200/Q + 120 - 18Q + Q^2")
    Cost.polynomial(200, 120, -18, 1)              # ascending coefficients
    Cost.from_table(q=[0, 1, 2, 3], tc=[10, 18, 24, 33])

A formula is read by :mod:`micro_viz.expr` (nothing is evaluated as Python). ``Cost`` keeps the
exact total, variable and marginal cost as expressions, so derivatives and integrals are exact
and the lowest AVC and ATC are closed-form where the algebra allows and found by bisection to
machine precision otherwise. A cubic with the sign pattern of :class:`~micro_viz.costs.CubicCost`
is evaluated through a ``CubicCost`` internally, so both give the same numbers.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

from micro_viz.costs.model import CostError, CostFunction, CubicCost, Extremum
from micro_viz.expr import ExprError, Expression
from micro_viz.formulas import (
    COST_HEADS,
    QUANTITY,
    REGISTRY,
    FormulaError,
    parse_formula,
    render_message,
)

_TOL = 1e-9
_SCAN_START = 1e-6
_SCAN_STOP = 1e9
_SCAN_FACTOR = 1.02
_BISECT_ROUNDS = 200
_GRID = 1201


def _say(key: str, language: str | None = None, **fields: object) -> str:
    return render_message(key, language, fields)


def _bisect(function: Callable[[float], float], low: float, high: float) -> float:
    """The root of ``function`` between ``low`` (negative) and ``high`` (nonnegative)."""
    for _ in range(_BISECT_ROUNDS):
        middle = (low + high) / 2
        if middle in (low, high):
            break
        if function(middle) < 0:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def _upcrossing(function: Callable[[float], float]) -> float | None:
    """The smallest ``q > 0`` where ``function`` goes from negative to nonnegative.

    ``0.0`` when it is not negative just above zero, ``None`` when it never crosses.
    """
    q = _SCAN_START
    try:
        if function(q) >= 0:
            return 0.0
        while q < _SCAN_STOP:
            nxt = q * _SCAN_FACTOR
            if function(nxt) >= 0:
                return _bisect(function, q, nxt)
            q = nxt
    except (ArithmeticError, ValueError, ExprError):
        return None
    return None


class Cost(CostFunction):
    """A cost function from a formula, coefficients or a table (see the module docstring).

    ``formula`` names what it defines on the left of ``=``: ``TC``, ``VC``, ``MC``, ``AC`` or
    ``ATC`` (average total) and ``AVC``; a bare right-hand side means ``TC``. ``fixed`` is the
    fixed cost for forms that do not contain it (``VC``, ``MC``, ``AVC``); without it the fixed
    cost is zero and :attr:`warnings` says so. ``output_symbol`` is the letter the figures print
    for output; the letter in the formula (``Q`` or ``q``) is only how you typed it.
    """

    _tc_expr: Expression | None
    _vc_expr: Expression | None
    _mc_expr: Expression | None
    _vc_numeric: Callable[[float], float]
    _cubic: CubicCost | None
    _table: tuple[tuple[float, ...], tuple[float, ...]] | None
    warnings: tuple[str, ...]

    def __init__(
        self,
        formula: str | Expression,
        *,
        fixed: float | None = None,
        output_symbol: str = "Q",
        language: str | None = None,
    ) -> None:
        expression = (
            formula
            if isinstance(formula, Expression)
            else parse_formula(formula, language=language)
        )
        head = expression.head or "TC"
        if head not in COST_HEADS:
            allowed = ", ".join(COST_HEADS)
            raise CostError(_say("cost.error.bad_head", language, name=head, allowed=allowed))
        names = expression.variables
        if names - {QUANTITY}:
            raise CostError(_say("cost.error.variable", language, names=", ".join(sorted(names))))
        self._setup(head, expression, fixed, output_symbol, language)

    # ---- construction ----
    def _setup(
        self,
        head: str,
        expression: Expression,
        fixed: float | None,
        symbol: str,
        language: str | None,
    ) -> None:
        if not symbol.strip():
            raise CostError(_say("cost.error.symbol", language))
        self.output_symbol = symbol
        self._language = language
        self._table = None
        self._vc_numeric = _no_numeric
        warnings: list[str] = []
        q = Expression.variable(QUANTITY, REGISTRY)
        given = None if fixed is None else float(fixed)
        if given is not None and not math.isfinite(given):
            raise CostError(_say("cost.error.not_finite", language, name="fixed"))
        mc_expr: Expression | None = None
        vc_expr: Expression | None
        tc_expr: Expression | None
        try:
            if head in ("TC", "AC", "ATC"):
                tc_expr = expression if head == "TC" else q * expression
                fc = self._constant_term(tc_expr, language)
                if given is not None and abs(given - fc) > _TOL * (1 + abs(fc)):
                    raise CostError(
                        _say("cost.error.fixed_conflict", language, fixed=given, value=fc)
                    )
                vc_expr = tc_expr - fc
            elif head in ("VC", "AVC"):
                vc_expr = expression if head == "VC" else q * expression
                start = self._constant_term(vc_expr, language)
                if abs(start) > _TOL * (1 + abs(start)):
                    raise CostError(_say("cost.error.vc_not_zero", language, value=start))
                fc = given if given is not None else 0.0
                if given is None:
                    warnings.append(_say("cost.warning.no_fixed", language))
                tc_expr = vc_expr + fc
            else:  # MC
                mc_expr = expression
                fc = given if given is not None else 0.0
                if given is None:
                    warnings.append(_say("cost.warning.no_fixed", language))
                try:
                    vc_expr = expression.integral()
                except ExprError:
                    vc_expr = None

                    def numeric(x: float, e: Expression = expression) -> float:
                        return e.integral_between(0.0, x)

                    self._vc_numeric = numeric
                tc_expr = None if vc_expr is None else vc_expr + fc
        except ExprError as error:
            raise _as_cost_error(error, language) from None
        if fc < 0:
            raise CostError(_say("cost.error.negative_fixed", language, value=fc))
        self.fixed_cost = float(fc)
        self._tc_expr = tc_expr
        self._vc_expr = vc_expr
        if mc_expr is None:
            assert vc_expr is not None
            mc_expr = vc_expr.derivative()
        self._mc_expr = mc_expr
        self.warnings = tuple(warnings)
        self._cubic = self._cubic_core()
        self._check_finite_at_zero()

    @staticmethod
    def _constant_term(expression: Expression, language: str | None) -> float:
        poly = expression.coefficients()
        if poly is not None:
            if any(k < 0 for k in poly):
                raise CostError(_say("cost.error.undefined_at_zero", language))
            return poly.get(0.0, 0.0)
        try:
            return expression(0.0)
        except ExprError:
            raise CostError(_say("cost.error.undefined_at_zero", language)) from None

    def _check_finite_at_zero(self) -> None:
        try:
            self.marginal_cost(0.0)
        except (ExprError, ArithmeticError, ValueError):
            raise CostError(_say("cost.error.undefined_at_zero", self._language)) from None

    def _cubic_core(self) -> CubicCost | None:
        poly = self._vc_expr.coefficients() if self._vc_expr is not None else None
        if poly is None or not poly or any(k not in (1.0, 2.0, 3.0) for k in poly):
            return None
        try:
            return CubicCost(
                fixed_cost=self.fixed_cost,
                linear=poly.get(1.0, 0.0),
                quadratic=poly.get(2.0, 0.0),
                cubic=poly.get(3.0, 0.0),
                output_symbol=self.output_symbol,
            )
        except CostError:
            return None

    @classmethod
    def polynomial(
        cls, *coefficients: float, output_symbol: str = "Q", language: str | None = None
    ) -> Cost:
        """``TC`` from coefficients in ascending order: ``Cost.polynomial(200, 120, -18, 1)`` is
        ``200 + 120Q - 18Q^2 + Q^3`` (the first is the fixed cost)."""
        if not coefficients:
            raise CostError(_say("cost.error.coefficients", language))
        if any(isinstance(c, bool) or not math.isfinite(float(c)) for c in coefficients):
            raise CostError(_say("cost.error.not_finite", language, name="coefficients"))
        expression = Expression.from_polynomial(
            {float(k): float(c) for k, c in enumerate(coefficients)}, QUANTITY, REGISTRY
        )
        return cls(expression, output_symbol=output_symbol, language=language)

    @classmethod
    def from_table(
        cls,
        *,
        q: Sequence[float],
        tc: Sequence[float],
        output_symbol: str = "Q",
        language: str | None = None,
    ) -> Cost:
        """Total cost from a schedule: ``q`` starts at 0 and increases, ``tc`` has the same length.

        Cost between rows is interpolated linearly, so marginal cost is a step: the extra cost
        per unit over the interval that starts at the row.
        """
        outputs = tuple(float(x) for x in q)
        totals = tuple(float(x) for x in tc)
        bad = (
            len(outputs) != len(totals)
            or len(outputs) < 2
            or outputs[0] != 0
            or any(b <= a for a, b in zip(outputs, outputs[1:], strict=False))
            or any(not math.isfinite(x) for x in (*outputs, *totals))
        )
        if bad:
            raise CostError(_say("cost.error.table", language))
        if totals[0] < 0:
            raise CostError(_say("cost.error.negative_fixed", language, value=totals[0]))
        if any(b < a for a, b in zip(totals, totals[1:], strict=False)):
            raise CostError(_say("cost.error.table_decreasing", language))
        self = cls.__new__(cls)
        self.output_symbol = output_symbol
        self._language = language
        self._table = (outputs, totals)
        self.fixed_cost = totals[0]
        self._tc_expr = self._vc_expr = self._mc_expr = None
        self._vc_numeric = _no_numeric
        self._cubic = None
        self.warnings = ()
        return self

    # ---- the cost curves ----
    @property
    def capacity(self) -> float:
        """The largest output (the last row of a table; unbounded for a formula)."""
        return self._table[0][-1] if self._table else math.inf

    @property
    def formula(self) -> str:
        """Total cost as a formula, or a description of the table."""
        if self._tc_expr is not None:
            return f"TC = {self._tc_expr}"
        if self._table is not None:
            return f"TC from a table of {len(self._table[0])} rows"
        return f"MC = {self._mc_expr}"

    def expression(self, kind: str) -> Expression | None:
        """The exact ``tc``, ``vc`` or ``mc`` as an :class:`~micro_viz.expr.Expression` (``None``
        for a table, or for ``tc`` and ``vc`` when an MC has no closed-form integral)."""
        found = {"tc": self._tc_expr, "vc": self._vc_expr, "mc": self._mc_expr}
        if kind not in found:
            raise ValueError("kind must be 'tc', 'vc' or 'mc'")
        return found[kind]

    def _interp(self, q: float) -> tuple[float, float]:
        assert self._table is not None
        outputs, totals = self._table
        lo, hi = 0, len(outputs) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if outputs[mid] <= q:
                lo = mid
            else:
                hi = mid
        slope = (totals[lo + 1] - totals[lo]) / (outputs[lo + 1] - outputs[lo])
        return totals[lo] + slope * (q - outputs[lo]), slope

    def variable_cost(self, output: float) -> float:
        q = self._output(output)
        if self._table is not None:
            return self._interp(q)[0] - self.fixed_cost
        if self._cubic is not None:
            return self._cubic.variable_cost(q)
        if self._vc_expr is not None:
            return self._vc_expr(q)
        return self._vc_numeric(q)

    def marginal_cost(self, output: float) -> float:
        q = self._output(output)
        if self._table is not None:
            return self._interp(min(q, self._table[0][-1] * (1 - 1e-15)))[1]
        if self._cubic is not None:
            return self._cubic.marginal_cost(q)
        assert self._mc_expr is not None
        return self._mc_expr(q)

    # short names
    def tc(self, q: float) -> float:
        """Total cost ``TC(q)``."""
        return self.total_cost(q)

    def vc(self, q: float) -> float:
        """Variable cost ``VC(q)``."""
        return self.variable_cost(q)

    def mc(self, q: float) -> float:
        """Marginal cost ``MC(q)``."""
        return self.marginal_cost(q)

    def atc(self, q: float) -> float | None:
        """Average total cost ``TC/q`` (``None`` at zero output)."""
        return self.average_total_cost(q)

    ac = atc

    def avc(self, q: float) -> float | None:
        """Average variable cost ``VC/q`` (``None`` at zero output)."""
        return self.average_variable_cost(q)

    def afc(self, q: float) -> float | None:
        """Average fixed cost ``FC/q`` (``None`` at zero output)."""
        return self.average_fixed_cost(q)

    @property
    def fc(self) -> float:
        """The fixed cost ``FC = TC(0)``."""
        return self.fixed_cost

    # ---- extreme points ----
    def min_mc(self) -> Extremum | None:
        """Where marginal cost is lowest, or ``None`` when it never falls first."""
        if self._cubic is not None:
            q = self._cubic.minimum_marginal_cost_output
        elif self._mc_expr is not None:
            slope = self._mc_expr.derivative()
            q_found = _upcrossing(lambda x: slope(x))
            q = q_found if q_found is not None else 0.0
        else:
            return None
        return Extremum(q, self.marginal_cost(q)) if q > 0 else None

    def min_avc(self) -> Extremum | None:
        """Where average variable cost is lowest (``MC = AVC`` there), or ``None`` when it is
        lowest at zero output."""
        if self._table is not None:
            return self._table_minimum(self.average_variable_cost)
        if self._cubic is not None:
            q = self._cubic.minimum_average_variable_cost_output
        else:
            q = _upcrossing(lambda x: x * self.marginal_cost(x) - self.variable_cost(x)) or 0.0
        return Extremum(q, self.variable_cost(q) / q) if q > 0 else None

    def min_atc(self) -> Extremum | None:
        """Where average total cost is lowest (``MC = ATC`` there), or ``None`` when it keeps
        falling."""
        if self._table is not None:
            return self._table_minimum(self.average_total_cost)
        if self._cubic is not None:
            q = self._cubic.minimum_average_total_cost_output
        elif self.fixed_cost > 0 and (found := self._quadratic_atc_minimum()) is not None:
            q = found
        else:
            q_found = _upcrossing(lambda x: x * self.marginal_cost(x) - self.total_cost(x))
            if q_found is None:
                return None
            q = q_found
        return Extremum(q, self.total_cost(q) / q) if q > 0 else None

    def _quadratic_atc_minimum(self) -> float | None:
        poly = self._tc_expr.coefficients() if self._tc_expr is not None else None
        if poly is None or set(poly) - {0.0, 1.0, 2.0} or poly.get(2.0, 0.0) <= 0:
            return None
        return math.sqrt(self.fixed_cost / poly[2.0])

    def _table_minimum(self, unit: Callable[[float], float | None]) -> Extremum | None:
        assert self._table is not None
        rows = [(x, unit(x)) for x in self._table[0] if x > 0]
        best = min(rows, key=lambda row: float(row[1]))  # type: ignore[arg-type]
        return Extremum(best[0], float(best[1]))  # type: ignore[arg-type]

    def shutdown_price(self) -> float:
        """The lowest average variable cost: below this price the firm produces nothing."""
        lowest = self.min_avc()
        return lowest.value if lowest is not None else self.marginal_cost(0.0)

    def breakeven_price(self) -> float | None:
        """The lowest average total cost, or ``None`` when ATC has no lowest point."""
        lowest = self.min_atc()
        return lowest.value if lowest is not None else None

    def output_at_price(self, price: float) -> float:
        """The profit-maximising output where ``price`` meets MC on its rising part (zero when
        the price is below MC everywhere)."""
        value = float(price)
        if self._table is not None:
            outputs, totals = self._table
            best = max(range(len(outputs)), key=lambda i: (value * outputs[i] - totals[i], -i))
            return outputs[best]
        if self._cubic is not None:
            b, c, d = self._cubic.linear, self._cubic.quadratic, self._cubic.cubic
            discriminant = 4 * c * c - 12 * d * (b - value)
            return (
                0.0 if discriminant < 0 else max(0.0, (-2 * c + math.sqrt(discriminant)) / (6 * d))
            )
        lowest = self.min_mc()
        floor = lowest.output if lowest is not None else 0.0
        if value < self.marginal_cost(floor):
            return 0.0
        high = max(1.0, 2 * floor)
        for _ in range(80):
            if self.marginal_cost(high) >= value:
                break
            high *= 2
        else:
            raise CostError(_say("cost.error.unbounded", self._language, price=value))
        return (
            _bisect(lambda x: self.marginal_cost(x) - value, floor, high)
            if self.marginal_cost(floor) < value
            else floor
        )

    # ---- checks ----
    def validate(self, output: tuple[float, float]) -> None:
        """Check the cost against economics over the output range ``(low, high)``.

        Fixed cost is not negative (checked when the cost is built), marginal cost is positive
        everywhere on the range, and so ``AVC <= ATC`` and total cost rises. Raises
        :class:`~micro_viz.costs.CostError` naming the interval of output where it fails.
        """
        low, high = float(output[0]), float(output[1])
        steps = _GRID - 1
        grid = [low + (high - low) * i / steps for i in range(_GRID)]
        bad = [x for x in grid if self.marginal_cost(x) <= 0]
        if not bad:
            return
        start = bad[0]
        index = grid.index(start)
        if index > 0:
            start = _edge(self.marginal_cost, grid[index - 1], start)
        stop = bad[-1]
        index = grid.index(stop)
        if index < steps:
            stop = _edge(self.marginal_cost, grid[index + 1], stop)
        raise CostError(
            _say(
                "cost.error.mc_not_positive",
                self._language,
                symbol=self.output_symbol,
                low=start,
                high=stop,
                at=bad[len(bad) // 2],
                mc=self.marginal_cost(bad[len(bad) // 2]),
            )
        )

    # ---- derived costs ----
    def with_unit_tax(self, tax: float) -> Cost:
        """The cost with a per-unit tax: ``TC`` rises by ``tax * Q``."""
        shift = float(tax)
        if not math.isfinite(shift):
            raise CostError(_say("cost.error.not_finite", self._language, name="tax"))
        if self._table is not None:
            outputs, totals = self._table
            return Cost.from_table(
                q=outputs,
                tc=[t + shift * x for x, t in zip(outputs, totals, strict=True)],
                output_symbol=self.output_symbol,
                language=self._language,
            )
        if self._tc_expr is not None:
            q = Expression.variable(QUANTITY, REGISTRY)
            return Cost(
                self._tc_expr + shift * q, output_symbol=self.output_symbol, language=self._language
            )
        assert self._mc_expr is not None
        return Cost(
            _with_head(self._mc_expr + shift, "MC"),
            fixed=self.fixed_cost,
            output_symbol=self.output_symbol,
            language=self._language,
        )

    def without_fixed_cost(self) -> Cost:
        """The same variable cost with ``FC = 0`` (the long-run-like form some figures need)."""
        if self._tc_expr is not None:
            return Cost(
                self._tc_expr - self.fixed_cost,
                output_symbol=self.output_symbol,
                language=self._language,
            )
        if self._table is not None:
            outputs, totals = self._table
            return Cost.from_table(
                q=outputs,
                tc=[t - self.fixed_cost for t in totals],
                output_symbol=self.output_symbol,
                language=self._language,
            )
        assert self._mc_expr is not None
        return Cost(
            _with_head(self._mc_expr, "MC"),
            fixed=0.0,
            output_symbol=self.output_symbol,
            language=self._language,
        )

    def as_cubic(self) -> CubicCost | None:
        """The equivalent :class:`~micro_viz.costs.CubicCost` when the cost has that shape."""
        return self._cubic

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "equation": self.formula,
            "fixed_cost": self.fixed_cost,
            "output_symbol": self.output_symbol,
        }
        if self._table is not None:
            data["table"] = {"q": list(self._table[0]), "tc": list(self._table[1])}
        return data

    def __repr__(self) -> str:
        return f"Cost({self.formula!r})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Cost)
            and self.formula == other.formula
            and self.fixed_cost == other.fixed_cost
            and self.output_symbol == other.output_symbol
            and self._table == other._table
        )

    def __hash__(self) -> int:
        return hash((self.formula, self.fixed_cost, self.output_symbol))


def _no_numeric(x: float) -> float:
    return 0.0


def _with_head(expression: Expression, head: str) -> Expression:
    return Expression(expression.node, expression.registry, head=head)


def _edge(function: Callable[[float], float], good: float, bad: float) -> float:
    """The boundary between a point where ``function > 0`` (``good``) and one where it does not."""
    for _ in range(_BISECT_ROUNDS):
        middle = (good + bad) / 2
        if middle in (good, bad):
            break
        if function(middle) > 0:
            good = middle
        else:
            bad = middle
    return (good + bad) / 2


def _as_cost_error(error: ExprError, language: str | None) -> CostError:
    return FormulaError(
        error.message_id,
        source=error.source,
        position=error.position,
        provider=render_message,
        language=language,
        **error.fields,
    )


__all__ = ["Cost"]
