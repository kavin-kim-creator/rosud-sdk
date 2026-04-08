"""Webhook resource"""
from __future__ import annotations

from typing import Any, Optional

from ..models import Webhook, WebhookList
from .._http import AsyncHTTPClient, SyncHTTPClient

AVAILABLE_EVENTS = [
    "payment.pending",
    "payment.confirmed",
    "payment.failed",
    "agent.created",
    "agent.disabled",
]


def _build_webhook_payload(
    url: str,
    events: list[str],
    secret: Optional[str] = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"url": url, "events": events}
    if secret is not None:
        payload["secret"] = secret
    return payload


class WebhooksResource:
    """Webhooks API (synchronous)

    Examples:
        >>> webhook = client.webhooks.create(
        ...     url="https://myapp.com/webhooks/rosud",
        ...     events=["payment.confirmed", "payment.failed"],
        ...     secret="my-hmac-secret",
        ... )
        >>> print(webhook.id)

        >>> webhooks = client.webhooks.list()
    """

    def __init__(self, http: SyncHTTPClient) -> None:
        self._http = http

    def create(
        self,
        url: str,
        events: list[str],
        secret: Optional[str] = None,
    ) -> Webhook:
        """Register a webhook.

        Args:
            url: Webhook receiver URL (HTTPS recommended)
            events: List of events to subscribe to
                    Possible values: payment.pending, payment.confirmed, payment.failed,
                                     agent.created, agent.disabled
            secret: HMAC signature verification secret (optional, 8+ characters)

        Returns:
            Webhook: The registered webhook object

        Raises:
            ValidationError: If URL is invalid or events list is empty
            AuthenticationError: API key error
        """
        payload = _build_webhook_payload(url, events, secret)
        data = self._http.post("/v1/webhooks", json=payload)
        return Webhook.model_validate(data)

    def list(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> WebhookList:
        """List registered webhooks.

        Args:
            limit: Maximum number of results to return (default: 20)
            offset: Number of results to skip (default: 0)

        Returns:
            WebhookList: List of webhooks (iterable)
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        data = self._http.get("/v1/webhooks", params=params)
        return WebhookList.model_validate(data)

    def get(self, webhook_id: str) -> Webhook:
        """Retrieve a specific webhook.

        Args:
            webhook_id: Webhook UUID

        Returns:
            Webhook: The webhook object

        Raises:
            NotFoundError: If the webhook is not found
        """
        data = self._http.get(f"/v1/webhooks/{webhook_id}")
        return Webhook.model_validate(data)

    def delete(self, webhook_id: str) -> None:
        """Delete a webhook.

        Args:
            webhook_id: Webhook UUID

        Raises:
            NotFoundError: If the webhook is not found
        """
        self._http.delete(f"/v1/webhooks/{webhook_id}")


class AsyncWebhooksResource:
    """Webhooks API (asynchronous)"""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def create(
        self,
        url: str,
        events: list[str],
        secret: Optional[str] = None,
    ) -> Webhook:
        """Register a webhook (async)."""
        payload = _build_webhook_payload(url, events, secret)
        data = await self._http.post("/v1/webhooks", json=payload)
        return Webhook.model_validate(data)

    async def list(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> WebhookList:
        """List webhooks (async)."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        data = await self._http.get("/v1/webhooks", params=params)
        return WebhookList.model_validate(data)

    async def get(self, webhook_id: str) -> Webhook:
        """Retrieve a specific webhook (async)."""
        data = await self._http.get(f"/v1/webhooks/{webhook_id}")
        return Webhook.model_validate(data)

    async def delete(self, webhook_id: str) -> None:
        """Delete a webhook (async)."""
        await self._http.delete(f"/v1/webhooks/{webhook_id}")
