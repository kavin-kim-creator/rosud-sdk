"""웹훅 리소스"""
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
    """웹훅 API (동기)

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
        """웹훅을 등록합니다.

        Args:
            url: 웹훅 수신 URL (HTTPS 권장)
            events: 구독할 이벤트 목록
                    가능한 값: payment.pending, payment.confirmed, payment.failed,
                              agent.created, agent.disabled
            secret: HMAC 서명 검증용 시크릿 (선택, 8자 이상)

        Returns:
            Webhook: 등록된 웹훅 객체

        Raises:
            ValidationError: URL이 유효하지 않거나 events가 비어있는 경우
            AuthenticationError: API 키 오류
        """
        payload = _build_webhook_payload(url, events, secret)
        data = self._http.post("/v1/webhooks", json=payload)
        return Webhook.model_validate(data)

    def list(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> WebhookList:
        """등록된 웹훅 목록을 조회합니다.

        Args:
            limit: 최대 반환 건수 (기본값: 20)
            offset: 건너뛸 건수 (기본값: 0)

        Returns:
            WebhookList: 웹훅 목록 (이터러블)
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        data = self._http.get("/v1/webhooks", params=params)
        return WebhookList.model_validate(data)

    def get(self, webhook_id: str) -> Webhook:
        """특정 웹훅을 조회합니다.

        Args:
            webhook_id: 웹훅 UUID

        Returns:
            Webhook: 웹훅 객체

        Raises:
            NotFoundError: 웹훅을 찾을 수 없는 경우
        """
        data = self._http.get(f"/v1/webhooks/{webhook_id}")
        return Webhook.model_validate(data)

    def delete(self, webhook_id: str) -> None:
        """웹훅을 삭제합니다.

        Args:
            webhook_id: 웹훅 UUID

        Raises:
            NotFoundError: 웹훅을 찾을 수 없는 경우
        """
        self._http.delete(f"/v1/webhooks/{webhook_id}")


class AsyncWebhooksResource:
    """웹훅 API (비동기)"""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def create(
        self,
        url: str,
        events: list[str],
        secret: Optional[str] = None,
    ) -> Webhook:
        """웹훅을 등록합니다 (비동기)."""
        payload = _build_webhook_payload(url, events, secret)
        data = await self._http.post("/v1/webhooks", json=payload)
        return Webhook.model_validate(data)

    async def list(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> WebhookList:
        """웹훅 목록을 조회합니다 (비동기)."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        data = await self._http.get("/v1/webhooks", params=params)
        return WebhookList.model_validate(data)

    async def get(self, webhook_id: str) -> Webhook:
        """특정 웹훅을 조회합니다 (비동기)."""
        data = await self._http.get(f"/v1/webhooks/{webhook_id}")
        return Webhook.model_validate(data)

    async def delete(self, webhook_id: str) -> None:
        """웹훅을 삭제합니다 (비동기)."""
        await self._http.delete(f"/v1/webhooks/{webhook_id}")
