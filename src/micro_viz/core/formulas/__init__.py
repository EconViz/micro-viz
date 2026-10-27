"""micro-viz formula registry, parsing, and localized errors.

:mod:`micro_viz.core.expr` is generic. This module fills its registry for microeconomics (quantity
``Q`` in either case, price ``P``, the cost and demand names that may stand left of ``=``, the
functions ``exp``, ``ln`` and ``sqrt``), points its messages at the locale tables and turns the
engine's error into :class:`FormulaError`, which is also a :class:`~micro_viz.firm.costs.CostError`.
"""

from __future__ import annotations

from collections.abc import Mapping

from micro_viz.core.expr import ExprError, Expression, Limits, Registry, functions, parse
from micro_viz.core.i18n import LANGUAGES, text
from micro_viz.firm.costs.model import CostError

QUANTITY = "Q"
PRICE = "P"
"""The canonical names of the two variables."""
COST_HEADS = ("TC", "VC", "MC", "AC", "ATC", "AVC")
"""Names that may stand left of ``=`` in a cost formula."""
DEMAND_HEADS = (PRICE, QUANTITY)
"""Names that may stand left of ``=`` in a demand formula."""


def _language(language: str | None) -> str:
    if language is not None:
        return language if language in LANGUAGES else LANGUAGES[0]
    from micro_viz.core.config import default_theme

    return default_theme().language


def render_message(message_id: str, language: str | None, fields: Mapping[str, object]) -> str:
    """The text of an engine message id in ``language`` (the active theme's by default)."""
    return text(message_id, _language(language), **fields)


def _heads() -> dict[str, str]:
    heads = {name: name for name in (*COST_HEADS, PRICE)}
    heads.update({"p": PRICE, "q": QUANTITY, QUANTITY: QUANTITY})
    return heads


REGISTRY = Registry(
    variables={"Q": QUANTITY, "q": QUANTITY, "P": PRICE, "p": PRICE},
    functions={"exp": functions.EXP, "ln": functions.LN, "sqrt": functions.SQRT},
    heads=_heads(),
    symbols={QUANTITY: "Q", PRICE: "P"},
    limits=Limits(),
    messages=render_message,
)
"""The registry every micro-viz formula is read with."""


class FormulaError(CostError, ExprError):
    """A formula micro-viz cannot read, with a message in the figure language and a caret."""


def parse_formula(source: str, *, language: str | None = None) -> Expression:
    """Read a micro-viz formula (``TC = 200 + 120Q``, ``P = 100 - Q``, ``36Q + Q^2``).

    Raises :class:`FormulaError`, never a bare Python error, for anything unreadable.
    """
    try:
        return parse(source, REGISTRY, language=language)
    except ExprError as error:
        if isinstance(error, FormulaError):
            raise
        raise FormulaError(
            error.message_id,
            source=error.source,
            position=error.position,
            provider=render_message,
            language=language,
            **error.fields,
        ) from None


__all__ = [
    "COST_HEADS",
    "DEMAND_HEADS",
    "PRICE",
    "QUANTITY",
    "REGISTRY",
    "FormulaError",
    "parse_formula",
    "render_message",
]
