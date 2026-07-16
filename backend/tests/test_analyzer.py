"""Unit tests for recommendation rules and boundary behavior."""

from decimal import Decimal

from app.models import CreativeStatus
from app.services.analyzer import AnalyzerThresholds, Performance, analyze, percent_change

THRESHOLDS = AnalyzerThresholds(
    ctr_drop_pct=Decimal("20"),
    cpa_increase_pct=Decimal("30"),
    minimum_roas=Decimal("2"),
    maximum_frequency=Decimal("3.5"),
    spend_threshold=Decimal("2000"),
)


def performance(
    *,
    spend: str = "1000",
    revenue: str = "3000",
    impressions: int = 10000,
    clicks: int = 200,
    purchases: int = 10,
    reach: int = 5000,
) -> Performance:
    return Performance(
        spend=Decimal(spend),
        revenue=Decimal(revenue),
        impressions=impressions,
        clicks=clicks,
        purchases=purchases,
        reach=reach,
    )


def test_healthy_when_no_rule_matches() -> None:
    result = analyze(performance(), performance(), THRESHOLDS)
    assert result.status is CreativeStatus.HEALTHY
    assert result.reasons == ()


def test_single_signal_is_watch() -> None:
    current = performance(clicks=150, revenue="3000")
    baseline = performance(clicks=200)
    result = analyze(current, baseline, THRESHOLDS)
    assert result.status is CreativeStatus.WATCH
    assert result.reasons[0].startswith("CTR down")


def test_two_signals_are_turn_off_recommendation() -> None:
    current = performance(spend="1500", revenue="1500", clicks=150, purchases=10)
    baseline = performance(spend="1000", revenue="3000", clicks=200, purchases=10)
    result = analyze(current, baseline, THRESHOLDS)
    assert result.status is CreativeStatus.TURN_OFF_RECOMMENDATION
    assert len(result.reasons) >= 2


def test_zero_purchase_spend_rule_is_critical() -> None:
    result = analyze(
        performance(spend="2000.01", revenue="0", purchases=0),
        performance(),
        THRESHOLDS,
    )
    assert result.status is CreativeStatus.TURN_OFF_RECOMMENDATION
    assert result.critical is True


def test_threshold_is_strictly_greater_than() -> None:
    current = performance(clicks=160)
    baseline = performance(clicks=200)
    result = analyze(current, baseline, THRESHOLDS)
    assert all(not reason.startswith("CTR down") for reason in result.reasons)


def test_percent_change_handles_zero_baseline() -> None:
    assert percent_change(Decimal("1"), Decimal(0)) is None
