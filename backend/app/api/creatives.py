"""Searchable and filterable creative performance routes."""

from uuid import UUID

from fastapi import APIRouter, Query

from app.api.dependencies import CurrentUser, SessionDep
from app.models import CreativeStatus
from app.schemas.api import CreativeListResponse
from app.services.queries import creative_rows

router = APIRouter(prefix="/creatives", tags=["Creatives"])


@router.get("", response_model=CreativeListResponse)
async def list_creatives(
    user: CurrentUser,
    session: SessionDep,
    search: str | None = None,
    product_id: UUID | None = None,
    recommendation: CreativeStatus | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
) -> CreativeListResponse:
    items, total = await creative_rows(
        session,
        user.id,
        search=search,
        product_id=product_id,
        status=recommendation,
        page=page,
        page_size=page_size,
    )
    return CreativeListResponse(items=items, total=total, page=page, page_size=page_size)
