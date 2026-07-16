"""Single-process hourly scheduler for Meta synchronization and notifications."""

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore[import-untyped]
from sqlalchemy import select

from app.core.config import Settings
from app.core.security import TokenCipher
from app.db.session import SessionFactory
from app.integrations.meta import MetaClient
from app.integrations.slack import SlackWebhookClient
from app.models import MetaAccount
from app.services.notifications import dispatch_pending_slack
from app.services.sync import SyncService

logger = structlog.get_logger(__name__)


async def scheduled_sync(config: Settings) -> None:
    """Synchronize active accounts independently so one failure cannot stop the batch."""

    meta = MetaClient(config.meta_app_id, config.meta_app_secret, config.meta_api_version)
    cipher = TokenCipher(config.token_encryption_key)
    service = SyncService(meta, cipher)
    async with SessionFactory() as session:
        account_ids = list(
            (
                await session.scalars(select(MetaAccount.id).where(MetaAccount.is_active.is_(True)))
            ).all()
        )
    for account_id in account_ids:
        async with SessionFactory() as session:
            account = await session.get(MetaAccount, account_id)
            if account is None:
                continue
            try:
                await service.run(session, account, "scheduled")
            except Exception:
                logger.exception("scheduled_sync_failed", meta_account_id=str(account_id))
    async with SessionFactory() as session:
        await dispatch_pending_slack(session, cipher, SlackWebhookClient())


def build_scheduler(config: Settings) -> AsyncIOScheduler:
    """Create but do not start the process-local scheduler."""

    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        scheduled_sync,
        "interval",
        minutes=config.sync_interval_minutes,
        kwargs={"config": config},
        id="meta-hourly-sync",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )
    return scheduler
