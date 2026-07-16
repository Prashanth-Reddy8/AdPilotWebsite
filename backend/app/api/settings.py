"""Analyzer and notification settings routes."""

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.dependencies import ConfigDep, CurrentUser, SessionDep
from app.core.security import TokenCipher
from app.models import Settings
from app.schemas.api import SettingsResponse, SettingsUpdate

router = APIRouter(prefix="/settings", tags=["Settings"])


async def _get_or_create(session: SessionDep, user_id: object) -> Settings:
    row = await session.scalar(select(Settings).where(Settings.user_id == user_id))
    if row is None:
        row = Settings(user_id=user_id)
        session.add(row)
        await session.flush()
    return row


def _response(row: Settings) -> SettingsResponse:
    return SettingsResponse(
        ctr_drop_threshold_pct=row.ctr_drop_threshold_pct,
        cpa_increase_threshold_pct=row.cpa_increase_threshold_pct,
        minimum_roas=row.minimum_roas,
        maximum_frequency=row.maximum_frequency,
        spend_threshold=row.spend_threshold,
        slack_enabled=row.slack_enabled,
        slack_configured=row.slack_webhook_url_ciphertext is not None,
        email_enabled=row.email_enabled,
    )


@router.get("", response_model=SettingsResponse)
async def get_user_settings(user: CurrentUser, session: SessionDep) -> SettingsResponse:
    row = await _get_or_create(session, user.id)
    await session.commit()
    return _response(row)


@router.put("", response_model=SettingsResponse)
async def update_user_settings(
    payload: SettingsUpdate,
    user: CurrentUser,
    session: SessionDep,
    config: ConfigDep,
) -> SettingsResponse:
    row = await _get_or_create(session, user.id)
    row.ctr_drop_threshold_pct = payload.ctr_drop_threshold_pct
    row.cpa_increase_threshold_pct = payload.cpa_increase_threshold_pct
    row.minimum_roas = payload.minimum_roas
    row.maximum_frequency = payload.maximum_frequency
    row.spend_threshold = payload.spend_threshold
    row.slack_enabled = payload.slack_enabled
    row.email_enabled = payload.email_enabled
    if payload.slack_webhook_url is not None:
        row.slack_webhook_url_ciphertext = TokenCipher(config.token_encryption_key).encrypt(
            str(payload.slack_webhook_url)
        )
    if row.slack_enabled and row.slack_webhook_url_ciphertext is None:
        raise HTTPException(
            status_code=422,
            detail="A Slack webhook URL is required before Slack notifications can be enabled",
        )
    await session.commit()
    return _response(row)
