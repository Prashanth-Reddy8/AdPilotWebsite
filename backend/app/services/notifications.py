"""Transactional-outbox dispatcher for alert notifications."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import TokenCipher
from app.integrations.slack import SlackWebhookClient
from app.models import Alert, NotificationLog, NotificationStatus, Settings


def _slack_message(alert: Alert) -> str:
    snapshot = alert.metric_snapshot
    reasons = "\n".join(f"• {reason}" for reason in alert.reasons)
    return (
        "🚨 *Creative Alert*\n"
        f"*Creative:* {alert.creative.name}\n"
        f"*CTR:* {snapshot.get('ctr', 'n/a')}%\n"
        f"*CPA:* {snapshot.get('cpa', 'n/a')}\n"
        f"*ROAS:* {snapshot.get('roas', 'n/a')}\n"
        f"*Recommendation:* {alert.new_status.value.replace('_', ' ').title()}\n"
        f"{reasons}"
    )


async def dispatch_pending_slack(
    session: AsyncSession, cipher: TokenCipher, client: SlackWebhookClient
) -> int:
    """Deliver pending/failed Slack outbox rows with recorded outcomes."""

    logs = list(
        (
            await session.scalars(
                select(NotificationLog)
                .where(
                    NotificationLog.channel == "slack",
                    NotificationLog.status != NotificationStatus.SENT,
                    NotificationLog.attempt_count < 5,
                )
                .order_by(NotificationLog.created_at)
                .limit(100)
            )
        ).all()
    )
    sent = 0
    for log in logs:
        alert = await session.scalar(
            select(Alert).options(selectinload(Alert.creative)).where(Alert.id == log.alert_id)
        )
        if alert is None:
            continue
        settings = await session.scalar(select(Settings).where(Settings.user_id == alert.user_id))
        if settings is None or not settings.slack_webhook_url_ciphertext:
            continue
        log.attempt_count += 1
        try:
            code = await client.send(
                cipher.decrypt(settings.slack_webhook_url_ciphertext), _slack_message(alert)
            )
            log.status = NotificationStatus.SENT
            log.response_code = code
            log.sent_at = datetime.now(UTC)
            log.error_message = None
            sent += 1
        except Exception as exc:  # provider errors must persist for operations visibility
            log.status = NotificationStatus.FAILED
            log.error_message = str(exc)[:1000]
        await session.commit()
    return sent
