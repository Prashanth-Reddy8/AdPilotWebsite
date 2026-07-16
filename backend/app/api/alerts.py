"""Paginated recommendation transition history."""

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.api.dependencies import CurrentUser, SessionDep
from app.models import Alert, Creative
from app.schemas.api import AlertListResponse, AlertResponse

router = APIRouter(prefix="/alerts", tags=["Alerts"])


async def alert_rows(
    session: SessionDep, user_id: object, page: int, page_size: int
) -> tuple[list[AlertResponse], int]:
    total = int(
        await session.scalar(select(func.count(Alert.id)).where(Alert.user_id == user_id)) or 0
    )
    rows = (
        await session.execute(
            select(Alert, Creative)
            .join(Creative, Creative.id == Alert.creative_id)
            .where(Alert.user_id == user_id)
            .order_by(Alert.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return (
        [
            AlertResponse(
                id=alert.id,
                creative_id=alert.creative_id,
                creative_name=creative.name,
                previous_status=alert.previous_status,
                new_status=alert.new_status,
                reasons=alert.reasons,
                metric_snapshot=alert.metric_snapshot,
                created_at=alert.created_at,
            )
            for alert, creative in rows
        ],
        total,
    )


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    user: CurrentUser,
    session: SessionDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
) -> AlertListResponse:
    items, total = await alert_rows(session, user.id, page, page_size)
    return AlertListResponse(items=items, total=total, page=page, page_size=page_size)
