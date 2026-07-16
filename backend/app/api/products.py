"""Product group management routes."""

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import CurrentUser, SessionDep
from app.models import Product
from app.schemas.api import ProductCreate, ProductResponse

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=list[ProductResponse])
async def list_products(user: CurrentUser, session: SessionDep) -> list[Product]:
    return list(
        (
            await session.scalars(
                select(Product)
                .where(Product.user_id == user.id, Product.is_active.is_(True))
                .order_by(Product.name)
            )
        ).all()
    )


@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(payload: ProductCreate, user: CurrentUser, session: SessionDep) -> Product:
    row = Product(user_id=user.id, name=payload.name.strip())
    session.add(row)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Product name already exists") from None
    await session.refresh(row)
    return row
