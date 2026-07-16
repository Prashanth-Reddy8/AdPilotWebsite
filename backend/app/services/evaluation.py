"""Batch evaluation, state transition, and notification outbox creation."""

from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Alert,
    Creative,
    DailyMetric,
    MetaAccount,
    NotificationLog,
    Settings,
)
from app.services.analyzer import AnalyzerThresholds, Performance, analyze


def _performance(rows: list[DailyMetric]) -> Performance:
    return Performance(
        spend=sum((row.spend for row in rows), start=Decimal(0)),
        revenue=sum((row.revenue for row in rows), start=Decimal(0)),
        impressions=sum(row.impressions for row in rows),
        clicks=sum(row.clicks for row in rows),
        purchases=sum(row.purchases for row in rows),
        reach=sum(row.reach for row in rows),
    )


async def evaluate_account(session: AsyncSession, account: MetaAccount) -> tuple[int, list[Alert]]:
    """Evaluate every creative in one account in a bounded set of database reads."""

    user_settings = await session.scalar(
        select(Settings).where(Settings.user_id == account.user_id)
    )
    if user_settings is None:
        user_settings = Settings(user_id=account.user_id)
        session.add(user_settings)
        await session.flush()
    thresholds = AnalyzerThresholds(
        ctr_drop_pct=user_settings.ctr_drop_threshold_pct,
        cpa_increase_pct=user_settings.cpa_increase_threshold_pct,
        minimum_roas=user_settings.minimum_roas,
        maximum_frequency=user_settings.maximum_frequency,
        spend_threshold=user_settings.spend_threshold,
    )
    creatives = list(
        (
            await session.scalars(select(Creative).where(Creative.meta_account_id == account.id))
        ).all()
    )
    if not creatives:
        return 0, []
    metrics = list(
        (
            await session.scalars(
                select(DailyMetric)
                .where(DailyMetric.meta_account_id == account.id)
                .order_by(DailyMetric.metric_date.desc())
            )
        ).all()
    )
    by_creative: dict[UUID, list[DailyMetric]] = defaultdict(list)
    for metric in metrics:
        by_creative[metric.creative_id].append(metric)

    now = datetime.now(UTC)
    alerts: list[Alert] = []
    for creative in creatives:
        rows = by_creative.get(creative.id, [])
        if not rows:
            continue
        current_date = max(row.metric_date for row in rows)
        current_rows = [row for row in rows if row.metric_date == current_date]
        prior_dates = sorted(
            {row.metric_date for row in rows if row.metric_date < current_date}, reverse=True
        )[:7]
        baseline_rows = [row for row in rows if row.metric_date in prior_dates]
        result = analyze(
            _performance(current_rows),
            _performance(baseline_rows) if baseline_rows else None,
            thresholds,
        )
        previous = creative.recommendation_status
        creative.recommendation_status = result.status
        creative.recommendation_reasons = list(result.reasons)
        creative.evaluated_at = now
        severity = {
            "healthy": 0,
            "watch": 1,
            "turn_off_recommendation": 2,
        }
        if severity[result.status.value] <= severity[previous.value]:
            continue
        current = _performance(current_rows)
        alert = Alert(
            user_id=account.user_id,
            meta_account_id=account.id,
            creative_id=creative.id,
            previous_status=previous,
            new_status=result.status,
            reasons=list(result.reasons),
            metric_snapshot={
                "date": current_date.isoformat(),
                "spend": str(current.spend),
                "revenue": str(current.revenue),
                "ctr": str(current.ctr),
                "cpa": str(current.cpa) if current.cpa is not None else None,
                "frequency": str(current.frequency),
                "roas": str(current.roas),
                "purchases": current.purchases,
            },
        )
        session.add(alert)
        await session.flush()
        if user_settings.slack_enabled and user_settings.slack_webhook_url_ciphertext:
            session.add(NotificationLog(alert_id=alert.id, channel="slack"))
        alerts.append(alert)
    return len(creatives), alerts
