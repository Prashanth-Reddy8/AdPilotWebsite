"""Dashboard aggregate and table route."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.api.alerts import alert_rows
from app.api.dependencies import CurrentUser, SessionDep
from app.models import Creative, CreativeStatus, DailyMetric, MetaAccount
from app.schemas.api import DashboardResponse, DashboardSummary
from app.services.queries import creative_rows

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardResponse)
async def dashboard(
    user: CurrentUser,
    session: SessionDep,
    search: str | None = None,
    product_id: UUID | None = None,
    recommendation: CreativeStatus | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
) -> DashboardResponse:
    account_ids = select(MetaAccount.id).where(MetaAccount.user_id == user.id)
    spend, revenue = (
        await session.execute(
            select(
                func.coalesce(func.sum(DailyMetric.spend), 0),
                func.coalesce(func.sum(DailyMetric.revenue), 0),
            ).where(
                DailyMetric.meta_account_id.in_(account_ids),
                DailyMetric.metric_date == date.today(),
            )
        )
    ).one()
    count_rows = (
        await session.execute(
            select(Creative.recommendation_status, func.count(Creative.id))
            .where(Creative.meta_account_id.in_(account_ids))
            .group_by(Creative.recommendation_status)
        )
    ).all()
    counts: dict[CreativeStatus, int] = {
        recommendation_status: int(count) for recommendation_status, count in count_rows
    }
    creatives, total = await creative_rows(
        session,
        user.id,
        search=search,
        product_id=product_id,
        status=recommendation,
        page=page,
        page_size=page_size,
    )
    alerts, _ = await alert_rows(session, user.id, 1, 10)
    spend_decimal = Decimal(spend)
    revenue_decimal = Decimal(revenue)
    return DashboardResponse(
        summary=DashboardSummary(
            today_spend=spend_decimal,
            today_revenue=revenue_decimal,
            roas=revenue_decimal / spend_decimal if spend_decimal else Decimal(0),
            healthy_creatives=counts.get(CreativeStatus.HEALTHY, 0),
            watch_creatives=counts.get(CreativeStatus.WATCH, 0),
            turn_off_recommendations=counts.get(CreativeStatus.TURN_OFF_RECOMMENDATION, 0),
        ),
        recent_alerts=alerts,
        creatives=creatives,
        total_creatives=total,
        page=page,
        page_size=page_size,
    )
