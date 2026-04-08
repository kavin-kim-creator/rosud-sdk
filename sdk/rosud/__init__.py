"""
Rosud Python SDK - Autonomous USDC payment infrastructure for AI agents

Quick Start:
    >>> import rosud
    >>> client = rosud.Rosud(api_key="rosud_live_xxx")
    >>> payment = client.payments.create(amount=5.00, to="0xRecipient", memo="fee")
    >>> print(payment.id, payment.status)

Async:
    >>> client = rosud.AsyncRosud(api_key="rosud_live_xxx")
    >>> payment = await client.payments.create(amount=1.00, to="0xAddr")
"""
from .client import AsyncRosud, Rosud
from .exceptions import (
    AuthenticationError,
    ConnectionError,
    InsufficientFundsError,
    NotFoundError,
    PaymentError,
    RateLimitError,
    RecipientNotAllowedError,
    RosudError,
    ServerError,
    SpendingLimitExceededError,
    TimeoutError,
    ValidationError,
)
from .models import (
    Agent,
    AgentCreated,
    AgentList,
    Payment,
    PaymentList,
    WalletBalance,
    Webhook,
    WebhookList,
)

__version__ = "0.1.0"
__all__ = [
    # Clients
    "Rosud",
    "AsyncRosud",
    # Models
    "Payment",
    "PaymentList",
    "Agent",
    "AgentCreated",
    "AgentList",
    "WalletBalance",
    "Webhook",
    "WebhookList",
    # Exceptions
    "RosudError",
    "AuthenticationError",
    "PaymentError",
    "InsufficientFundsError",
    "SpendingLimitExceededError",
    "RecipientNotAllowedError",
    "ValidationError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    "TimeoutError",
    "ConnectionError",
]
