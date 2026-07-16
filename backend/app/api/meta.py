"""Meta OAuth connection and explicit synchronization routes."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.dependencies import ConfigDep, CurrentUser, SessionDep
from app.core.security import TokenCipher
from app.integrations.meta import MetaClient
from app.models import MetaAccount, MetaConnectionSession
from app.schemas.api import (
    MetaAccountOption,
    MetaAccountResponse,
    MetaConnectCompleteRequest,
    MetaConnectOptionsRequest,
    MetaConnectOptionsResponse,
    MetaConnectRequest,
    SyncRequest,
    SyncResponse,
)
from app.services.sync import SyncService

router = APIRouter(tags=["Meta"])


def _client(config: ConfigDep) -> MetaClient:
    if not config.meta_app_id or not config.meta_app_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Meta integration is not configured",
        )
    return MetaClient(config.meta_app_id, config.meta_app_secret, config.meta_api_version)


async def _persist_account(
    session: SessionDep,
    *,
    user_id: object,
    selected: dict[str, object],
    token: str,
    cipher: TokenCipher,
) -> MetaAccount:
    account_id = str(selected["id"])
    row = await session.scalar(
        select(MetaAccount).where(
            MetaAccount.user_id == user_id,
            MetaAccount.external_account_id == account_id,
        )
    )
    ciphertext = cipher.encrypt(token)
    if row is None:
        row = MetaAccount(
            user_id=user_id,
            external_account_id=account_id,
            name=str(selected.get("name") or account_id),
            currency=str(selected.get("currency") or "INR"),
            timezone_name=str(selected.get("timezone_name") or "UTC"),
            access_token_ciphertext=ciphertext,
        )
        session.add(row)
    else:
        row.name = str(selected.get("name") or account_id)
        row.currency = str(selected.get("currency") or row.currency)
        row.timezone_name = str(selected.get("timezone_name") or row.timezone_name)
        row.access_token_ciphertext = ciphertext
        row.is_active = True
    return row


@router.get("/meta/accounts", response_model=list[MetaAccountResponse])
async def list_meta_accounts(user: CurrentUser, session: SessionDep) -> list[MetaAccount]:
    return list(
        (
            await session.scalars(
                select(MetaAccount)
                .where(MetaAccount.user_id == user.id, MetaAccount.is_active.is_(True))
                .order_by(MetaAccount.name)
            )
        ).all()
    )


@router.post("/meta/connect/options", response_model=MetaConnectOptionsResponse)
async def meta_connect_options(
    payload: MetaConnectOptionsRequest,
    user: CurrentUser,
    session: SessionDep,
    config: ConfigDep,
) -> MetaConnectOptionsResponse:
    """Exchange an OAuth code and return selectable accounts without exposing the token."""

    token = await _client(config).exchange_code(
        payload.authorization_code, str(payload.redirect_uri)
    )
    accounts = await _client(config).get_ad_accounts(token)
    if not accounts:
        raise HTTPException(status_code=403, detail="No accessible Meta ad accounts found")
    expires_at = datetime.now(UTC) + timedelta(minutes=15)
    connection = MetaConnectionSession(
        user_id=user.id,
        access_token_ciphertext=TokenCipher(config.token_encryption_key).encrypt(token),
        accounts=accounts,
        expires_at=expires_at,
    )
    session.add(connection)
    await session.commit()
    return MetaConnectOptionsResponse(
        connection_session_id=connection.id,
        expires_at=expires_at,
        accounts=[
            MetaAccountOption(
                id=str(account["id"]),
                name=str(account.get("name") or account["id"]),
                currency=str(account.get("currency") or "INR"),
                timezone_name=str(account.get("timezone_name") or "UTC"),
            )
            for account in accounts
        ],
    )


@router.post("/meta/connect/complete", response_model=MetaAccountResponse)
async def complete_meta_connection(
    payload: MetaConnectCompleteRequest,
    user: CurrentUser,
    session: SessionDep,
    config: ConfigDep,
) -> MetaAccount:
    connection = await session.scalar(
        select(MetaConnectionSession).where(
            MetaConnectionSession.id == payload.connection_session_id,
            MetaConnectionSession.user_id == user.id,
            MetaConnectionSession.consumed_at.is_(None),
            MetaConnectionSession.expires_at > datetime.now(UTC),
        )
    )
    if connection is None:
        raise HTTPException(status_code=404, detail="Connection session expired or not found")
    selected = next(
        (account for account in connection.accounts if account.get("id") == payload.account_id),
        None,
    )
    if selected is None:
        raise HTTPException(status_code=403, detail="Selected Meta account is not accessible")
    cipher = TokenCipher(config.token_encryption_key)
    row = await _persist_account(
        session,
        user_id=user.id,
        selected=selected,
        token=cipher.decrypt(connection.access_token_ciphertext),
        cipher=cipher,
    )
    connection.consumed_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(row)
    return row


@router.post("/meta/connect", response_model=MetaAccountResponse)
async def connect_meta(
    payload: MetaConnectRequest,
    user: CurrentUser,
    session: SessionDep,
    config: ConfigDep,
) -> MetaAccount:
    client = _client(config)
    token = await client.exchange_code(payload.authorization_code, str(payload.redirect_uri))
    accounts = await client.get_ad_accounts(token)
    selected = next((item for item in accounts if item.get("id") == payload.account_id), None)
    if selected is None:
        raise HTTPException(status_code=403, detail="Selected Meta account is not accessible")
    row = await _persist_account(
        session,
        user_id=user.id,
        selected=selected,
        token=token,
        cipher=TokenCipher(config.token_encryption_key),
    )
    await session.commit()
    await session.refresh(row)
    return row


@router.post("/sync", response_model=SyncResponse)
async def sync_meta(
    payload: SyncRequest,
    user: CurrentUser,
    session: SessionDep,
    config: ConfigDep,
) -> SyncResponse:
    account = await session.scalar(
        select(MetaAccount).where(
            MetaAccount.id == payload.meta_account_id,
            MetaAccount.user_id == user.id,
            MetaAccount.is_active.is_(True),
        )
    )
    if account is None:
        raise HTTPException(status_code=404, detail="Meta account not found")
    result = await SyncService(_client(config), TokenCipher(config.token_encryption_key)).run(
        session, account, "manual"
    )
    return SyncResponse(
        sync_run_id=result.sync_run_id,
        rows_imported=result.rows_imported,
        creatives_evaluated=result.creatives_evaluated,
        alerts_created=result.alerts_created,
    )
