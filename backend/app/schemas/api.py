"""Versioned request and response contracts for the v1 HTTP API."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl

from app.models import CreativeStatus


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class MetaConnectRequest(BaseModel):
    authorization_code: str = Field(min_length=5)
    redirect_uri: HttpUrl
    account_id: str = Field(pattern=r"^act_\d+$")


class MetaConnectOptionsRequest(BaseModel):
    authorization_code: str = Field(min_length=5)
    redirect_uri: HttpUrl


class MetaAccountOption(BaseModel):
    id: str
    name: str
    currency: str
    timezone_name: str


class MetaConnectOptionsResponse(BaseModel):
    connection_session_id: UUID
    expires_at: datetime
    accounts: list[MetaAccountOption]


class MetaConnectCompleteRequest(BaseModel):
    connection_session_id: UUID
    account_id: str = Field(pattern=r"^act_\d+$")


class MetaAccountResponse(ORMModel):
    id: UUID
    external_account_id: str
    name: str
    currency: str
    timezone_name: str
    last_sync_at: datetime | None


class SyncRequest(BaseModel):
    meta_account_id: UUID


class SyncResponse(BaseModel):
    sync_run_id: UUID
    rows_imported: int
    creatives_evaluated: int
    alerts_created: int


class SettingsResponse(BaseModel):
    ctr_drop_threshold_pct: Decimal
    cpa_increase_threshold_pct: Decimal
    minimum_roas: Decimal
    maximum_frequency: Decimal
    spend_threshold: Decimal
    slack_enabled: bool
    slack_configured: bool
    email_enabled: bool


class SettingsUpdate(BaseModel):
    ctr_drop_threshold_pct: Decimal = Field(ge=0, le=100)
    cpa_increase_threshold_pct: Decimal = Field(ge=0, le=1000)
    minimum_roas: Decimal = Field(ge=0, le=100)
    maximum_frequency: Decimal = Field(gt=0, le=100)
    spend_threshold: Decimal = Field(ge=0)
    slack_enabled: bool = False
    slack_webhook_url: HttpUrl | None = None
    email_enabled: bool = False


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)


class ProductResponse(ORMModel):
    id: UUID
    name: str
    is_active: bool


class CampaignResponse(BaseModel):
    id: UUID
    name: str
    external_id: str
    status: str | None
    product_id: UUID | None
    product_name: str | None


class CampaignProductUpdate(BaseModel):
    product_id: UUID | None


class CreativeRow(BaseModel):
    id: UUID
    name: str
    campaign: str
    product: str | None
    ctr: Decimal
    cpa: Decimal | None
    frequency: Decimal
    roas: Decimal
    spend: Decimal
    revenue: Decimal
    recommendation: CreativeStatus
    reasons: list[str]
    updated_at: datetime | None


class AlertResponse(BaseModel):
    id: UUID
    creative_id: UUID
    creative_name: str
    previous_status: CreativeStatus
    new_status: CreativeStatus
    reasons: list[str]
    metric_snapshot: dict[str, object]
    created_at: datetime


class DashboardSummary(BaseModel):
    today_spend: Decimal
    today_revenue: Decimal
    roas: Decimal
    healthy_creatives: int
    watch_creatives: int
    turn_off_recommendations: int


class DashboardResponse(BaseModel):
    summary: DashboardSummary
    recent_alerts: list[AlertResponse]
    creatives: list[CreativeRow]
    total_creatives: int
    page: int
    page_size: int


class Page(BaseModel):
    items: list[object]
    total: int
    page: int
    page_size: int


class CreativeListResponse(BaseModel):
    items: list[CreativeRow]
    total: int
    page: int
    page_size: int


class AlertListResponse(BaseModel):
    items: list[AlertResponse]
    total: int
    page: int
    page_size: int
