"""Composition root for version 1 API routes."""

from fastapi import APIRouter

from app.api import alerts, auth, campaigns, creatives, dashboard, meta, products, settings

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(meta.router)
api_router.include_router(dashboard.router)
api_router.include_router(campaigns.router)
api_router.include_router(creatives.router)
api_router.include_router(alerts.router)
api_router.include_router(settings.router)
api_router.include_router(products.router)
