"""Contract tests for Meta insight normalization."""

from decimal import Decimal

from app.integrations.meta import MetaClient


def test_parse_insight_extracts_purchase_facts() -> None:
    insight = MetaClient._parse_insight(
        {
            "ad_id": "123",
            "date_start": "2026-07-15",
            "spend": "250.00",
            "impressions": "1000",
            "reach": "800",
            "clicks": "50",
            "ctr": "5",
            "cpc": "5",
            "cpm": "250",
            "frequency": "1.25",
            "actions": [{"action_type": "purchase", "value": "2"}],
            "action_values": [{"action_type": "purchase", "value": "1000"}],
        }
    )
    assert insight.purchases == 2
    assert insight.cpa == Decimal("125.00")
    assert insight.roas == Decimal("4")
