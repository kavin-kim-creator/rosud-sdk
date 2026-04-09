"""리소스 API 단위 테스트 (payments, agents, wallets, webhooks)"""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rosud.models import (
    Agent,
    AgentCreated,
    AgentList,
    Payment,
    PaymentList,
    WalletBalance,
    Webhook,
    WebhookList,
)
from rosud.resources.agents import AgentsResource, AsyncAgentsResource
from rosud.resources.payments import AsyncPaymentsResource, PaymentsResource
from rosud.resources.wallets import AsyncWalletsResource, WalletsResource
from rosud.resources.webhooks import AsyncWebhooksResource, WebhooksResource


# ────────────────────────────────────────────────
# 테스트용 픽스처 헬퍼
# ────────────────────────────────────────────────

AGENT_ID = str(uuid.uuid4())
OPERATOR_ID = str(uuid.uuid4())
PAYMENT_ID = str(uuid.uuid4())
WEBHOOK_ID = str(uuid.uuid4())
NOW = datetime.now().isoformat()

PAYMENT_DATA = {
    "id": PAYMENT_ID,
    "agent_id": None,
    "operator_id": OPERATOR_ID,
    "amount": "5.00",
    "currency": "USDC",
    "network": "base",
    "from_wallet": "0xFromWallet",
    "to_wallet": "0xToWallet",
    "memo": "api_call_fee",
    "status": "confirmed",
    "fee": "0.01",
    "tx_hash": "0xabc123",
    "idempotency_key": None,
    "created_at": NOW,
    "confirmed_at": NOW,
}

AGENT_DATA = {
    "id": AGENT_ID,
    "operator_id": OPERATOR_ID,
    "name": "Test Bot",
    "spending_limit_daily": "100.00",
    "spending_limit_per_tx": "10.00",
    "allowed_recipients": None,
    "is_active": True,
    "created_at": NOW,
}

AGENT_CREATED_DATA = {**AGENT_DATA, "api_key": "rosud_live_testkey123456"}

WALLET_BALANCE_DATA = {
    "wallet_id": "wallet-abc",
    "address": "0xMyWallet",
    "amount": "250.50",
    "currency": "USDC",
    "network": "base",
    "updated_at": NOW,
}

WEBHOOK_DATA = {
    "id": WEBHOOK_ID,
    "operator_id": OPERATOR_ID,
    "url": "https://example.com/webhook",
    "events": ["payment.confirmed", "payment.failed"],
    "is_active": True,
    "created_at": NOW,
}


def make_sync_http(return_value):
    """SyncHTTPClient 모킹 헬퍼"""
    http = MagicMock()
    http.post.return_value = return_value
    http.get.return_value = return_value
    http.delete.return_value = None
    return http


def make_async_http(return_value):
    """AsyncHTTPClient 모킹 헬퍼"""
    http = MagicMock()
    http.post = AsyncMock(return_value=return_value)
    http.get = AsyncMock(return_value=return_value)
    http.delete = AsyncMock(return_value=None)
    return http


# ────────────────────────────────────────────────
# PaymentsResource 동기 테스트
# ────────────────────────────────────────────────

