"""mosaickit figure builders for bundling in valuation space."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mosaickit import Canvas

from micro_viz.core.theme import PlotTheme
from micro_viz.firm.strategy.bundling.model import (
    BUNDLE,
    GOOD_1,
    GOOD_2,
    NONE,
    Offer,
    ValuationProfile,
    choice_regions,
)
from micro_viz.visuals.common import FIGURE_DPI, FIGURE_SIZE, MARGIN, Point, Texts, resolve_theme
from micro_viz.visuals.plane import Plane

TOLERANCE = 1e-9
SHADES = {NONE: "light", GOOD_1: "mid", GOOD_2: "mid", BUNDLE: "dark"}
"""Fill of each package region."""
NUMERALS = {GOOD_1: "I", GOOD_2: "II", BUNDLE: "III", NONE: "IV"}


def _plane(
    profile: ValuationProfile,
    prefix: str,
    theme: PlotTheme | None,
    labels: Mapping[str, str] | None,
    title: str | None,
    margin: float,
    size: tuple[float, float],
    dpi: int,
) -> Plane:
    texts = Texts(resolve_theme(theme), labels)
    return Plane(
        prefix=prefix,
        x_label=texts("bundling.axis.r1"),
        y_label=texts("bundling.axis.r2"),
        x_max=profile.reach,
        y_max=profile.reach,
        theme=theme,
        labels=labels,
        title=title,
        margin=margin,
        size=size,
        dpi=dpi,
    )


def _consumers(plane: Plane, profile: ValuationProfile, names: Sequence[str] | None) -> None:
    for index, (r1, r2) in enumerate(profile.points):
        name = names[index] if names and index < len(names) else None
        plane.point(r1, r2, name=name)


def _edges(plane: Plane, polygon: Sequence[Point], reach: float) -> None:
    """Thin solid borders of a region, except along the edges of the valuation square."""
    for a, b in zip(polygon, [*polygon[1:], polygon[0]], strict=True):
        on_box = any(
            abs(a[i] - edge) < TOLERANCE and abs(b[i] - edge) < TOLERANCE
            for i in (0, 1)
            for edge in (0.0, reach)
        )
        if not on_box and (abs(a[0] - b[0]) > TOLERANCE or abs(a[1] - b[1]) > TOLERANCE):
            plane.thin((a, b))


def _regions(
    plane: Plane,
    profile: ValuationProfile,
    offer: Offer,
    *,
    separate: bool,
    numbered: bool,
) -> None:
    for name, polygon in choice_regions(offer, profile.reach).items():
        if numbered:
            text = plane.t("bundling.numeral", numeral=NUMERALS[name])
        else:
            both = "bundling.region.both" if separate else "bundling.region.bundle"
            key = both if name == BUNDLE else f"bundling.region.{name}"
            text = plane.t(key)
        plane.area(polygon, text, shade=SHADES[name])
        _edges(plane, polygon, profile.reach)


def _marks(plane: Plane, profile: ValuationProfile, offer: Offer) -> None:
    reach = profile.reach
    if offer.price_1 is not None and offer.price_1 <= reach:
        plane.xmark(offer.price_1, plane.t("bundling.mark.p1"))
    if offer.price_2 is not None and offer.price_2 <= reach:
        plane.ymark(offer.price_2, plane.t("bundling.mark.p2"))
    if offer.price_bundle is not None and offer.price_bundle <= reach:
        plane.xmark(offer.price_bundle, plane.t("bundling.mark.pb"))
        plane.ymark(offer.price_bundle, plane.t("bundling.mark.pb"))


def _costs(plane: Plane, profile: ValuationProfile) -> None:
    reach = profile.reach
    if profile.cost_1 > 0:
        plane.guide((profile.cost_1, 0.0), (profile.cost_1, reach))
        plane.xmark(profile.cost_1, plane.t("bundling.mark.c1"))
    if profile.cost_2 > 0:
        plane.guide((0.0, profile.cost_2), (reach, profile.cost_2))
        plane.ymark(profile.cost_2, plane.t("bundling.mark.c2"))


def valuation_scatter_canvas(
    profile: ValuationProfile,
    names: Sequence[str] | None = None,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Consumers as points ``(r1, r2)`` in valuation space; ``names`` labels the first points."""
    plane = _plane(profile, "bundling.scatter", theme, labels, title, margin, size, dpi)
    _consumers(plane, profile, names)
    return plane.finish()


def separate_selling_regions_canvas(
    profile: ValuationProfile,
    offer: Offer,
    names: Sequence[str] | None = None,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """The four purchase regions cut by ``r1 = P1`` and ``r2 = P2`` (goods sold apart)."""
    plane = _plane(profile, "bundling.separate", theme, labels, title, margin, size, dpi)
    _regions(plane, profile, offer, separate=True, numbered=False)
    _marks(plane, profile, Offer(offer.price_1, offer.price_2))
    _consumers(plane, profile, names)
    return plane.finish()


def pure_bundling_canvas(
    profile: ValuationProfile,
    price: float,
    names: Sequence[str] | None = None,
    *,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Valuation space split by the diagonal ``r1 + r2 = P_B``: consumers above it buy."""
    plane = _plane(profile, "bundling.pure", theme, labels, title, margin, size, dpi)
    offer = Offer.pure(price)
    _regions(plane, profile, offer, separate=False, numbered=False)
    _marks(plane, profile, offer)
    _consumers(plane, profile, names)
    return plane.finish()


def mixed_bundling_canvas(
    profile: ValuationProfile,
    offer: Offer,
    names: Sequence[str] | None = None,
    *,
    numbered: bool = False,
    title: str | None = None,
    theme: PlotTheme | None = None,
    labels: Mapping[str, str] | None = None,
    margin: float = MARGIN,
    size: tuple[float, float] = FIGURE_SIZE,
    dpi: int = FIGURE_DPI,
) -> Canvas:
    """Regions of mixed bundling (goods at ``P1``, ``P2`` and the bundle at ``P_B``). With
    positive costs the cost lines are marked; ``numbered`` labels the regions I to IV."""
    plane = _plane(profile, "bundling.mixed", theme, labels, title, margin, size, dpi)
    _regions(plane, profile, offer, separate=False, numbered=numbered)
    _marks(plane, profile, offer)
    _costs(plane, profile)
    _consumers(plane, profile, names)
    return plane.finish()


__all__ = [
    "mixed_bundling_canvas",
    "pure_bundling_canvas",
    "separate_selling_regions_canvas",
    "valuation_scatter_canvas",
]
