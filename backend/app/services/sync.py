"""Meta structure/insight import orchestration and idempotent persistence."""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TokenCipher
from app.integrations.meta import MetaClient
from app.models import (
    Ad,
    AdSet,
    Campaign,
    Creative,
    DailyMetric,
    MetaAccount,
    SyncRun,
    SyncStatus,
)
from app.services.evaluation import evaluate_account


@dataclass(frozen=True, slots=True)
class SyncResult:
    sync_run_id: UUID
    rows_imported: int
    creatives_evaluated: int
    alerts_created: int


class SyncService:
    """Application service shared by manual and scheduled synchronization."""

    def __init__(self, meta: MetaClient, cipher: TokenCipher) -> None:
        self.meta = meta
        self.cipher = cipher

    async def run(self, session: AsyncSession, account: MetaAccount, trigger: str) -> SyncResult:
        run = SyncRun(
            meta_account_id=account.id,
            trigger=trigger,
            status=SyncStatus.RUNNING,
            started_at=datetime.now(UTC),
        )
        session.add(run)
        await session.commit()
        try:
            token = self.cipher.decrypt(account.access_token_ciphertext)
            remote_ads = await self.meta.fetch_ads(account.external_account_id, token)
            insights = await self.meta.fetch_daily_insights(account.external_account_id, token)

            campaigns = {
                row.external_id: row
                for row in (
                    await session.scalars(
                        select(Campaign).where(Campaign.meta_account_id == account.id)
                    )
                ).all()
            }
            ad_sets = {
                row.external_id: row
                for row in (
                    await session.scalars(select(AdSet).where(AdSet.meta_account_id == account.id))
                ).all()
            }
            creatives = {
                row.external_id: row
                for row in (
                    await session.scalars(
                        select(Creative).where(Creative.meta_account_id == account.id)
                    )
                ).all()
            }
            ads = {
                row.external_id: row
                for row in (
                    await session.scalars(select(Ad).where(Ad.meta_account_id == account.id))
                ).all()
            }
            for remote in remote_ads:
                campaign = campaigns.get(remote.campaign_id)
                if campaign is None:
                    campaign = Campaign(
                        meta_account_id=account.id,
                        external_id=remote.campaign_id,
                        name=remote.campaign_name,
                    )
                    session.add(campaign)
                    campaigns[remote.campaign_id] = campaign
                else:
                    campaign.name = remote.campaign_name
                await session.flush()

                ad_set = ad_sets.get(remote.ad_set_id)
                if ad_set is None:
                    ad_set = AdSet(
                        meta_account_id=account.id,
                        campaign_id=campaign.id,
                        external_id=remote.ad_set_id,
                        name=remote.ad_set_name,
                    )
                    session.add(ad_set)
                    ad_sets[remote.ad_set_id] = ad_set
                else:
                    ad_set.name = remote.ad_set_name
                    ad_set.campaign_id = campaign.id

                creative = creatives.get(remote.creative_id)
                if creative is None:
                    creative = Creative(
                        meta_account_id=account.id,
                        external_id=remote.creative_id,
                        name=remote.creative_name,
                    )
                    session.add(creative)
                    creatives[remote.creative_id] = creative
                else:
                    creative.name = remote.creative_name
                await session.flush()

                ad = ads.get(remote.external_id)
                if ad is None:
                    ad = Ad(
                        meta_account_id=account.id,
                        campaign_id=campaign.id,
                        ad_set_id=ad_set.id,
                        creative_id=creative.id,
                        external_id=remote.external_id,
                        name=remote.name,
                        status=remote.status,
                    )
                    session.add(ad)
                    ads[remote.external_id] = ad
                else:
                    ad.name = remote.name
                    ad.status = remote.status
                    ad.campaign_id = campaign.id
                    ad.ad_set_id = ad_set.id
                    ad.creative_id = creative.id
            await session.flush()

            existing_metrics = {
                (row.ad_id, row.metric_date): row
                for row in (
                    await session.scalars(
                        select(DailyMetric).where(DailyMetric.meta_account_id == account.id)
                    )
                ).all()
            }
            imported = 0
            for insight in insights:
                ad = ads.get(insight.ad_external_id)
                if ad is None:
                    continue
                metric = existing_metrics.get((ad.id, insight.metric_date))
                if metric is None:
                    metric = DailyMetric(
                        meta_account_id=account.id,
                        ad_id=ad.id,
                        creative_id=ad.creative_id,
                        metric_date=insight.metric_date,
                    )
                    session.add(metric)
                metric.spend = insight.spend
                metric.revenue = insight.revenue
                metric.impressions = insight.impressions
                metric.reach = insight.reach
                metric.clicks = insight.clicks
                metric.purchases = insight.purchases
                metric.ctr = insight.ctr
                metric.cpc = insight.cpc
                metric.cpm = insight.cpm
                metric.cpa = insight.cpa
                metric.frequency = insight.frequency
                metric.roas = insight.roas
                imported += 1
            evaluated, alerts = await evaluate_account(session, account)
            account.last_sync_at = datetime.now(UTC)
            run.status = SyncStatus.SUCCEEDED
            run.completed_at = datetime.now(UTC)
            run.rows_imported = imported
            await session.commit()
            return SyncResult(run.id, imported, evaluated, len(alerts))
        except Exception as exc:
            await session.rollback()
            persisted_run = await session.get(SyncRun, run.id)
            if persisted_run:
                persisted_run.status = SyncStatus.FAILED
                persisted_run.completed_at = datetime.now(UTC)
                persisted_run.error_message = str(exc)[:2000]
                await session.commit()
            raise
