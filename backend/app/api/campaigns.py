"""Campaign listing and product assignment routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import or_, select

from app.api.dependencies import CurrentUser, SessionDep
from app.models import Campaign, MetaAccount, Product
from app.schemas.api import CampaignProductUpdate, CampaignResponse

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@router.get("", response_model=list[CampaignResponse])
async def list_campaigns(
    user: CurrentUser,
    session: SessionDep,
    search: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[CampaignResponse]:
    query = (
        select(Campaign, Product)
        .join(MetaAccount, MetaAccount.id == Campaign.meta_account_id)
        .outerjoin(Product, Product.id == Campaign.product_id)
        .where(MetaAccount.user_id == user.id)
        .order_by(Campaign.name)
        .limit(limit)
    )
    if search:
        query = query.where(
            or_(Campaign.name.ilike(f"%{search}%"), Product.name.ilike(f"%{search}%"))
        )
    rows = (await session.execute(query)).all()
    return [
        CampaignResponse(
            id=campaign.id,
            name=campaign.name,
            external_id=campaign.external_id,
            status=campaign.status,
            product_id=campaign.product_id,
            product_name=product.name if product else None,
        )
        for campaign, product in rows
    ]


@router.put("/{campaign_id}/product", response_model=CampaignResponse)
async def assign_product(
    campaign_id: UUID,
    payload: CampaignProductUpdate,
    user: CurrentUser,
    session: SessionDep,
) -> CampaignResponse:
    campaign = await session.scalar(
        select(Campaign)
        .join(MetaAccount, MetaAccount.id == Campaign.meta_account_id)
        .where(Campaign.id == campaign_id, MetaAccount.user_id == user.id)
    )
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    product = None
    if payload.product_id:
        product = await session.scalar(
            select(Product).where(Product.id == payload.product_id, Product.user_id == user.id)
        )
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
    campaign.product_id = product.id if product else None
    await session.commit()
    return CampaignResponse(
        id=campaign.id,
        name=campaign.name,
        external_id=campaign.external_id,
        status=campaign.status,
        product_id=campaign.product_id,
        product_name=product.name if product else None,
    )
