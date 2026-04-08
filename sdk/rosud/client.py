"""Rosud SDK main client"""
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
    """Read the API key from the argument or environment variable."""
    key = api_key or os.environ.get("ROSUD_API_KEY")
    if not key:
        raise ValueError(
            "API key is required. "
            "Pass Rosud(api_key='rosud_live_xxx') or "
            "set the ROSUD_API_KEY environment variable."
        )
    return key


class Rosud:
    """Rosud synchronous client

    Infrastructure SDK for AI agents to make autonomous USDC stablecoin payments

    Args:
        api_key: Rosud API key (format: rosud_live_xxx).
                 If None, uses the ROSUD_API_KEY environment variable.
        base_url: API server URL (default: https://api.rosud.com)
        timeout: Request timeout in seconds (default: 30)
        max_retries: Maximum retry attempts (default: 3)
        http_client: Custom httpx.Client (for advanced configuration)

    Examples:
        >>> import rosud
        >>> client = rosud.Rosud(api_key="rosud_live_xxx")

        # Using environment variable
        >>> import os
        >>> os.environ["ROSUD_API_KEY"] = "rosud_live_xxx"
        >>> client = rosud.Rosud()

        # Using context manager
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
        """Close the HTTP connection."""
        self._http.close()

    def __enter__(self) -> Rosud:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"Rosud(base_url={self._http._base_url!r})"


class AsyncRosud:
    """Rosud asynchronous client

    Args:
        api_key: Rosud API key (format: rosud_live_xxx).
                 If None, uses the ROSUD_API_KEY environment variable.
        base_url: API server URL (default: https://api.rosud.com)
        timeout: Request timeout in seconds (default: 30)
        max_retries: Maximum retry attempts (default: 3)
        http_client: Custom httpx.AsyncClient (for advanced configuration)

    Examples:
        >>> import asyncio
        >>> import rosud

        >>> async def main():
        ...     client = rosud.AsyncRosud(api_key="rosud_live_xxx")
        ...     payment = await client.payments.create(amount=1.00, to="0xAddr")
        ...     await client.aclose()

        # Using async context manager
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
        """Close the HTTP connection."""
        await self._http.aclose()

    async def __aenter__(self) -> AsyncRosud:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    def __repr__(self) -> str:
        return f"AsyncRosud(base_url={self._http._base_url!r})"
