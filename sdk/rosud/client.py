"""Rosud SDK 메인 클라이언트"""
from __future__ import annotations

import os
from typing import Optional

import httpx

from ._http import AsyncHTTPClient, SyncHTTPClient, DEFAULT_BASE_URL, DEFAULT_TIMEOUT, DEFAULT_MAX_RETRIES
from .resources import (
    AgentsResource,
    AsyncAgentsResource,
    AsyncPaymentsResource,
    AsyncWalletsResource,
    AsyncWebhooksResource,
    PaymentsResource,
    WalletsResource,
    WebhooksResource,
)


def _resolve_api_key(api_key: Optional[str]) -> str:
    """API 키를 인자 또는 환경변수에서 읽어옵니다."""
    key = api_key or os.environ.get("ROSUD_API_KEY")
    if not key:
        raise ValueError(
            "API 키가 필요합니다. "
            "Rosud(api_key='rosud_live_xxx') 또는 "
            "ROSUD_API_KEY 환경변수를 설정하세요."
        )
    return key


class Rosud:
    """Rosud 동기 클라이언트

    AI 에이전트가 USDC 스테이블코인으로 자율 결제하는 인프라 SDK

    Args:
        api_key: Rosud API 키 (rosud_live_xxx 형식).
                 None이면 ROSUD_API_KEY 환경변수를 사용합니다.
        base_url: API 서버 URL (기본값: https://api.rosud.com)
        timeout: 요청 타임아웃 (초, 기본값: 30)
        max_retries: 최대 재시도 횟수 (기본값: 3)
        http_client: 커스텀 httpx.Client (고급 설정용)

    Examples:
        >>> import rosud
        >>> client = rosud.Rosud(api_key="rosud_live_xxx")

        # 환경변수 사용
        >>> import os
        >>> os.environ["ROSUD_API_KEY"] = "rosud_live_xxx"
        >>> client = rosud.Rosud()

        # context manager 사용
        >>> with rosud.Rosud(api_key="rosud_live_xxx") as client:
        ...     payment = client.payments.create(amount=5.00, to="0xAddr")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        resolved_key = _resolve_api_key(api_key)
        self._http = SyncHTTPClient(
            api_key=resolved_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            http_client=http_client,
        )
        self.payments = PaymentsResource(self._http)
        self.agents = AgentsResource(self._http)
        self.wallets = WalletsResource(self._http)
        self.webhooks = WebhooksResource(self._http)

    def close(self) -> None:
        """HTTP 연결을 닫습니다."""
        self._http.close()

    def __enter__(self) -> Rosud:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"Rosud(base_url={self._http._base_url!r})"


class AsyncRosud:
    """Rosud 비동기 클라이언트

    Args:
        api_key: Rosud API 키 (rosud_live_xxx 형식).
                 None이면 ROSUD_API_KEY 환경변수를 사용합니다.
        base_url: API 서버 URL (기본값: https://api.rosud.com)
        timeout: 요청 타임아웃 (초, 기본값: 30)
        max_retries: 최대 재시도 횟수 (기본값: 3)
        http_client: 커스텀 httpx.AsyncClient (고급 설정용)

    Examples:
        >>> import asyncio
        >>> import rosud

        >>> async def main():
        ...     client = rosud.AsyncRosud(api_key="rosud_live_xxx")
        ...     payment = await client.payments.create(amount=1.00, to="0xAddr")
        ...     await client.aclose()

        # async context manager 사용
        >>> async def main():
        ...     async with rosud.AsyncRosud(api_key="rosud_live_xxx") as client:
        ...         balance = await client.wallets.get_balance()
        ...         print(balance.amount)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        resolved_key = _resolve_api_key(api_key)
        self._http = AsyncHTTPClient(
            api_key=resolved_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            http_client=http_client,
        )
        self.payments = AsyncPaymentsResource(self._http)
        self.agents = AsyncAgentsResource(self._http)
        self.wallets = AsyncWalletsResource(self._http)
        self.webhooks = AsyncWebhooksResource(self._http)

    async def aclose(self) -> None:
        """HTTP 연결을 닫습니다."""
        await self._http.aclose()

    async def __aenter__(self) -> AsyncRosud:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    def __repr__(self) -> str:
        return f"AsyncRosud(base_url={self._http._base_url!r})"
