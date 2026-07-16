"""Slack incoming-webhook delivery adapter."""

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


class SlackDeliveryError(RuntimeError):
    """Raised after Slack rejects or repeatedly fails a webhook delivery."""


class SlackWebhookClient:
    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def send(self, webhook_url: str, text: str) -> int:
        """Deliver one Slack notification and return the HTTP status."""

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, json={"text": text})
        if response.status_code >= 400:
            raise SlackDeliveryError(f"Slack webhook rejected delivery ({response.status_code})")
        return response.status_code
