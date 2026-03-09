"""Rosud API HTTP 클라이언트"""
from typing import Any, Optional

import httpx

from .config import settings


class RosudAPIError(Exception):
    def __init__(self, status_code: int, error: str, message: str):
        self.status_code = status_code
        self.error = error
        self.message = message
        super().__init__(f"[{status_code}] {error}: {message}")


class RosudClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.rosud_api_key
        self.base_url = (base_url or settings.rosud_api_url).rstrip("/")

        if not self.api_key:
            raise ValueError(
                "ROSUD_API_KEY 환경변수가 설정되지 않았습니다. "
                "export ROSUD_API_KEY=rosud_live_xxx 로 설정하세요."
            )

    def _headers(self) -> dict[str, str]:
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _raise_for_error(self, response: httpx.Response) -> None:
        if response.status_code >= 400:
            try:
                body = response.json()
                error = body.get("error", "unknown_error")
                message = body.get("message", response.text)
            except Exception:
                error = "parse_error"
                message = response.text
            raise RosudAPIError(response.status_code, error, message)

    async def create_payment(
        self,
        amount: float,
        to: str,
        memo: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"amount": amount, "to": to}
        if memo:
            payload["memo"] = memo
        if idempotency_key:
            payload["idempotency_key"] = idempotency_key

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/payments",
                json=payload,
                headers=self._headers(),
            )
        self._raise_for_error(response)
        return response.json()

    async def get_balance(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/v1/wallets/balance",
                headers=self._headers(),
            )
        self._raise_for_error(response)
        return response.json()

    async def list_payments(
        self,
        limit: int = 10,
        status: Optional[str] = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit}
        if status:
            params["status"] = status

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/v1/payments",
                params=params,
                headers=self._headers(),
            )
        self._raise_for_error(response)
        return response.json()

    async def get_payment(self, payment_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/v1/payments/{payment_id}",
                headers=self._headers(),
            )
        self._raise_for_error(response)
        return response.json()
