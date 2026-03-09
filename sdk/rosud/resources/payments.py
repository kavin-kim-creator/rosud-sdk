"""결제 리소스"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from ..models import Payment, PaymentList
from .._http import AsyncHTTPClient, SyncHTTPClient


def _build_payment_payload(
    amount: float | Decimal,
    to: str,
    currency: str = "USDC",
    memo: Optional[str] = None,
    idempotency_key: Optional[str] = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "amount": str(Decimal(str(amount))),
        "to": to,
        "currency": currency,
    }
    if memo is not None:
        payload["memo"] = memo
    if idempotency_key is not None:
        payload["idempotency_key"] = idempotency_key
    return payload


class PaymentsResource:
    """결제 API (동기)

    Examples:
        >>> payment = client.payments.create(amount=5.00, to="0xRecipient", memo="fee")
        >>> payment.id, payment.status

        >>> payments = client.payments.list(limit=10)
        >>> for p in payments:
        ...     print(p.id, p.amount, p.status)

        >>> payment = client.payments.get("payment-uuid")
    """

    def __init__(self, http: SyncHTTPClient) -> None:
        self._http = http

    def create(
        self,
        amount: float | Decimal,
        to: str,
        currency: str = "USDC",
        memo: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Payment:
        """USDC 결제를 생성합니다.

        Args:
            amount: 결제 금액 (USDC 기준, 예: 5.00)
            to: 수신자 지갑 주소 (예: "0xRecipientAddress")
            currency: 통화 (기본값: "USDC")
            memo: 결제 메모 (선택)
            idempotency_key: 중복 방지 키 (선택)

        Returns:
            Payment: 생성된 결제 객체

        Raises:
            ValidationError: amount <= 0이거나 to가 비어있는 경우
            InsufficientFundsError: 잔액 부족
            SpendingLimitExceededError: 지출 한도 초과
            RecipientNotAllowedError: 허용되지 않은 수신자
            AuthenticationError: API 키 오류
        """
        payload = _build_payment_payload(amount, to, currency, memo, idempotency_key)
        data = self._http.post("/v1/payments", json=payload)
        return Payment.model_validate(data)

    def list(
        self,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> PaymentList:
        """결제 목록을 조회합니다.

        Args:
            limit: 최대 반환 건수 (기본값: 20)
            offset: 건너뛸 건수 (기본값: 0)
            status: 상태 필터 ("pending", "confirmed", "failed")

        Returns:
            PaymentList: 결제 목록 (이터러블)
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if status is not None:
            params["status"] = status
        data = self._http.get("/v1/payments", params=params)
        return PaymentList.model_validate(data)

    def get(self, payment_id: str) -> Payment:
        """특정 결제를 조회합니다.

        Args:
            payment_id: 결제 UUID

        Returns:
            Payment: 결제 객체

        Raises:
            NotFoundError: 결제를 찾을 수 없는 경우
        """
        data = self._http.get(f"/v1/payments/{payment_id}")
        return Payment.model_validate(data)


class AsyncPaymentsResource:
    """결제 API (비동기)

    Examples:
        >>> payment = await client.payments.create(amount=5.00, to="0xRecipient")
        >>> payments = await client.payments.list(limit=10)
        >>> payment = await client.payments.get("payment-uuid")
    """

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def create(
        self,
        amount: float | Decimal,
        to: str,
        currency: str = "USDC",
        memo: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Payment:
        """USDC 결제를 생성합니다 (비동기).

        Args:
            amount: 결제 금액 (USDC)
            to: 수신자 지갑 주소
            currency: 통화 (기본값: "USDC")
            memo: 결제 메모 (선택)
            idempotency_key: 중복 방지 키 (선택)

        Returns:
            Payment: 생성된 결제 객체
        """
        payload = _build_payment_payload(amount, to, currency, memo, idempotency_key)
        data = await self._http.post("/v1/payments", json=payload)
        return Payment.model_validate(data)

    async def list(
        self,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> PaymentList:
        """결제 목록을 조회합니다 (비동기)."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if status is not None:
            params["status"] = status
        data = await self._http.get("/v1/payments", params=params)
        return PaymentList.model_validate(data)

    async def get(self, payment_id: str) -> Payment:
        """특정 결제를 조회합니다 (비동기)."""
        data = await self._http.get(f"/v1/payments/{payment_id}")
        return Payment.model_validate(data)