class TestPaymentsResource:
    def test_create_returns_payment(self):
        http = make_sync_http(PAYMENT_DATA)
        resource = PaymentsResource(http)
        payment = resource.create(amount=5.00, to="0xToWallet", memo="api_call_fee")

        http.post.assert_called_once()
        call_kwargs = http.post.call_args
        assert call_kwargs[0][0] == "/v1/payments"
        assert Decimal(call_kwargs[1]["json"]["amount"]) == Decimal("5")
        assert call_kwargs[1]["json"]["to"] == "0xToWallet"
        assert call_kwargs[1]["json"]["memo"] == "api_call_fee"

        assert isinstance(payment, Payment)
        assert payment.is_confirmed
        assert payment.tx_hash == "0xabc123"

    def test_create_includes_idempotency_key(self):
        http = make_sync_http(PAYMENT_DATA)
        resource = PaymentsResource(http)
        resource.create(amount=1.00, to="0xAddr", idempotency_key="unique-key-123")

        payload = http.post.call_args[1]["json"]
        assert payload["idempotency_key"] == "unique-key-123"

    def test_create_without_memo_omits_field(self):
        http = make_sync_http(PAYMENT_DATA)
        resource = PaymentsResource(http)
        resource.create(amount=1.00, to="0xAddr")

        payload = http.post.call_args[1]["json"]
        assert "memo" not in payload

    def test_list_returns_payment_list(self):
        list_data = {
            "items": [PAYMENT_DATA],
            "total": 1,
            "limit": 20,
            "offset": 0,
        }
        http = make_sync_http(list_data)
        resource = PaymentsResource(http)
        payments = resource.list(limit=10)

        http.get.assert_called_once_with("/v1/payments", params={"limit": 10, "offset": 0})
        assert isinstance(payments, PaymentList)
        assert len(payments) == 1
        assert payments[0].currency == "USDC"

    def test_list_with_status_filter(self):
        list_data = {"items": [], "total": 0, "limit": 20, "offset": 0}
        http = make_sync_http(list_data)
        resource = PaymentsResource(http)
        resource.list(status="confirmed")

        params = http.get.call_args[1]["params"]
        assert params["status"] == "confirmed"

    def test_get_returns_payment(self):
        http = make_sync_http(PAYMENT_DATA)
        resource = PaymentsResource(http)
        payment = resource.get(PAYMENT_ID)

        http.get.assert_called_once_with(f"/v1/payments/{PAYMENT_ID}")
        assert isinstance(payment, Payment)

    def test_payment_decimal_precision(self):
        """Decimal 정밀도 보존 확인"""
        http = make_sync_http(PAYMENT_DATA)
        resource = PaymentsResource(http)
        resource.create(amount=0.001, to="0xAddr")

        payload = http.post.call_args[1]["json"]
        assert payload["amount"] == "0.001"


# ────────────────────────────────────────────────
# AsyncPaymentsResource 테스트
# ────────────────────────────────────────────────

class TestAsyncPaymentsResource:
    @pytest.mark.asyncio
    async def test_create_returns_payment(self):
        http = make_async_http(PAYMENT_DATA)
        resource = AsyncPaymentsResource(http)
        payment = await resource.create(amount=5.00, to="0xToWallet")

        assert isinstance(payment, Payment)
        assert payment.status == "confirmed"

    @pytest.mark.asyncio
    async def test_list_returns_payment_list(self):
        list_data = {"items": [PAYMENT_DATA], "total": 1, "limit": 20, "offset": 0}
        http = make_async_http(list_data)
        resource = AsyncPaymentsResource(http)
        payments = await resource.list()

        assert isinstance(payments, PaymentList)
        assert len(payments) == 1

    @pytest.mark.asyncio
    async def test_get_returns_payment(self):
        http = make_async_http(PAYMENT_DATA)
        resource = AsyncPaymentsResource(http)
        payment = await resource.get(PAYMENT_ID)

        http.get.assert_called_once_with(f"/v1/payments/{PAYMENT_ID}")
        assert isinstance(payment, Payment)


# ────────────────────────────────────────────────
# AgentsResource 동기 테스트
# ────────────────────────────────────────────────

