"""Payment resource"""
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
    """Payments API (synchronous)

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
        """Create a USDC payment.

        Args:
            amount: Payment amount in USDC (e.g., 5.00)
            to: Recipient wallet address (e.g., "0xRecipientAddress")
            currency: Currency (default: "USDC")
            memo: Payment memo (optional)
            idempotency_key: Deduplication key (optional)

        Returns:
            Payment: The created payment object

        Raises:
            ValidationError: If amount <= 0 or to is empty
            InsufficientFundsError: Insufficient balance
            SpendingLimitExceededError: Spending limit exceeded
            RecipientNotAllowedError: Recipient not allowed
            AuthenticationError: API key error
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
        """List payments.

        Args:
            limit: Maximum number of results to return (default: 20)
            offset: Number of results to skip (default: 0)
            status: Status filter ("pending", "confirmed", "failed")

        Returns:
            PaymentList: List of payments (iterable)
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if status is not None:
            params["status"] = status
        data = self._http.get("/v1/payments", params=params)
        return PaymentList.model_validate(data)

    def get(self, payment_id: str) -> Payment:
        """Retrieve a specific payment.

        Args:
            payment_id: Payment UUID

        Returns:
            Payment: The payment object

        Raises:
            NotFoundError: If the payment is not found
        """
        data = self._http.get(f"/v1/payments/{payment_id}")
        return Payment.model_validate(data)


class AsyncPaymentsResource:
    """Payments API (asynchronous)

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
        """Create a USDC payment (async).

        Args:
            amount: Payment amount in USDC
            to: Recipient wallet address
            currency: Currency (default: "USDC")
            memo: Payment memo (optional)
            idempotency_key: Deduplication key (optional)

        Returns:
            Payment: The created payment object
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
        """List payments (async)."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if status is not None:
            params["status"] = status
        data = await self._http.get("/v1/payments", params=params)
        return PaymentList.model_validate(data)

    async def get(self, payment_id: str) -> Payment:
        """Retrieve a specific payment (async)."""
        data = await self._http.get(f"/v1/payments/{payment_id}")
        return Payment.model_validate(data)
