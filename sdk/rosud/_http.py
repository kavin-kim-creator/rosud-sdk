"""Rosud SDK HTTP client (httpx-based, with retry logic)"""
from __future__ import annotations

import time
from typing import Any

import httpx

from .exceptions import (
    ConnectionError,
    RosudError,
    ServerError,
    TimeoutError,
    _raise_for_status,
)

DEFAULT_BASE_URL = "https://api.rosud.com"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}


def _build_headers(api_key: str) -> dict[str, str]:
    return {
        "X-API-Key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "rosud-python/0.1.0",
    }


def _should_retry(status_code: int, attempt: int, max_retries: int) -> bool:
    return status_code in RETRY_STATUS_CODES and attempt < max_retries


def _backoff_wait(attempt: int) -> float:
    """Exponential backoff: 1s, 2s, 4s"""
    return min(2 ** attempt, 16)


class SyncHTTPClient:
    """Synchronous HTTP client"""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._headers = _build_headers(api_key)
        self._client = http_client or httpx.Client(
            timeout=httpx.Timeout(timeout),
            headers=self._headers,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> SyncHTTPClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        last_exc: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                response = self._client.request(
                    method,
                    url,
                    params=params,
                    json=json,
                    headers=self._headers,
                )
            except httpx.TimeoutException as e:
                raise TimeoutError(
                    f"Request timed out ({self._timeout}s): {method} {path}"
                ) from e
            except httpx.ConnectError as e:
                raise ConnectionError(
                    f"Cannot connect to server: {self._base_url}"
                ) from e
            except httpx.RequestError as e:
                raise RosudError(f"Request error: {e}") from e

            # Successful response
            if response.status_code < 400:
                return response.json()

            # Retryable error
            if _should_retry(response.status_code, attempt, self._max_retries):
                wait = _backoff_wait(attempt)
                time.sleep(wait)
                continue

            # Error handling
            try:
                body = response.json()
            except Exception:
                body = {"error": "parse_error", "message": response.text or f"HTTP {response.status_code}"}

            _raise_for_status(response.status_code, body)

        # All retries exhausted
        raise ServerError(f"Maximum retries ({self._max_retries}) exceeded")

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.request("GET", path, params=params)

    def post(self, path: str, *, json: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.request("POST", path, json=json)

    def delete(self, path: str) -> dict[str, Any]:
        return self.request("DELETE", path)


class AsyncHTTPClient:
    """Asynchronous HTTP client"""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._headers = _build_headers(api_key)
        self._client = http_client or httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers=self._headers,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> AsyncHTTPClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        import asyncio

        url = f"{self._base_url}{path}"

        for attempt in range(self._max_retries + 1):
            try:
                response = await self._client.request(
                    method,
                    url,
                    params=params,
                    json=json,
                    headers=self._headers,
                )
            except httpx.TimeoutException as e:
                raise TimeoutError(
                    f"Request timed out ({self._timeout}s): {method} {path}"
                ) from e
            except httpx.ConnectError as e:
                raise ConnectionError(
                    f"Cannot connect to server: {self._base_url}"
                ) from e
            except httpx.RequestError as e:
                raise RosudError(f"Request error: {e}") from e

            # Successful response
            if response.status_code < 400:
                return response.json()

            # Retryable error
            if _should_retry(response.status_code, attempt, self._max_retries):
                wait = _backoff_wait(attempt)
                await asyncio.sleep(wait)
                continue

            # Error handling
            try:
                body = response.json()
            except Exception:
                body = {"error": "parse_error", "message": response.text or f"HTTP {response.status_code}"}

            _raise_for_status(response.status_code, body)

        raise ServerError(f"Maximum retries ({self._max_retries}) exceeded")

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self.request("GET", path, params=params)

    async def post(self, path: str, *, json: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self.request("POST", path, json=json)

    async def delete(self, path: str) -> dict[str, Any]:
        return await self.request("DELETE", path)