class TestAgentsResource:
    def test_create_returns_agent_created(self):
        http = make_sync_http(AGENT_CREATED_DATA)
        resource = AgentsResource(http)
        agent = resource.create(
            name="Payment Bot",
            spending_limit_daily=100.00,
            spending_limit_per_tx=10.00,
        )

        http.post.assert_called_once()
        payload = http.post.call_args[1]["json"]
        assert payload["name"] == "Payment Bot"
        assert Decimal(payload["spending_limit_daily"]) == Decimal("100")
        assert Decimal(payload["spending_limit_per_tx"]) == Decimal("10")

        assert isinstance(agent, AgentCreated)
        assert agent.api_key == "rosud_live_testkey123456"
        # mock 응답은 AGENT_CREATED_DATA의 "Test Bot"을 반환 (정상 동작 확인)
        assert agent.name == "Test Bot"
        assert agent.is_active

    def test_create_minimal_agent(self):
        """이름만으로 에이전트 생성 (선택 필드 없음)"""
        http = make_sync_http(AGENT_CREATED_DATA)
        resource = AgentsResource(http)
        resource.create(name="Minimal Bot")

        payload = http.post.call_args[1]["json"]
        assert payload == {"name": "Minimal Bot"}
        assert "spending_limit_daily" not in payload
        assert "spending_limit_per_tx" not in payload

    def test_create_with_allowed_recipients(self):
        recipients = ["0xAddr1", "0xAddr2"]
        http = make_sync_http(AGENT_CREATED_DATA)
        resource = AgentsResource(http)
        resource.create(name="Restricted Bot", allowed_recipients=recipients)

        payload = http.post.call_args[1]["json"]
        assert payload["allowed_recipients"] == recipients

    def test_list_returns_agent_list(self):
        list_data = {"items": [AGENT_DATA], "total": 1, "limit": 20, "offset": 0}
        http = make_sync_http(list_data)
        resource = AgentsResource(http)
        agents = resource.list()

        http.get.assert_called_once_with("/v1/agents", params={"limit": 20, "offset": 0})
        assert isinstance(agents, AgentList)
        assert len(agents) == 1
        assert agents[0].name == "Test Bot"

    def test_list_with_active_filter(self):
        list_data = {"items": [], "total": 0, "limit": 20, "offset": 0}
        http = make_sync_http(list_data)
        resource = AgentsResource(http)
        resource.list(is_active=True)

        params = http.get.call_args[1]["params"]
        assert params["is_active"] is True

    def test_get_returns_agent(self):
        http = make_sync_http(AGENT_DATA)
        resource = AgentsResource(http)
        agent = resource.get(AGENT_ID)

        http.get.assert_called_once_with(f"/v1/agents/{AGENT_ID}")
        assert isinstance(agent, Agent)
        assert str(agent.id) == AGENT_ID

    def test_agent_repr_masks_key(self):
        agent = AgentCreated(**{
            "id": uuid.uuid4(),
            "operator_id": uuid.uuid4(),
            "name": "Test",
            "is_active": True,
            "created_at": datetime.now(),
            "api_key": "rosud_live_verylongkey_secret",
        })
        r = repr(agent)
        assert "verylongkey_secret" not in r
        assert "..." in r


# ────────────────────────────────────────────────
# AsyncAgentsResource 테스트
# ────────────────────────────────────────────────

class TestAsyncAgentsResource:
    @pytest.mark.asyncio
    async def test_create_returns_agent(self):
        http = make_async_http(AGENT_CREATED_DATA)
        resource = AsyncAgentsResource(http)
        agent = await resource.create(name="Async Bot", spending_limit_daily=50.0)

        assert isinstance(agent, AgentCreated)
        assert agent.api_key.startswith("rosud_live_")

    @pytest.mark.asyncio
    async def test_list_returns_agent_list(self):
        list_data = {"items": [AGENT_DATA], "total": 1, "limit": 20, "offset": 0}
        http = make_async_http(list_data)
        resource = AsyncAgentsResource(http)
        agents = await resource.list()

        assert len(agents) == 1

    @pytest.mark.asyncio
    async def test_get_returns_agent(self):
        http = make_async_http(AGENT_DATA)
        resource = AsyncAgentsResource(http)
        agent = await resource.get(AGENT_ID)

        assert isinstance(agent, Agent)


# ────────────────────────────────────────────────
# WalletsResource 테스트
# ────────────────────────────────────────────────

class TestWalletsResource:
    def test_get_balance_returns_wallet_balance(self):
        http = make_sync_http(WALLET_BALANCE_DATA)
        resource = WalletsResource(http)
        balance = resource.get_balance()

        http.get.assert_called_once_with("/v1/wallets/balance")
        assert isinstance(balance, WalletBalance)
        assert balance.amount == Decimal("250.50")
        assert balance.currency == "USDC"
        assert balance.network == "base"
        assert balance.address == "0xMyWallet"

    def test_wallet_balance_repr(self):
        balance = WalletBalance(**WALLET_BALANCE_DATA)
        r = repr(balance)
        assert "250.50" in r
        assert "USDC" in r

    @pytest.mark.asyncio
    async def test_async_get_balance(self):
        http = make_async_http(WALLET_BALANCE_DATA)
        resource = AsyncWalletsResource(http)
        balance = await resource.get_balance()

        http.get.assert_called_once_with("/v1/wallets/balance")
        assert isinstance(balance, WalletBalance)
        assert balance.amount == Decimal("250.50")


# ────────────────────────────────────────────────
# WebhooksResource 테스트
# ────────────────────────────────────────────────

