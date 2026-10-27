"""Renderer-neutral product-bundling domain models.

Each consumer has reservation prices ``(r1, r2)`` for goods 1 and 2. An *option* is a package
(good 1, good 2 or both) with a price; a consumer takes the option with the largest surplus
``sum(r_i for the goods in it) - price`` and buys nothing when every surplus is negative.
Separate selling offers goods 1 and 2 (and their sum, priced ``P1 + P2``); pure bundling offers
only the bundle at ``P_B``; mixed bundling offers all three at independent prices.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import product

from micro_viz.firm.competition import CompetitionError

Point = tuple[float, float]
CANDIDATES = 40
"""Largest number of distinct trial prices per good in the mixed-bundling search."""
RADIX = 3
"""Base of the van der Corput sequence that offsets the generated points."""

NONE, GOOD_1, GOOD_2, BUNDLE = "none", "good_1", "good_2", "bundle"


def _radical_inverse(index: int, base: int = RADIX) -> float:
    """The van der Corput value of ``index`` in ``base``: digits mirrored about the point."""
    result, scale = 0.0, 1.0 / base
    while index:
        index, digit = divmod(index, base)
        result += digit * scale
        scale /= base
    return result


class BundlingError(CompetitionError):
    """Raised when a bundling input is invalid."""


@dataclass(frozen=True, slots=True)
class ValuationProfile:
    """Consumers' reservation prices ``(r1, r2)`` and the constant marginal costs of the goods."""

    points: tuple[Point, ...]
    cost_1: float = 0.0
    cost_2: float = 0.0

    def __post_init__(self) -> None:
        if not self.points:
            raise BundlingError("At least one consumer is required.")
        if any(not math.isfinite(v) or v < 0 for pair in self.points for v in pair):
            raise BundlingError("Reservation prices must be finite and nonnegative.")
        if self.cost_1 < 0 or self.cost_2 < 0:
            raise BundlingError("Marginal costs must be nonnegative.")

    @property
    def reach(self) -> float:
        """The largest reservation price of either good."""
        return max(max(pair) for pair in self.points)

    @classmethod
    def correlated(
        cls,
        count: int,
        *,
        low: float,
        high: float,
        direction: float,
        spread: float,
        cost_1: float = 0.0,
        cost_2: float = 0.0,
    ) -> ValuationProfile:
        """``count`` consumers spread between ``low`` and ``high`` for good 1; good 2 follows the
        same ordering when ``direction`` is positive and the reverse ordering when negative, plus
        a deterministic offset of at most ``spread`` (a van der Corput sequence, not random)."""
        if count < 2 or high <= low or spread < 0:
            raise BundlingError("Need count >= 2, high > low and spread >= 0.")
        sign = 1.0 if direction >= 0 else -1.0
        pts = []
        for i in range(count):
            t = low + (high - low) * i / (count - 1)
            mate = t if sign > 0 else high + low - t
            offset = spread * (2.0 * _radical_inverse(i + 1) - 1.0)
            pts.append((t, min(max(mate + offset, 0.0), high)))
        return cls(tuple(pts), cost_1, cost_2)


@dataclass(frozen=True, slots=True)
class Offer:
    """Prices of the offered packages; ``None`` means the package is not sold."""

    price_1: float | None = None
    price_2: float | None = None
    price_bundle: float | None = None

    def options(self) -> dict[str, tuple[float, float, float]]:
        """Package name -> (weight of r1, weight of r2, price), including buying nothing."""
        found: dict[str, tuple[float, float, float]] = {NONE: (0.0, 0.0, 0.0)}
        if self.price_1 is not None:
            found[GOOD_1] = (1.0, 0.0, self.price_1)
        if self.price_2 is not None:
            found[GOOD_2] = (0.0, 1.0, self.price_2)
        if self.price_bundle is not None:
            found[BUNDLE] = (1.0, 1.0, self.price_bundle)
        return found

    @classmethod
    def separate(cls, price_1: float, price_2: float) -> Offer:
        """Goods sold apart; a consumer taking both pays ``P1 + P2``."""
        return cls(price_1, price_2, price_1 + price_2)

    @classmethod
    def pure(cls, price_bundle: float) -> Offer:
        return cls(None, None, price_bundle)

    @classmethod
    def mixed(cls, price_1: float, price_2: float, price_bundle: float) -> Offer:
        return cls(price_1, price_2, price_bundle)


def choice(offer: Offer, r1: float, r2: float) -> str:
    """The package a consumer with reservation prices ``(r1, r2)`` takes (ties favour the
    cheaper-to-serve package in the order none, good 1, good 2, bundle)."""
    best, best_surplus = NONE, 0.0
    for name, (w1, w2, price) in offer.options().items():
        surplus = w1 * r1 + w2 * r2 - price
        if surplus > best_surplus + 1e-12:
            best, best_surplus = name, surplus
    return best


@dataclass(frozen=True, slots=True)
class BundlingOutcome:
    """Result of an offer: who buys what and the seller's profit."""

    offer: Offer
    choices: tuple[str, ...]
    revenue: float
    cost: float

    @property
    def profit(self) -> float:
        return self.revenue - self.cost

    def count(self, package: str) -> int:
        return sum(1 for c in self.choices if c == package)


def evaluate_offer(profile: ValuationProfile, offer: Offer) -> BundlingOutcome:
    """Profit of ``offer`` against the profile."""
    options = offer.options()
    picks = tuple(choice(offer, r1, r2) for r1, r2 in profile.points)
    revenue = sum(options[p][2] for p in picks)
    cost = sum(options[p][0] * profile.cost_1 + options[p][1] * profile.cost_2 for p in picks)
    return BundlingOutcome(offer, picks, revenue, cost)


