"""Counts of the expensive steps, not wall time: a regression shows as a larger count."""

from __future__ import annotations

import pytest

import micro_viz.bundling.model as bundling
from micro_viz import Offer, ValuationProfile, best_mixed, evaluate_offer

PROFILES = (
    ValuationProfile.correlated(16, low=10.0, high=90.0, direction=-1.0, spread=8.0),
    ValuationProfile.correlated(
        16, low=10.0, high=90.0, direction=1.0, spread=5.0, cost_1=15.0, cost_2=7.0
    ),
)


@pytest.mark.parametrize("profile", PROFILES)  # type: ignore[untyped-decorator]
def test_scoring_an_offer_equals_the_outcome_profit_exactly(profile: ValuationProfile) -> None:
    offers = (
        Offer.separate(30.0, 41.5),
        Offer.pure(77.0),
        Offer.mixed(60.0, 55.0, 90.0),
        Offer(None, 40.0, None),
    )
    for offer in offers:
        assert bundling._profit(profile, offer) == evaluate_offer(profile, offer).profit


@pytest.mark.parametrize("profile", PROFILES)  # type: ignore[untyped-decorator]
def test_the_mixed_search_builds_only_a_few_outcomes(
    profile: ValuationProfile, monkeypatch: pytest.MonkeyPatch
) -> None:
    built = 0
    original = bundling.evaluate_offer

    def counting(profile: ValuationProfile, offer: Offer) -> bundling.BundlingOutcome:
        nonlocal built
        built += 1
        return original(profile, offer)

    monkeypatch.setattr(bundling, "evaluate_offer", counting)
    best_mixed(profile)
    assert built <= 3  # the best separate, the best pure and the winner; never one per trial