class TestWebhooksResource:
    def test_create_returns_webhook(self):
        http = make_sync_http(WEBHOOK_DATA)
        resource = WebhooksResource(http)
        webhook = resource.create(
            url="https://example.com/webhook",
            events=["payment.confirmed", "payment.failed"],
            secret="my-hmac-secret",
        )

        http.post.assert_called_once()
        payload = http.post.call_args[1]["json"]
        assert payload["url"] == "https://example.com/webhook"
        assert "payment.confirmed" in payload["events"]
        assert payload["secret"] == "my-hmac-secret"

        assert isinstance(webhook, Webhook)
        assert webhook.is_active
        assert webhook.url == "https://example.com/webhook"

    def test_create_without_secret(self):
        http = make_sync_http(WEBHOOK_DATA)
        resource = WebhooksResource(http)
        resource.create(url="https://example.com/wh", events=["payment.confirmed"])

        payload = http.post.call_args[1]["json"]
        assert "secret" not in payload

    def test_list_returns_webhook_list(self):
        list_data = {"items": [WEBHOOK_DATA], "total": 1, "limit": 20, "offset": 0}
        http = make_sync_http(list_data)
        resource = WebhooksResource(http)
        webhooks = resource.list()

        http.get.assert_called_once_with("/v1/webhooks", params={"limit": 20, "offset": 0})
        assert isinstance(webhooks, WebhookList)
        assert len(webhooks) == 1

    def test_get_returns_webhook(self):
        http = make_sync_http(WEBHOOK_DATA)
        resource = WebhooksResource(http)
        webhook = resource.get(WEBHOOK_ID)

        http.get.assert_called_once_with(f"/v1/webhooks/{WEBHOOK_ID}")
        assert isinstance(webhook, Webhook)

    def test_delete_calls_correct_endpoint(self):
        http = make_sync_http(WEBHOOK_DATA)
        resource = WebhooksResource(http)
        resource.delete(WEBHOOK_ID)

        http.delete.assert_called_once_with(f"/v1/webhooks/{WEBHOOK_ID}")

    def test_webhook_repr(self):
        webhook = Webhook(**WEBHOOK_DATA)
        r = repr(webhook)
        assert "example.com" in r
        assert "payment.confirmed" in r


# ────────────────────────────────────────────────
# AsyncWebhooksResource 테스트
# ────────────────────────────────────────────────

class TestAsyncWebhooksResource:
    @pytest.mark.asyncio
    async def test_create_returns_webhook(self):
        http = make_async_http(WEBHOOK_DATA)
        resource = AsyncWebhooksResource(http)
        webhook = await resource.create(
            url="https://example.com/webhook",
            events=["payment.confirmed"],
        )

        assert isinstance(webhook, Webhook)
        assert webhook.is_active

    @pytest.mark.asyncio
    async def test_list_returns_webhook_list(self):
        list_data = {"items": [WEBHOOK_DATA], "total": 1, "limit": 20, "offset": 0}
        http = make_async_http(list_data)
        resource = AsyncWebhooksResource(http)
        webhooks = await resource.list()

        assert isinstance(webhooks, WebhookList)
        assert len(webhooks) == 1

    @pytest.mark.asyncio
    async def test_delete_is_called(self):
        http = make_async_http(None)
        resource = AsyncWebhooksResource(http)
        await resource.delete(WEBHOOK_ID)

        http.delete.assert_called_once_with(f"/v1/webhooks/{WEBHOOK_ID}")


# ────────────────────────────────────────────────
# 모델 반복자/인덱서 테스트
# ────────────────────────────────────────────────

class TestListModels:
    def _make_payment(self) -> dict:
        return PAYMENT_DATA.copy()

    def test_payment_list_iteration(self):
        items = [Payment(**PAYMENT_DATA) for _ in range(3)]
        plist = PaymentList(items=items, total=3, limit=20, offset=0)
        collected = [p for p in plist]
        assert len(collected) == 3

    def test_agent_list_indexing(self):
        items = [Agent(**AGENT_DATA) for _ in range(2)]
        alist = AgentList(items=items, total=2, limit=20, offset=0)
        assert alist[0].name == "Test Bot"
        assert alist[1].name == "Test Bot"

    def test_webhook_list_len(self):
        wlist = WebhookList(
            items=[Webhook(**WEBHOOK_DATA)],
            total=1,
            limit=20,
            offset=0,
        )
        assert len(wlist) == 1
