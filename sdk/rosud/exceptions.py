"""Rosud SDK 예외 클래스"""
from __future__ import annotations

from typing import Any


class RosudError(Exception):
    """Rosud SDK 기본 예외"""

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
    """API 키가 유효하지 않거나 누락됨 (HTTP 401/403)"""


class PaymentError(RosudError):
    """결제 처리 중 오류"""


class InsufficientFundsError(PaymentError):
    """잔액 부족"""


class SpendingLimitExceededError(PaymentError):
    """지출 한도 초과"""


class RecipientNotAllowedError(PaymentError):
    """허용되지 않은 수신자 주소"""


class ValidationError(RosudError):
    """요청 파라미터 유효성 검사 실패 (HTTP 422)"""

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
            return f"{self.message} - 필드 오류: {errors}"
        return self.message


class NotFoundError(RosudError):
    """리소스를 찾을 수 없음 (HTTP 404)"""


class RateLimitError(RosudError):
    """요청 속도 제한 초과 (HTTP 429)"""

    def __init__(self, message: str, retry_after: int | None = None, **kwargs: Any) -> None:
        self.retry_after = retry_after
        super().__init__(message, **kwargs)


class ServerError(RosudError):
    """서버 내부 오류 (HTTP 5xx)"""


class TimeoutError(RosudError):
    """요청 타임아웃"""


class ConnectionError(RosudError):
    """네트워크 연결 오류"""


def _raise_for_status(status_code: int, body: dict[str, Any]) -> None:
    """HTTP 상태코드에 따라 적절한 예외를 발생시킵니다."""
    error_code = body.get("error", "unknown_error")
    message = body.get("message", f"HTTP {status_code} 오류")

    if status_code == 401:
        raise AuthenticationError(message, status_code=status_code, error_code=error_code, response_body=body)
    elif status_code == 403:
        # 결제 관련 403은 더 구체적인 예외로
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
