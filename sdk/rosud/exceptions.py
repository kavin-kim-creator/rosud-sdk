"""Rosud SDK exception classes"""
from __future__ import annotations

from typing import Any


class RosudError(Exception):
    """Base exception for Rosud SDK"""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        error_code: str | None = None,
        response_body: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.response_body = response_body
        super().__init__(message)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"status_code={self.status_code}, "
            f"error_code={self.error_code!r})"
        )


class AuthenticationError(RosudError):
    """API key is invalid or missing (HTTP 401/403)"""


class PaymentError(RosudError):
    """Error during payment processing"""


class InsufficientFundsError(PaymentError):
    """Insufficient balance"""


class SpendingLimitExceededError(PaymentError):
    """Spending limit exceeded"""


class RecipientNotAllowedError(PaymentError):
    """Recipient address not allowed"""


class ValidationError(RosudError):
    """Request parameter validation failed (HTTP 422)"""

    def __init__(
        self,
        message: str,
        field_errors: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> None:
        self.field_errors = field_errors or []
        super().__init__(message, **kwargs)

    def __str__(self) -> str:
        if self.field_errors:
            errors = "; ".join(
                f"{e.get('loc', ['unknown'])[-1]}: {e.get('msg', 'invalid')}"
                for e in self.field_errors
            )
            return f"{self.message} - Field errors: {errors}"
        return self.message


class NotFoundError(RosudError):
    """Resource not found (HTTP 404)"""


class RateLimitError(RosudError):
    """Request rate limit exceeded (HTTP 429)"""

    def __init__(self, message: str, retry_after: int | None = None, **kwargs: Any) -> None:
        self.retry_after = retry_after
        super().__init__(message, **kwargs)


class ServerError(RosudError):
    """Internal server error (HTTP 5xx)"""


class TimeoutError(RosudError):
    """Request timeout"""


class ConnectionError(RosudError):
    """Network connection error"""


def _raise_for_status(status_code: int, body: dict[str, Any]) -> None:
    """Raise the appropriate exception based on HTTP status code."""
    error_code = body.get("error", "unknown_error")
    message = body.get("message", f"HTTP {status_code} error")

    if status_code == 401:
        raise AuthenticationError(message, status_code=status_code, error_code=error_code, response_body=body)
    elif status_code == 403:
        # Map payment-related 403 to more specific exceptions
        if error_code == "spending_limit_exceeded":
            raise SpendingLimitExceededError(message, status_code=status_code, error_code=error_code, response_body=body)
        elif error_code == "recipient_not_allowed":
            raise RecipientNotAllowedError(message, status_code=status_code, error_code=error_code, response_body=body)
        raise AuthenticationError(message, status_code=status_code, error_code=error_code, response_body=body)
    elif status_code == 404:
        raise NotFoundError(message, status_code=status_code, error_code=error_code, response_body=body)
    elif status_code == 422:
        field_errors = body.get("detail", [])
        raise ValidationError(
            message,
            field_errors=field_errors if isinstance(field_errors, list) else [],
            status_code=status_code,
            error_code=error_code,
            response_body=body,
        )
    elif status_code == 429:
        retry_after = body.get("retry_after")
        raise RateLimitError(
            message,
            retry_after=int(retry_after) if retry_after else None,
            status_code=status_code,
            error_code=error_code,
            response_body=body,
        )
    elif status_code == 402 or error_code == "insufficient_funds":
        raise InsufficientFundsError(message, status_code=status_code, error_code=error_code, response_body=body)
    elif 400 <= status_code < 500:
        if "payment" in error_code:
            raise PaymentError(message, status_code=status_code, error_code=error_code, response_body=body)
        raise RosudError(message, status_code=status_code, error_code=error_code, response_body=body)
    elif status_code >= 500:
        raise ServerError(message, status_code=status_code, error_code=error_code, response_body=body)
