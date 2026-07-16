"""Normalized persistence model for AdPilot's Meta-monitoring MVP."""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class CreativeStatus(StrEnum):
    HEALTHY = "healthy"
    WATCH = "watch"
    TURN_OFF_RECOMMENDATION = "turn_off_recommendation"


class NotificationStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class SyncStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    meta_accounts: Mapped[list["MetaAccount"]] = relationship(back_populates="user")
    settings: Mapped["Settings | None"] = relationship(back_populates="user", uselist=False)


class Product(TimestampMixin, Base):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_products_user_name"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class MetaAccount(TimestampMixin, Base):
    __tablename__ = "meta_accounts"
    __table_args__ = (
        UniqueConstraint("user_id", "external_account_id", name="uq_meta_accounts_user_external"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    external_account_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255))
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    timezone_name: Mapped[str] = mapped_column(String(100), default="UTC")
    access_token_ciphertext: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="meta_accounts")
    campaigns: Mapped[list["Campaign"]] = relationship(back_populates="meta_account")


class MetaConnectionSession(TimestampMixin, Base):
    """Short-lived encrypted OAuth result used while a user selects an ad account."""

    __tablename__ = "meta_connection_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    access_token_ciphertext: Mapped[str] = mapped_column(Text)
    accounts: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Campaign(TimestampMixin, Base):
    __tablename__ = "campaigns"
    __table_args__ = (
        UniqueConstraint("meta_account_id", "external_id", name="uq_campaigns_account_external"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    meta_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("meta_accounts.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"), index=True
    )
    external_id: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(255), index=True)
    status: Mapped[str | None] = mapped_column(String(50))

    meta_account: Mapped[MetaAccount] = relationship(back_populates="campaigns")
    product: Mapped[Product | None] = relationship()


class AdSet(TimestampMixin, Base):
    __tablename__ = "ad_sets"
    __table_args__ = (
        UniqueConstraint("meta_account_id", "external_id", name="uq_ad_sets_account_external"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    meta_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("meta_accounts.id", ondelete="CASCADE"), index=True
    )
    campaign_id: Mapped[UUID] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    external_id: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str | None] = mapped_column(String(50))


class Creative(TimestampMixin, Base):
    __tablename__ = "creatives"
    __table_args__ = (
        UniqueConstraint("meta_account_id", "external_id", name="uq_creatives_account_external"),
        Index("ix_creatives_account_status", "meta_account_id", "recommendation_status"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    meta_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("meta_accounts.id", ondelete="CASCADE"), index=True
    )
    external_id: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(255), index=True)
    recommendation_status: Mapped[CreativeStatus] = mapped_column(
        Enum(CreativeStatus, name="creative_status"), default=CreativeStatus.HEALTHY
    )
    recommendation_reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Ad(TimestampMixin, Base):
    __tablename__ = "ads"
    __table_args__ = (
        UniqueConstraint("meta_account_id", "external_id", name="uq_ads_account_external"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    meta_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("meta_accounts.id", ondelete="CASCADE"), index=True
    )
    campaign_id: Mapped[UUID] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    ad_set_id: Mapped[UUID] = mapped_column(
        ForeignKey("ad_sets.id", ondelete="CASCADE"), index=True
    )
    creative_id: Mapped[UUID] = mapped_column(
        ForeignKey("creatives.id", ondelete="CASCADE"), index=True
    )
    external_id: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str | None] = mapped_column(String(50))

    campaign: Mapped[Campaign] = relationship()
    ad_set: Mapped[AdSet] = relationship()
    creative: Mapped[Creative] = relationship()


class DailyMetric(TimestampMixin, Base):
    __tablename__ = "daily_metrics"
    __table_args__ = (
        UniqueConstraint("ad_id", "metric_date", name="uq_daily_metrics_ad_date"),
        Index("ix_daily_metrics_creative_date", "creative_id", "metric_date"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    meta_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("meta_accounts.id", ondelete="CASCADE"), index=True
    )
    ad_id: Mapped[UUID] = mapped_column(ForeignKey("ads.id", ondelete="CASCADE"), index=True)
    creative_id: Mapped[UUID] = mapped_column(
        ForeignKey("creatives.id", ondelete="CASCADE"), index=True
    )
    metric_date: Mapped[date] = mapped_column(Date, index=True)
    spend: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    revenue: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    reach: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    purchases: Mapped[int] = mapped_column(Integer, default=0)
    ctr: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=0)
    cpc: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=0)
    cpm: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=0)
    cpa: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    frequency: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=0)
    roas: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=0)


class Alert(TimestampMixin, Base):
    __tablename__ = "alerts"
    __table_args__ = (Index("ix_alerts_user_created", "user_id", "created_at"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    meta_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("meta_accounts.id", ondelete="CASCADE"), index=True
    )
    creative_id: Mapped[UUID] = mapped_column(
        ForeignKey("creatives.id", ondelete="CASCADE"), index=True
    )
    previous_status: Mapped[CreativeStatus] = mapped_column(
        Enum(CreativeStatus, name="alert_previous_creative_status")
    )
    new_status: Mapped[CreativeStatus] = mapped_column(
        Enum(CreativeStatus, name="alert_new_creative_status")
    )
    reasons: Mapped[list[str]] = mapped_column(JSON)
    metric_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)

    creative: Mapped[Creative] = relationship()


class Settings(TimestampMixin, Base):
    __tablename__ = "settings"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    ctr_drop_threshold_pct: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=20)
    cpa_increase_threshold_pct: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=30)
    minimum_roas: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=2)
    maximum_frequency: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=3.5)
    spend_threshold: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=2000)
    slack_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    slack_webhook_url_ciphertext: Mapped[str | None] = mapped_column(Text)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User] = relationship(back_populates="settings")


class NotificationLog(TimestampMixin, Base):
    __tablename__ = "notification_logs"
    __table_args__ = (
        UniqueConstraint("alert_id", "channel", name="uq_notification_logs_alert_channel"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    alert_id: Mapped[UUID] = mapped_column(ForeignKey("alerts.id", ondelete="CASCADE"), index=True)
    channel: Mapped[str] = mapped_column(String(30))
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus, name="notification_status"), default=NotificationStatus.PENDING
    )
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    response_code: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SyncRun(TimestampMixin, Base):
    __tablename__ = "sync_runs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    meta_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("meta_accounts.id", ondelete="CASCADE"), index=True
    )
    trigger: Mapped[str] = mapped_column(String(30))
    status: Mapped[SyncStatus] = mapped_column(
        Enum(SyncStatus, name="sync_status"), default=SyncStatus.RUNNING
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rows_imported: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