def _profit(profile: ValuationProfile, offer: Offer) -> float:
    """``evaluate_offer(profile, offer).profit`` without building the outcome.

    The same surpluses, tie rule (none, good 1, good 2, bundle; a later package must beat the
    best by more than ``1e-12``) and summation order as :func:`choice` and
    :func:`evaluate_offer`, so the value is identical; the search below calls it tens of
    thousands of times. The package weights are 0 or 1, so a surplus is ``r1 - P1``,
    ``r2 - P2`` or ``(r1 + r2) - P_B`` exactly, and a package costs ``c1``, ``c2`` or ``c1 + c2``.
    """
    p1, p2, pb = offer.price_1, offer.price_2, offer.price_bundle
    c1, c2 = profile.cost_1, profile.cost_2
    cb = 1.0 * c1 + 1.0 * c2
    revenue: list[float] = []
    cost: list[float] = []
    for r1, r2 in profile.points:
        price, served, surplus = 0.0, 0.0, 0.0
        if p1 is not None:
            gain = r1 - p1
            if gain > surplus + 1e-12:
                price, served, surplus = p1, c1, gain
        if p2 is not None:
            gain = r2 - p2
            if gain > surplus + 1e-12:
                price, served, surplus = p2, c2, gain
        if pb is not None:
            gain = r1 + r2 - pb
            if gain > surplus + 1e-12:
                price, served, surplus = pb, cb, gain
        revenue.append(price)
        cost.append(served)
    return sum(revenue) - sum(cost)


def _grid(values: Sequence[float], floor: float) -> list[float]:
    found = sorted({max(v, floor) for v in values})
    if len(found) > CANDIDATES:
        step = (len(found) - 1) / (CANDIDATES - 1)
        found = [found[round(i * step)] for i in range(CANDIDATES)]
    return found


def best_separate(profile: ValuationProfile) -> BundlingOutcome:
    """The profit-maximising ``(P1, P2)``; each good is priced alone, so the search is separable."""
    best: Offer | None = None
    best_profit = 0.0
    for p1, p2 in product(
        _grid([r[0] for r in profile.points], profile.cost_1),
        _grid([r[1] for r in profile.points], profile.cost_2),
    ):
        offer = Offer.separate(p1, p2)
        profit = _profit(profile, offer)
        if best is None or profit > best_profit:
            best, best_profit = offer, profit
    assert best is not None
    return evaluate_offer(profile, best)


def best_pure(profile: ValuationProfile) -> BundlingOutcome:
    """The profit-maximising bundle price."""
    best: Offer | None = None
    best_profit = 0.0
    for price in _grid([sum(r) for r in profile.points], profile.cost_1 + profile.cost_2):
        offer = Offer.pure(price)
        profit = _profit(profile, offer)
        if best is None or profit > best_profit:
            best, best_profit = offer, profit
    assert best is not None
    return evaluate_offer(profile, best)


def best_mixed(profile: ValuationProfile) -> BundlingOutcome:
    """The profit-maximising ``(P1, P2, P_B)`` over trial prices drawn from the data. Mixed
    bundling nests separate selling (``P_B = P1 + P2``) and pure bundling (``P1, P2`` very high),
    so its profit is never below either."""
    top = max(best_separate(profile), best_pure(profile), key=lambda o: o.profit)
    top_profit = top.profit
    best: Offer | None = None
    for p1, p2, pb in product(
        _grid([r[0] for r in profile.points], profile.cost_1),
        _grid([r[1] for r in profile.points], profile.cost_2),
        _grid([sum(r) for r in profile.points], profile.cost_1 + profile.cost_2),
    ):
        offer = Offer.mixed(p1, p2, pb)
        profit = _profit(profile, offer)
        if profit > top_profit:
            best, top_profit = offer, profit
    return top if best is None else evaluate_offer(profile, best)


def _clip(polygon: list[Point], a: float, b: float, c: float) -> list[Point]:
    """Keep the part of ``polygon`` with ``a x + b y >= c`` (Sutherland-Hodgman)."""
    result: list[Point] = []
    for i, current in enumerate(polygon):
        previous = polygon[i - 1]
        f_cur = a * current[0] + b * current[1] - c
        f_prev = a * previous[0] + b * previous[1] - c
        if (f_cur >= 0) != (f_prev >= 0):
            t = f_prev / (f_prev - f_cur)
            result.append(
                (
                    previous[0] + t * (current[0] - previous[0]),
                    previous[1] + t * (current[1] - previous[1]),
                )
            )
        if f_cur >= 0:
            result.append(current)
    return result


def choice_regions(offer: Offer, reach: float) -> dict[str, tuple[Point, ...]]:
    """Package -> polygon of the valuation square ``[0, reach]^2`` where it is chosen. The
    regions follow from comparing surpluses, so they agree with :func:`choice` off the borders."""
    options = offer.options()
    box = [(0.0, 0.0), (reach, 0.0), (reach, reach), (0.0, reach)]
    regions: dict[str, tuple[Point, ...]] = {}
    for name, (w1, w2, price) in options.items():
        polygon = list(box)
        for other, (v1, v2, other_price) in options.items():
            if other != name:
                polygon = _clip(polygon, w1 - v1, w2 - v2, price - other_price)
                if not polygon:
                    break
        if len(polygon) >= 3:
            regions[name] = tuple(polygon)
    return regions
