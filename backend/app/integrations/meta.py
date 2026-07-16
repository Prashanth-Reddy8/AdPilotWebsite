"""Resilient, read-only adapter for the Meta Marketing API."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter


class MetaAPIError(RuntimeError):
    """A sanitized Meta API failure safe to record in operational logs."""


@dataclass(frozen=True, slots=True)
class MetaAd:
    external_id: str
    name: str
    status: str | None
    campaign_id: str
    campaign_name: str
    ad_set_id: str
    ad_set_name: str
    creative_id: str
    creative_name: str


@dataclass(frozen=True, slots=True)
class MetaInsight:
    ad_external_id: str
    metric_date: date
    spend: Decimal
    revenue: Decimal
    impressions: int
    reach: int
    clicks: int
    purchases: int
    ctr: Decimal
    cpc: Decimal
    cpm: Decimal
    cpa: Decimal | None
    frequency: Decimal
    roas: Decimal


class MetaClient:
    """Minimal Marketing API client limited to identity and reporting reads."""

    def __init__(self, app_id: str, app_secret: str, api_version: str) -> None:
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = f"https://graph.facebook.com/{api_version}"

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        wait=wait_exponential_jitter(initial=1, max=20),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
            response = await client.get(f"{self.base_url}/{path.lstrip('/')}", params=params)
        if response.status_code >= 400:
            request_id = response.headers.get("x-fb-trace-id", "unknown")
            raise MetaAPIError(
                f"Meta API request failed ({response.status_code}, trace {request_id})"
            )
        payload: object = response.json()
        if not isinstance(payload, dict):
            raise MetaAPIError("Meta API returned an unexpected response shape")
        return {str(key): value for key, value in payload.items()}

    async def exchange_code(self, code: str, redirect_uri: str) -> str:
        """Exchange OAuth code for a long-lived user token."""

        short = await self._get(
            "oauth/access_token",
            {
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "redirect_uri": redirect_uri,
                "code": code,
            },
        )
        long_lived = await self._get(
            "oauth/access_token",
            {
                "grant_type": "fb_exchange_token",
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "fb_exchange_token": short["access_token"],
            },
        )
        return str(long_lived["access_token"])

    async def get_ad_accounts(self, token: str) -> list[dict[str, Any]]:
        payload = await self._get(
            "me/adaccounts",
            {
                "access_token": token,
                "fields": "id,name,currency,timezone_name,account_status",
                "limit": 100,
            },
        )
        return list(payload.get("data", []))

    async def _get_all(self, path: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        payload = await self._get(path, params)
        while True:
            rows.extend(payload.get("data", []))
            next_url = payload.get("paging", {}).get("next")
            if not next_url:
                return rows
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(next_url)
            if response.status_code >= 400:
                raise MetaAPIError(f"Meta pagination failed ({response.status_code})")
            payload = response.json()

    async def fetch_ads(self, account_id: str, token: str) -> list[MetaAd]:
        """Fetch active and inactive ad structure; no mutation fields are requested."""

        rows = await self._get_all(
            f"{account_id}/ads",
            {
                "access_token": token,
                "fields": (
                    "id,name,effective_status,campaign{id,name},adset{id,name},creative{id,name}"
                ),
                "limit": 500,
            },
        )
        result: list[MetaAd] = []
        for row in rows:
            campaign = row.get("campaign") or {}
            ad_set = row.get("adset") or {}
            creative = row.get("creative") or {}
            if not all((campaign.get("id"), ad_set.get("id"), creative.get("id"))):
                continue
            result.append(
                MetaAd(
                    external_id=str(row["id"]),
                    name=str(row.get("name") or row["id"]),
                    status=row.get("effective_status"),
                    campaign_id=str(campaign["id"]),
                    campaign_name=str(campaign.get("name") or campaign["id"]),
                    ad_set_id=str(ad_set["id"]),
                    ad_set_name=str(ad_set.get("name") or ad_set["id"]),
                    creative_id=str(creative["id"]),
                    creative_name=str(creative.get("name") or row.get("name") or creative["id"]),
                )
            )
        return result

    async def fetch_daily_insights(self, account_id: str, token: str) -> list[MetaInsight]:
        """Fetch the rolling eight-day ad-level fact window."""

        fields = ",".join(
            [
                "ad_id",
                "spend",
                "impressions",
                "reach",
                "clicks",
                "ctr",
                "cpc",
                "cpm",
                "frequency",
                "actions",
                "action_values",
            ]
        )
        rows = await self._get_all(
            f"{account_id}/insights",
            {
                "access_token": token,
                "fields": fields,
                "level": "ad",
                "date_preset": "last_8d",
                "time_increment": 1,
                "limit": 500,
            },
        )
        return [self._parse_insight(row) for row in rows]

    @staticmethod
    def _action_total(rows: list[dict[str, Any]] | None, names: set[str]) -> Decimal:
        return sum(
            (
                Decimal(str(item.get("value", 0)))
                for item in rows or []
                if item.get("action_type") in names
            ),
            start=Decimal(0),
        )

    @classmethod
    def _parse_insight(cls, row: dict[str, Any]) -> MetaInsight:
        purchase_names = {"purchase", "omni_purchase"}
        spend = Decimal(str(row.get("spend", 0)))
        purchases_decimal = cls._action_total(row.get("actions"), purchase_names)
        revenue = cls._action_total(row.get("action_values"), purchase_names)
        purchases = int(purchases_decimal)
        return MetaInsight(
            ad_external_id=str(row["ad_id"]),
            metric_date=date.fromisoformat(row["date_start"]),
            spend=spend,
            revenue=revenue,
            impressions=int(row.get("impressions", 0)),
            reach=int(row.get("reach", 0)),
            clicks=int(row.get("clicks", 0)),
            purchases=purchases,
            ctr=Decimal(str(row.get("ctr", 0))),
            cpc=Decimal(str(row.get("cpc", 0))),
            cpm=Decimal(str(row.get("cpm", 0))),
            cpa=spend / purchases if purchases else None,
            frequency=Decimal(str(row.get("frequency", 0))),
            roas=revenue / spend if spend else Decimal(0),
        )
