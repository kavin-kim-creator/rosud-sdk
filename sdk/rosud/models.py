"""Rosud SDK 응답 모델 (Pydantic)"""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, Field


class Payment(BaseModel):
    """결제 응답 모델"""

    id: uuid.UUID
    agent_id: Optional[uuid.UUID] = None
    operator_id: Optional[uuid.UUID] = None
    amount: Decimal
    currency: str
    network: str
    from_wallet: Optional[str] = None
    to_wallet: str
    memo: Optional[str] = None
    status: str
    fee: Optional[Decimal] = None
    circle_transfer_id: Optional[str] = None
    tx_hash: Optional[str] = None
    idempotency_key: Optional[str] = None
    created_at: datetime
    confirmed_at: Optional[datetime] = None

    @property
    def is_confirmed(self) -> bool:
        return self.status == "confirmed"

    @property
    def is_pending(self) -> bool:
        return self.status == "pending"

    @property
    def is_failed(self) -> bool:
        return self.status == "failed"

    def __repr__(self) -> str:
        return f"Payment(id={self.id}, amount={self.amount} {self.currency}, status={self.status!r})"


class PaymentList(BaseModel):
    """결제 목록 응답 모델"""

    items: list[Payment]
    total: int
    limit: int
    offset: int

    def __iter__(self):  # type: ignore[override]
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int) -> Payment:
        return self.items[index]


class Agent(BaseModel):
    """에이전트 응답 모델"""

    id: uuid.UUID
    operator_id: uuid.UUID
    name: str
    spending_limit_daily: Optional[Decimal] = None
    spending_limit_per_tx: Optional[Decimal] = None
    allowed_recipients: Optional[list[str]] = None
    is_active: bool
    created_at: datetime

    def __repr__(self) -> str:
        return f"Agent(id={self.id}, name={self.name!r}, is_active={self.is_active})"


class AgentCreated(Agent):
    """에이전트 생성 응답 (API 키 포함 - 최초 1회만 반환)"""

    api_key: str = Field(..., description="최초 생성 시에만 반환. 안전하게 보관하세요.")

    def __repr__(self) -> str:
        masked_key = f"{self.api_key[:12]}..." if len(self.api_key) > 12 else "***"
        return f"AgentCreated(id={self.id}, name={self.name!r}, api_key={masked_key!r})"


class AgentList(BaseModel):
    """에이전트 목록 응답 모델"""

    items: list[Agent]
    total: int
    limit: int
    offset: int

    def __iter__(self):  # type: ignore[override]
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int) -> Agent:
        return self.items[index]


class WalletBalance(BaseModel):
    """지갑 잔액 응답 모델"""

    wallet_id: str
    address: str
    amount: Decimal
    currency: str
    network: str
    updated_at: Optional[datetime] = None

    def __repr__(self) -> str:
        return f"WalletBalance(address={self.address!r}, amount={self.amount} {self.currency})"


class Webhook(BaseModel):
    """웹훅 응답 모델"""

    id: uuid.UUID
    operator_id: uuid.UUID
    url: str
    events: list[str]
    is_active: bool
    created_at: datetime

    def __repr__(self) -> str:
        return f"Webhook(id={self.id}, url={self.url!r}, events={self.events})"


class WebhookList(BaseModel):
    """웹훅 목록 응답 모델"""

    items: list[Webhook]
    total: int
    limit: int
    offset: int

    def __iter__(self):  # type: ignore[override]
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int) -> Webhook:
        return self.items[index]
