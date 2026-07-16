"""Read-model queries for creative tables and dashboard summaries."""

from collections import defaultdict
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Ad, Campaign, Creative, CreativeStatus, DailyMetric, MetaAccount, Product
from app.schemas.api import CreativeRow
from app.services.analyzer import Performance


async def creative_rows(
    session: AsyncSession,
    user_id: UUID,
    *,
    search: str | None = None,
    product_id: UUID | None = None,
    status: CreativeStatus | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[CreativeRow], int]:
    """Return a bounded page of current creative read models."""

    query = (
        select(Creative.id)
        .join(MetaAccount, MetaAccount.id == Creative.meta_account_id)
        .join(Ad, Ad.creative_id == Creative.id)
        .join(Campaign, Campaign.id == Ad.campaign_id)
        .outerjoin(Product, Product.id == Campaign.product_id)
        .where(MetaAccount.user_id == user_id)
        .distinct()
    )
    if search:
        term = f"%{search.strip()}%"
        query = query.where(or_(Creative.name.ilike(term), Campaign.name.ilike(term)))
    if product_id:
        query = query.where(Campaign.product_id == product_id)
    if status:
        query = query.where(Creative.recommendation_status == status)
    total = int(await session.scalar(select(func.count()).select_from(query.subquery())) or 0)
    ids = list(
        (
            await session.scalars(
                query.order_by(Creative.name).offset((page - 1) * page_size).limit(page_size)
            )
        ).all()
    )
    if not ids:
        return [], total

    entity_rows = (
        await session.execute(
            select(Creative, Campaign, Product)
            .join(Ad, Ad.creative_id == Creative.id)
            .join(Campaign, Campaign.id == Ad.campaign_id)
            .outerjoin(Product, Product.id == Campaign.product_id)
            .where(Creative.id.in_(ids))
            .order_by(Campaign.name)
        )
    ).all()
    display: dict[UUID, tuple[Creative, Campaign, Product | None]] = {}
    for creative, campaign, product in entity_rows:
        display.setdefault(creative.id, (creative, campaign, product))

    metrics = list(
        (
            await session.scalars(
                select(DailyMetric)
                .where(DailyMetric.creative_id.in_(ids))
                .order_by(DailyMetric.metric_date.desc())
            )
        ).all()
    )
    latest_dates: dict[UUID, date] = {}
    for metric in metrics:
        latest_dates.setdefault(metric.creative_id, metric.metric_date)
    grouped: dict[UUID, list[DailyMetric]] = defaultdict(list)
    for metric in metrics:
        if metric.metric_date == latest_dates[metric.creative_id]:
            grouped[metric.creative_id].append(metric)

    result: list[CreativeRow] = []
    for creative_id in ids:
        creative, campaign, product = display[creative_id]
        rows = grouped.get(creative_id, [])
        performance = Performance(
            spend=sum((row.spend for row in rows), start=Decimal(0)),
            revenue=sum((row.revenue for row in rows), start=Decimal(0)),
            impressions=sum(row.impressions for row in rows),
            clicks=sum(row.clicks for row in rows),
            purchases=sum(row.purchases for row in rows),
            reach=sum(row.reach for row in rows),
        )
        result.append(
            CreativeRow(
                id=creative.id,
                name=creative.name,
                campaign=campaign.name,
                product=product.name if product else None,
                ctr=performance.ctr,
                cpa=performance.cpa,
                frequency=performance.frequency,
                roas=performance.roas,
                spend=performance.spend,
                revenue=performance.revenue,
                recommendation=creative.recommendation_status,
                reasons=creative.recommendation_reasons,
                updated_at=creative.evaluated_at,
            )
        )
    return result, total
